from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.research_task import ResearchTask, TaskType, TaskStatus
from app.api.deps import get_current_user

router = APIRouter()


class DiscoveryTaskCreate(BaseModel):
    title: str
    theme: str
    market_cap_min: Optional[int] = None
    market_cap_max: Optional[int] = None
    sectors: Optional[List[str]] = None
    additional_criteria: Optional[str] = None


class DeepDiveTaskCreate(BaseModel):
    title: str
    ticker: str
    focus_areas: Optional[List[str]] = None


from datetime import datetime as dt

class ResearchTaskResponse(BaseModel):
    id: UUID
    task_type: TaskType
    title: str
    description: Optional[str] = None
    parameters: dict
    status: TaskStatus
    progress: int
    error_message: Optional[str] = None
    results: dict
    created_at: dt
    started_at: Optional[dt] = None
    completed_at: Optional[dt] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[ResearchTaskResponse])
async def list_research_tasks(
    status_filter: Optional[TaskStatus] = None,
    task_type: Optional[TaskType] = None,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(ResearchTask).where(ResearchTask.user_id == current_user.id)

    if status_filter:
        query = query.where(ResearchTask.status == status_filter)
    if task_type:
        query = query.where(ResearchTask.task_type == task_type)

    query = query.order_by(desc(ResearchTask.created_at)).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks


@router.post("/discovery", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_discovery_task(
    task_in: DiscoveryTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parameters = {
        "theme": task_in.theme,
        "market_cap_min": task_in.market_cap_min,
        "market_cap_max": task_in.market_cap_max,
        "sectors": task_in.sectors,
        "additional_criteria": task_in.additional_criteria,
    }

    task = ResearchTask(
        user_id=current_user.id,
        task_type=TaskType.DISCOVERY,
        title=task_in.title,
        description=f"Discover stocks related to: {task_in.theme}",
        parameters=parameters,
        status=TaskStatus.QUEUED,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Trigger Celery task
    from app.tasks.research_tasks import run_discovery_task
    celery_task = run_discovery_task.delay(str(task.id))

    # Update with Celery task ID
    task.celery_task_id = celery_task.id
    await db.commit()

    return task


@router.post("/deep-dive", response_model=ResearchTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_deep_dive_task(
    task_in: DeepDiveTaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    parameters = {
        "ticker": task_in.ticker.upper(),
        "focus_areas": task_in.focus_areas or ["financials", "competition", "growth"],
    }

    task = ResearchTask(
        user_id=current_user.id,
        task_type=TaskType.DEEP_DIVE,
        title=task_in.title,
        description=f"Deep dive research on {task_in.ticker.upper()}",
        parameters=parameters,
        status=TaskStatus.QUEUED,
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Trigger Celery task
    from app.tasks.research_tasks import run_deep_dive_task
    celery_task = run_deep_dive_task.delay(str(task.id))

    task.celery_task_id = celery_task.id
    await db.commit()

    return task


@router.get("/{task_id}", response_model=ResearchTaskResponse)
async def get_research_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchTask).where(
            ResearchTask.id == task_id,
            ResearchTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found",
        )

    return task


@router.post("/{task_id}/cancel", response_model=ResearchTaskResponse)
async def cancel_research_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ResearchTask).where(
            ResearchTask.id == task_id,
            ResearchTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research task not found",
        )

    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task already finished",
        )

    # Cancel Celery task if running
    if task.celery_task_id:
        from app.core.celery_app import celery_app
        celery_app.control.revoke(task.celery_task_id, terminate=True)

    task.status = TaskStatus.CANCELLED
    await db.commit()
    await db.refresh(task)

    return task
