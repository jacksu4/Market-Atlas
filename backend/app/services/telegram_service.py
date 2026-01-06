from typing import Optional
import httpx

from app.core.config import settings


class TelegramService:
    BASE_URL = "https://api.telegram.org"

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN

    @property
    def api_url(self) -> str:
        return f"{self.BASE_URL}/bot{self.bot_token}"

    # ==================== SYNC METHODS (for Celery) ====================

    def send_message_sync(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """Synchronous version for Celery tasks"""
        if not self.bot_token:
            print("Telegram bot token not configured")
            return False

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_web_page_preview,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return True
                else:
                    print(f"Telegram API error: {response.text}")
                    return False
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_research_complete_notification_sync(
        self,
        chat_id: str,
        task_title: str,
        task_type: str,
        summary: str,
    ) -> bool:
        """Synchronous version for Celery tasks"""
        message = f"""<b>Research Complete</b>

<b>Task:</b> {task_title}
<b>Type:</b> {task_type}

<b>Summary:</b>
{summary[:500]}{'...' if len(summary) > 500 else ''}

View full results in Market Atlas."""

        return self.send_message_sync(chat_id, message)

    def send_discovery_notification_sync(
        self,
        chat_id: str,
        theme: str,
        candidates: list[dict],
    ) -> bool:
        """Synchronous version for Celery tasks"""
        candidates_text = ""
        for i, c in enumerate(candidates[:5], 1):
            candidates_text += f"\n{i}. <b>{c.get('ticker')}</b> - {c.get('company_name')}"
            candidates_text += f"\n   Score: {c.get('confidence_score', 'N/A')}/100"

        message = f"""<b>Discovery Complete</b>

<b>Theme:</b> {theme}

<b>Top Candidates:</b>
{candidates_text}

View full research in Market Atlas."""

        return self.send_message_sync(chat_id, message)

    # ==================== ASYNC METHODS (for FastAPI) ====================

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """
        Send a message to a Telegram chat.
        """
        if not self.bot_token:
            print("Telegram bot token not configured")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "disable_web_page_preview": disable_web_page_preview,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return True
                else:
                    print(f"Telegram API error: {response.text}")
                    return False
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    async def send_research_complete_notification(
        self,
        chat_id: str,
        task_title: str,
        task_type: str,
        summary: str,
    ) -> bool:
        """
        Send notification when a research task is complete.
        """
        message = f"""<b>Research Complete</b>

<b>Task:</b> {task_title}
<b>Type:</b> {task_type}

<b>Summary:</b>
{summary[:500]}{'...' if len(summary) > 500 else ''}

View full results in Market Atlas."""

        return await self.send_message(chat_id, message)

    async def send_important_news_notification(
        self,
        chat_id: str,
        ticker: str,
        headline: str,
        sentiment: str,
        summary: Optional[str] = None,
    ) -> bool:
        """
        Send notification for important news.
        """
        emoji = ""
        if sentiment == "bullish":
            emoji = ""
        elif sentiment == "bearish":
            emoji = ""

        message = f"""<b>{emoji} Important News: {ticker}</b>

{headline}
"""
        if summary:
            message += f"\n{summary[:300]}{'...' if len(summary) > 300 else ''}"

        return await self.send_message(chat_id, message)

    async def send_sec_filing_notification(
        self,
        chat_id: str,
        ticker: str,
        filing_type: str,
        summary: str,
    ) -> bool:
        """
        Send notification for new SEC filing.
        """
        message = f"""<b>New SEC Filing: {ticker}</b>

<b>Form:</b> {filing_type}

<b>Summary:</b>
{summary[:500]}{'...' if len(summary) > 500 else ''}

View full analysis in Market Atlas."""

        return await self.send_message(chat_id, message)

    async def send_discovery_notification(
        self,
        chat_id: str,
        theme: str,
        candidates: list[dict],
    ) -> bool:
        """
        Send notification with discovery results.
        """
        candidates_text = ""
        for i, c in enumerate(candidates[:5], 1):
            candidates_text += f"\n{i}. <b>{c.get('ticker')}</b> - {c.get('company_name')}"
            candidates_text += f"\n   Score: {c.get('confidence_score', 'N/A')}/100"

        message = f"""<b>Discovery Complete</b>

<b>Theme:</b> {theme}

<b>Top Candidates:</b>
{candidates_text}

View full research in Market Atlas."""

        return await self.send_message(chat_id, message)


telegram_service = TelegramService()
