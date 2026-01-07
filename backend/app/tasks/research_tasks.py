from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.database import SyncSessionLocal
from app.models.research_task import ResearchTask, TaskStatus
from app.models.stock import Stock
from app.models.filing import Filing, FilingType, FilingStatus
from app.models.watchlist import WatchlistItem
from app.models.user import User
from app.services.ai_service import ai_service
from app.services.sec_service import sec_service
from app.services.fmp_service import fmp_service
from app.services.telegram_service import telegram_service


def _send_task_notification_sync(db, task: ResearchTask):
    """Send Telegram notification for completed task (sync version)"""
    if task.notification_sent:
        return

    # Get user
    result = db.execute(
        select(User).where(User.id == task.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return

    chat_id = user.settings.get("telegram_chat_id") if user.settings else None
    if not chat_id:
        return

    # Check notification preferences
    prefs = user.settings.get("notification_preferences", {}) if user.settings else {}
    if not prefs.get("research_complete", True):
        return

    # Send notification based on task type
    if task.task_type.value == "discovery":
        candidates = task.results.get("candidates", []) if task.results else []
        telegram_service.send_discovery_notification_sync(
            chat_id,
            task.parameters.get("theme", "Unknown") if task.parameters else "Unknown",
            candidates,
        )
    else:
        summary = task.results.get("summary", str(task.results)[:500]) if task.results else ""
        telegram_service.send_research_complete_notification_sync(
            chat_id,
            task.title,
            task.task_type.value,
            summary,
        )

    task.notification_sent = True
    db.commit()


@celery_app.task(name="app.tasks.research_tasks.run_discovery_task")
def run_discovery_task(task_id: str):
    """Run AI discovery task (sync version for Celery)"""
    db = SyncSessionLocal()
    try:
        # Get task
        result = db.execute(
            select(ResearchTask).where(ResearchTask.id == UUID(task_id))
        )
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        # Update status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        task.progress = 10
        db.commit()

        try:
            # Extract parameters
            params = task.parameters or {}
            theme = params.get("theme", "")
            criteria = params.get("additional_criteria")

            # Run AI discovery
            task.progress = 30
            db.commit()

            discovery_results = ai_service.run_discovery_sync(theme, criteria)

            task.progress = 80
            db.commit()

            # Store results
            task.results = discovery_results
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            db.commit()

            # Send notification
            _send_task_notification_sync(db, task)

            return {"success": True, "results": discovery_results}

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
            return {"error": str(e)}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.research_tasks.run_deep_dive_task")
def run_deep_dive_task(task_id: str):
    """Run deep dive research task (sync version for Celery)"""
    db = SyncSessionLocal()
    try:
        result = db.execute(
            select(ResearchTask).where(ResearchTask.id == UUID(task_id))
        )
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        task.progress = 10
        db.commit()

        try:
            params = task.parameters or {}
            ticker = params.get("ticker", "")

            # Gather data
            task.progress = 20
            db.commit()

            # Get company profile
            profile = fmp_service.get_company_profile_sync(ticker)

            # Get recent earnings transcript
            task.progress = 40
            db.commit()
            transcript = fmp_service.get_earnings_transcript_sync(ticker)

            # Get income statements
            task.progress = 60
            db.commit()
            financials = fmp_service.get_income_statement_sync(ticker, period="annual", limit=3)

            # Build research report
            results = {
                "ticker": ticker,
                "profile": profile or {},
                "recent_financials": financials,
                "earnings_transcript_available": transcript is not None,
            }

            # Analyze earnings call if available
            if transcript:
                transcript_text = transcript.get("content", "")
                if transcript_text:
                    task.progress = 80
                    db.commit()
                    earnings_analysis = ai_service.analyze_earnings_call_sync(
                        transcript_text,
                        ticker,
                        transcript.get("quarter", "Recent"),
                    )
                    results["earnings_analysis"] = earnings_analysis

            task.results = results
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now(timezone.utc)
            db.commit()

            _send_task_notification_sync(db, task)

            return {"success": True}

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
            return {"error": str(e)}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.research_tasks.check_sec_filings")
def check_sec_filings():
    """Check for new SEC filings for watchlist stocks (sync version for Celery)"""
    db = SyncSessionLocal()
    try:
        # Get all stocks with CIK from watchlists
        result = db.execute(
            select(Stock)
            .join(WatchlistItem, WatchlistItem.ticker == Stock.ticker)
            .where(Stock.cik.isnot(None))
            .distinct()
        )
        stocks = result.scalars().all()

        new_filings = 0

        for stock in stocks:
            # Get recent filings
            filings = sec_service.get_recent_filings_sync(
                stock.cik,
                filing_types=["10-K", "10-Q", "8-K"],
            )

            for filing_data in filings[:5]:  # Check last 5
                # Check if already processed
                existing = db.execute(
                    select(Filing).where(
                        Filing.accession_number == filing_data["accession_number"]
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                # Determine filing type
                form = filing_data["form"]
                try:
                    filing_type = FilingType(form)
                except ValueError:
                    filing_type = FilingType.OTHER

                # Create filing record
                filing = Filing(
                    ticker=stock.ticker,
                    filing_type=filing_type,
                    accession_number=filing_data["accession_number"],
                    filed_at=datetime.fromisoformat(filing_data["filing_date"]),
                    filing_url=filing_data["filing_url"],
                    status=FilingStatus.PENDING,
                )

                db.add(filing)
                db.flush()  # Get the filing ID
                new_filings += 1

                # Queue for analysis
                analyze_sec_filing.delay(str(filing.id))

        db.commit()

        return {"message": f"Found {new_filings} new filings"}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.research_tasks.analyze_sec_filing")
def analyze_sec_filing(filing_id: str):
    """Analyze a specific SEC filing (sync version for Celery)"""
    db = SyncSessionLocal()
    try:
        result = db.execute(
            select(Filing).where(Filing.id == UUID(filing_id))
        )
        filing = result.scalar_one_or_none()

        if not filing:
            return {"error": "Filing not found"}

        filing.status = FilingStatus.PROCESSING
        db.commit()

        try:
            # Download filing text
            text = sec_service.get_filing_text_sync(filing.filing_url)

            if not text:
                filing.status = FilingStatus.FAILED
                filing.ai_analysis = {"error": "Could not download filing"}
                db.commit()
                return {"error": "Could not download filing"}

            filing.raw_text = text[:100000]  # Store first 100k chars

            # Analyze with AI
            analysis = ai_service.analyze_sec_filing_sync(
                filing.filing_type.value,
                text,
                filing.ticker,
            )

            filing.ai_summary = analysis.get("summary", "")
            filing.ai_analysis = analysis
            filing.status = FilingStatus.ANALYZED
            filing.analyzed_at = datetime.now(timezone.utc)
            db.commit()

            # Send notification to users watching this ticker
            from app.models.watchlist import Watchlist, WatchlistItem
            from app.core.logging_config import app_logger

            users_result = db.execute(
                select(User)
                .join(Watchlist, Watchlist.user_id == User.id)
                .join(WatchlistItem, WatchlistItem.watchlist_id == Watchlist.id)
                .where(WatchlistItem.ticker == filing.ticker)
                .distinct()
            )
            users = users_result.scalars().all()

            for user in users:
                chat_id = user.settings.get("telegram_chat_id") if user.settings else None
                prefs = user.settings.get("notification_preferences", {}) if user.settings else {}

                if chat_id and prefs.get("filing_alerts", True):
                    try:
                        telegram_service.send_sec_filing_notification_sync(
                            chat_id,
                            filing.ticker,
                            filing.filing_type.value,
                            filing.ai_summary or "Analysis completed. Please check details."
                        )
                        app_logger.info(
                            "Filing notification sent",
                            extra={
                                "user_id": str(user.id),
                                "ticker": filing.ticker,
                                "filing_type": filing.filing_type.value
                            }
                        )
                    except Exception as e:
                        app_logger.error(f"Failed to send filing notification: {e}")

            return {"success": True}

        except Exception as e:
            filing.status = FilingStatus.FAILED
            filing.ai_analysis = {"error": str(e)}
            db.commit()
            return {"error": str(e)}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.research_tasks.check_earnings_transcripts")
def check_earnings_transcripts():
    """Check for new earnings transcripts (sync version for Celery)"""
    db = SyncSessionLocal()
    try:
        # Get all unique tickers from watchlists
        result = db.execute(
            select(WatchlistItem.ticker).distinct()
        )
        tickers = [row[0] for row in result.fetchall()]

        checked = 0
        for ticker in tickers:
            # Check for new transcripts
            transcripts = fmp_service.get_all_transcripts_sync(ticker, limit=1)

            if transcripts:
                # Could trigger analysis task here
                checked += 1

        return {"message": f"Checked {checked} tickers for new transcripts"}

    except Exception as e:
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
