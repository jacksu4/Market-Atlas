from datetime import datetime
from typing import Optional
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Enforce strong password requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    is_active: bool
    settings: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None


class TelegramConnect(BaseModel):
    chat_id: str


class NotificationPreferences(BaseModel):
    news_alerts: Optional[bool] = None
    filing_alerts: Optional[bool] = None
    research_complete: Optional[bool] = None


class SettingsUpdate(BaseModel):
    notification_preferences: Optional[NotificationPreferences] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str
