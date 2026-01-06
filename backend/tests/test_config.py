"""
Tests for configuration validation.
"""
import pytest
from pydantic import ValidationError
from app.core.config import Settings


def test_jwt_secret_validation_weak():
    """Test that weak JWT secrets are rejected"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(JWT_SECRET_KEY="secret")

    errors = exc_info.value.errors()
    assert any("32 characters" in str(err["msg"]) for err in errors)


def test_jwt_secret_validation_default():
    """Test that default JWT secrets are rejected"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production")

    errors = exc_info.value.errors()
    assert any("default" in str(err["msg"]).lower() for err in errors)


def test_jwt_secret_validation_valid():
    """Test that valid JWT secrets are accepted"""
    # Should not raise
    settings = Settings(
        JWT_SECRET_KEY="this-is-a-very-secure-random-secret-key-with-at-least-32-chars"
    )
    assert len(settings.JWT_SECRET_KEY) >= 32
