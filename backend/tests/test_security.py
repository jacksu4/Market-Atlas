"""
Tests for security functions.
"""
import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing():
    """Test password hashing and verification"""
    password = "SecurePassword123"
    hashed = get_password_hash(password)

    # Hash should be different from original
    assert hashed != password

    # Should verify correctly
    assert verify_password(password, hashed)

    # Wrong password should not verify
    assert not verify_password("WrongPassword", hashed)


def test_access_token_creation():
    """Test access token creation and decoding"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_access_token(data={"sub": user_id})

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_refresh_token_creation():
    """Test refresh token creation and decoding"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    token = create_refresh_token(data={"sub": user_id})

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_invalid_token_decode():
    """Test that invalid tokens return None"""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)
    assert payload is None
