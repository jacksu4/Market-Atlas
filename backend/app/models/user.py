import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # OAuth fields
    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # User settings stored as JSON
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    # settings structure:
    # {
    #   "telegram_chat_id": "123456789",
    #   "notification_preferences": {
    #     "news_alerts": true,
    #     "filing_alerts": true,
    #     "research_complete": true
    #   }
    # }

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    watchlists = relationship("Watchlist", back_populates="user", lazy="selectin")
    research_tasks = relationship("ResearchTask", back_populates="user", lazy="selectin")
