from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.core.security import decode_token
from app.core.config import settings
from app.models.user import User
from app.services.telegram_service import telegram_service
from app.core.logging_config import app_logger

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Telegram bot updates.
    Supports: /start <token> - Connect account via deep link
    """
    # Verify webhook signature
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_header != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()

    # Extract message
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = str(message.get("from", {}).get("id", ""))

    if not text.startswith("/start "):
        # Send usage instructions
        await telegram_service.send_message(
            chat_id,
            "Welcome to Market Atlas Bot!\n\nPlease click the 'Connect Telegram' button in Settings to generate a connection link."
        )
        return {"status": "ok"}

    # Extract token
    token = text.split(" ", 1)[1] if " " in text else ""

    try:
        # Verify token
        payload = decode_token(token)

        if not payload or payload.get("type") != "telegram_link":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user_id = payload.get("sub")

        # Find user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Save chat_id
        current_settings = user.settings or {}
        current_settings["telegram_chat_id"] = chat_id
        user.settings = current_settings
        flag_modified(user, "settings")

        await db.commit()

        # Send confirmation message
        await telegram_service.send_message(
            chat_id,
            "✅ Account connected successfully!\n\nYou will now receive Market Atlas notifications."
        )

        app_logger.info(
            "Telegram account connected",
            extra={"user_id": user_id, "chat_id": chat_id}
        )

    except Exception as e:
        app_logger.error(f"Webhook error: {e}")
        await telegram_service.send_message(
            chat_id,
            "❌ Connection failed. The link may have expired, please generate a new one."
        )

    return {"status": "ok"}
