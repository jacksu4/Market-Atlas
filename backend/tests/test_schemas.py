"""
Tests for Pydantic schemas validation.
"""
import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate
from app.schemas.watchlist import WatchlistItemCreate, StockCreate


class TestUserSchema:
    """Tests for user schemas"""

    def test_password_too_short(self):
        """Test that short passwords are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                email="test@example.com",
                password="Short1",
                name="Test User",
            )
        errors = exc_info.value.errors()
        assert any("8 characters" in str(err["msg"]) for err in errors)

    def test_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="lowercase123",
                name="Test User",
            )

    def test_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="UPPERCASE123",
                name="Test User",
            )

    def test_password_no_digit(self):
        """Test that passwords without digits are rejected"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="NoDigitsHere",
                name="Test User",
            )

    def test_valid_user_create(self):
        """Test valid user creation"""
        user = UserCreate(
            email="test@example.com",
            password="SecurePass123",
            name="Test User",
        )
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123"


class TestWatchlistSchema:
    """Tests for watchlist schemas"""

    def test_ticker_validation_empty(self):
        """Test that empty tickers are rejected"""
        with pytest.raises(ValidationError):
            WatchlistItemCreate(ticker="")

    def test_ticker_validation_too_long(self):
        """Test that very long tickers are rejected"""
        with pytest.raises(ValidationError):
            WatchlistItemCreate(ticker="VERYLONGTICKER123")

    def test_ticker_validation_invalid_chars(self):
        """Test that invalid characters are rejected"""
        with pytest.raises(ValidationError):
            WatchlistItemCreate(ticker="INVALID@TICKER")

    def test_ticker_validation_valid(self):
        """Test valid ticker formats"""
        # Regular ticker
        item1 = WatchlistItemCreate(ticker="AAPL")
        assert item1.ticker == "AAPL"

        # Ticker with hyphen
        item2 = WatchlistItemCreate(ticker="BRK-A")
        assert item2.ticker == "BRK-A"

        # Lowercase gets converted to uppercase
        item3 = WatchlistItemCreate(ticker="msft")
        assert item3.ticker == "MSFT"

    def test_stock_create_ticker_validation(self):
        """Test ticker validation in StockCreate schema"""
        stock = StockCreate(
            ticker="aapl",
            company_name="Apple Inc.",
        )
        assert stock.ticker == "AAPL"
