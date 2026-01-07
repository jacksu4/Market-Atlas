import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.core.token_manager import token_manager
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, RefreshTokenRequest, TelegramConnect, SettingsUpdate
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging_config import app_logger

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")  # Limit registration to 5 per hour per IP
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=get_password_hash(user_in.password),
        settings={
            "notification_preferences": {
                "news_alerts": True,
                "filing_alerts": True,
                "research_complete": True,
            }
        },
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")  # Limit login attempts to 10 per minute per IP
async def login(request: Request, credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Store refresh token in Redis for rotation tracking
    await token_manager.store_refresh_token(
        str(user.id),
        refresh_token,
        settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
@limiter.limit("20/minute")  # Limit token refresh to 20 per minute per IP
async def refresh_token(request: Request, token_request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(token_request.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    # Verify token is in whitelist (not already used/revoked)
    is_valid = await token_manager.verify_refresh_token(user_id, token_request.refresh_token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or already used",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Implement token rotation: invalidate old token and store new one
    # This ensures each refresh token can only be used once
    await token_manager.store_refresh_token(
        str(user.id),
        new_refresh_token,
        settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/settings", response_model=UserResponse)
async def update_user_settings(
    settings_update: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user notification preferences (auto-save).
    Accepts partial updates: news_alerts, filing_alerts, research_complete
    """
    # Validate and update only notification_preferences
    if settings_update.notification_preferences:
        # Merge with existing settings
        current_settings = current_user.settings or {}
        current_prefs = current_settings.get("notification_preferences", {})

        # Update only the provided fields
        prefs_dict = settings_update.notification_preferences.model_dump(exclude_unset=True)
        current_prefs.update(prefs_dict)
        current_settings["notification_preferences"] = current_prefs

        current_user.settings = current_settings
        # Mark the settings field as modified for SQLAlchemy to detect the change
        flag_modified(current_user, "settings")
        await db.commit()
        await db.refresh(current_user)

    return current_user


@router.post("/telegram/connect", response_model=UserResponse)
@limiter.limit("5/minute")
async def connect_telegram(
    request: Request,
    telegram_data: TelegramConnect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Connect Telegram account and send test message.

    Steps:
    1. Validate chat_id format (numeric string)
    2. Send test message
    3. Save to settings if successful
    4. Return updated user object
    """
    # Validate chat_id format
    import re
    if not re.match(r'^-?\d+$', telegram_data.chat_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid chat_id format. Must be numeric string."
        )

    # Send test message
    from app.services.telegram_service import telegram_service
    test_message = """🎉 Successfully connected to Market Atlas!

You'll now receive notifications for:
• Important news alerts
• SEC filing updates
• Research task completions

Manage your preferences in Settings."""

    success = await telegram_service.send_message(
        telegram_data.chat_id,
        test_message
    )

    if not success:
        raise HTTPException(
            status_code=503,
            detail="Failed to send test message. Please verify your Chat ID."
        )

    # Save chat_id
    current_settings = current_user.settings or {}
    current_settings["telegram_chat_id"] = telegram_data.chat_id
    current_user.settings = current_settings
    flag_modified(current_user, "settings")

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.delete("/telegram/disconnect", response_model=UserResponse)
async def disconnect_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove telegram_chat_id from user settings"""
    current_settings = current_user.settings or {}
    current_settings.pop("telegram_chat_id", None)
    current_user.settings = current_settings
    flag_modified(current_user, "settings")

    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/telegram/link")
async def generate_telegram_link(
    current_user: User = Depends(get_current_user)
):
    """
    Generate Telegram bot deep link.
    Returns: {link, expires_in}
    """
    from app.core.security import create_telegram_link_token
    token = create_telegram_link_token(str(current_user.id))

    return {
        "link": f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={token}",
        "expires_in": 600
    }


# ============== Google OAuth ==============

# In-memory state storage (use Redis in production for multi-instance)
_oauth_states: dict[str, bool] = {}


@router.get("/google/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth flow.
    Redirects user to Google's authorization page.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = True

    # Build Google authorization URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Exchanges code for tokens, creates/logs in user, redirects to frontend.
    """
    # Handle errors from Google
    if error:
        app_logger.warning(f"Google OAuth error: {error}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        )

    # Validate state (CSRF protection)
    if not state or state not in _oauth_states:
        app_logger.warning("Invalid OAuth state")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=invalid_state"
        )

    # Remove used state
    _oauth_states.pop(state, None)

    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=no_code"
        )

    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                }
            )

            if token_response.status_code != 200:
                app_logger.error(f"Google token exchange failed: {token_response.text}")
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/login?error=token_exchange_failed"
                )

            token_data = token_response.json()
            google_access_token = token_data.get("access_token")

            # Get user info from Google
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {google_access_token}"}
            )

            if userinfo_response.status_code != 200:
                app_logger.error(f"Google userinfo failed: {userinfo_response.text}")
                return RedirectResponse(
                    url=f"{settings.FRONTEND_URL}/login?error=userinfo_failed"
                )

            google_user = userinfo_response.json()

        # Extract user info
        google_id = google_user.get("id")
        email = google_user.get("email")
        name = google_user.get("name", email.split("@")[0] if email else "User")

        if not email:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=no_email"
            )

        # Check if user exists by OAuth ID
        result = await db.execute(
            select(User).where(
                User.oauth_provider == "google",
                User.oauth_id == google_id
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            # Check if email already exists (password user)
            result = await db.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                # Email exists but not linked to Google
                if existing_user.oauth_provider:
                    # Already linked to different OAuth provider
                    return RedirectResponse(
                        url=f"{settings.FRONTEND_URL}/login?error=email_linked_other_provider"
                    )
                else:
                    # Password user - link Google account
                    existing_user.oauth_provider = "google"
                    existing_user.oauth_id = google_id
                    await db.commit()
                    user = existing_user
                    app_logger.info(f"Linked Google account to existing user: {email}")
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    oauth_provider="google",
                    oauth_id=google_id,
                    settings={
                        "notification_preferences": {
                            "news_alerts": True,
                            "filing_alerts": True,
                            "research_complete": True,
                        }
                    },
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                app_logger.info(f"Created new Google user: {email}")

        if not user.is_active:
            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?error=account_inactive"
            )

        # Generate JWT tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Store refresh token
        await token_manager.store_refresh_token(
            str(user.id),
            refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        # Redirect to frontend with tokens
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"?access_token={access_token}"
            f"&refresh_token={refresh_token}"
        )

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        app_logger.error(f"Google OAuth error: {str(e)}")
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=server_error"
        )
