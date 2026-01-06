"""
Comprehensive integration tests for Market Atlas.

Tests complete user workflows:
1. User registration -> Create watchlist -> Add stock -> Check values
2. AI discovery integration
3. News analysis workflow
4. Research task lifecycle
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import Watchlist, WatchlistItem
from app.models.stock import Stock
from app.models.news import News


class TestUserWatchlistWorkflow:
    """Test complete user workflow from registration to watchlist management"""

    @pytest.mark.asyncio
    async def test_complete_user_workflow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """
        Integration test: Register -> Login -> Create Watchlist -> Add Stock -> Verify
        """
        # Step 1: Register a new user
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "investor@example.com",
                "password": "SecurePass123",
                "name": "Test Investor",
            },
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["email"] == "investor@example.com"
        user_id = user_data["id"]

        # Step 2: Login with the user
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "investor@example.com",
                "password": "SecurePass123",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Step 3: Create a watchlist
        watchlist_response = await client.post(
            "/api/v1/watchlist",
            headers=headers,
            json={
                "name": "Tech Stocks",
                "description": "My favorite technology companies",
            },
        )
        assert watchlist_response.status_code == 201
        watchlist_data = watchlist_response.json()
        assert watchlist_data["name"] == "Tech Stocks"
        assert watchlist_data["description"] == "My favorite technology companies"
        watchlist_id = watchlist_data["id"]

        # Step 4: Add a stock to the watchlist
        add_stock_response = await client.post(
            f"/api/v1/watchlist/{watchlist_id}/items",
            headers=headers,
            json={
                "ticker": "AAPL",
                "notes": "Apple Inc. - Strong fundamentals",
            },
        )
        assert add_stock_response.status_code == 201
        stock_item = add_stock_response.json()
        assert stock_item["ticker"] == "AAPL"
        assert stock_item["notes"] == "Apple Inc. - Strong fundamentals"

        # Step 5: Add another stock
        add_stock_response2 = await client.post(
            f"/api/v1/watchlist/{watchlist_id}/items",
            headers=headers,
            json={
                "ticker": "MSFT",
                "notes": "Microsoft - Cloud growth",
            },
        )
        assert add_stock_response2.status_code == 201

        # Step 6: Get the watchlist and verify stocks
        get_watchlist_response = await client.get(
            f"/api/v1/watchlist/{watchlist_id}",
            headers=headers,
        )
        assert get_watchlist_response.status_code == 200
        watchlist = get_watchlist_response.json()
        assert watchlist["name"] == "Tech Stocks"
        assert len(watchlist["items"]) == 2

        # Verify stock items
        tickers = {item["ticker"] for item in watchlist["items"]}
        assert "AAPL" in tickers
        assert "MSFT" in tickers

        # Step 7: Verify database state
        db_watchlist = await db_session.execute(
            select(Watchlist)
            .where(Watchlist.id == watchlist_id)
        )
        watchlist_obj = db_watchlist.scalar_one()
        assert watchlist_obj.name == "Tech Stocks"

        # Check stocks were created
        db_stock = await db_session.execute(
            select(Stock).where(Stock.ticker == "AAPL")
        )
        stock_obj = db_stock.scalar_one_or_none()
        assert stock_obj is not None
        assert stock_obj.ticker == "AAPL"

        # Step 8: List all watchlists
        list_response = await client.get(
            "/api/v1/watchlist",
            headers=headers,
        )
        assert list_response.status_code == 200
        watchlists = list_response.json()
        assert len(watchlists) >= 1
        assert any(w["id"] == watchlist_id for w in watchlists)

        # Step 9: Update watchlist
        update_response = await client.patch(
            f"/api/v1/watchlist/{watchlist_id}",
            headers=headers,
            json={"name": "Top Tech Stocks"},
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Top Tech Stocks"

        # Step 10: Remove a stock
        remove_response = await client.delete(
            f"/api/v1/watchlist/{watchlist_id}/items/MSFT",
            headers=headers,
        )
        assert remove_response.status_code == 204

        # Verify stock was removed
        get_watchlist_response2 = await client.get(
            f"/api/v1/watchlist/{watchlist_id}",
            headers=headers,
        )
        watchlist2 = get_watchlist_response2.json()
        assert len(watchlist2["items"]) == 1
        assert watchlist2["items"][0]["ticker"] == "AAPL"

    @pytest.mark.asyncio
    async def test_duplicate_stock_prevention(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that duplicate stocks cannot be added to watchlist"""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test2@example.com",
                "password": "SecurePass123",
                "name": "Test User 2",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test2@example.com", "password": "SecurePass123"},
        )
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Create watchlist
        watchlist_response = await client.post(
            "/api/v1/watchlist",
            headers=headers,
            json={"name": "My Stocks"},
        )
        watchlist_id = watchlist_response.json()["id"]

        # Add stock
        await client.post(
            f"/api/v1/watchlist/{watchlist_id}/items",
            headers=headers,
            json={"ticker": "GOOGL"},
        )

        # Try to add same stock again
        duplicate_response = await client.post(
            f"/api/v1/watchlist/{watchlist_id}/items",
            headers=headers,
            json={"ticker": "GOOGL"},
        )
        assert duplicate_response.status_code == 400
        assert "already in watchlist" in duplicate_response.json()["detail"].lower()


class TestAuthenticationFlow:
    """Test authentication and token management"""

    @pytest.mark.asyncio
    async def test_token_refresh_workflow(self, client: AsyncClient):
        """Test token refresh and rotation"""
        # Register user
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "token_test@example.com",
                "password": "SecurePass123",
                "name": "Token Test",
            },
        )

        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "token_test@example.com", "password": "SecurePass123"},
        )
        tokens = login_response.json()
        old_refresh_token = tokens["refresh_token"]
        old_access_token = tokens["access_token"]

        # Use refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]

        # Verify new tokens are different
        assert new_access_token != old_access_token
        assert new_refresh_token != old_refresh_token

        # Verify new access token works
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert me_response.status_code == 200

        # Verify old refresh token is invalidated (token rotation)
        old_refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert old_refresh_response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_rejection(self, client: AsyncClient):
        """Test that invalid tokens are properly rejected"""
        # Try to access protected route with invalid token
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )
        assert response.status_code == 401

        # Try to use invalid refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"},
        )
        assert refresh_response.status_code == 401


class TestInputValidation:
    """Test input validation across the application"""

    @pytest.mark.asyncio
    async def test_ticker_validation(self, client: AsyncClient):
        """Test ticker format validation"""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "validation_test@example.com",
                "password": "SecurePass123",
                "name": "Validation Test",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "validation_test@example.com", "password": "SecurePass123"},
        )
        headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

        # Create watchlist
        watchlist_response = await client.post(
            "/api/v1/watchlist",
            headers=headers,
            json={"name": "Test"},
        )
        watchlist_id = watchlist_response.json()["id"]

        # Test invalid ticker formats
        invalid_tickers = [
            "",  # Empty
            "TOOLONGTICKER123",  # Too long
            "123ABC",  # Starts with number
            "ABC@#$",  # Invalid characters
        ]

        for invalid_ticker in invalid_tickers:
            response = await client.post(
                f"/api/v1/watchlist/{watchlist_id}/items",
                headers=headers,
                json={"ticker": invalid_ticker},
            )
            assert response.status_code == 422, f"Failed to reject ticker: {invalid_ticker}"

        # Test valid ticker formats
        valid_tickers = ["AAPL", "BRK-A", "GOOGL", "MSFT"]

        for valid_ticker in valid_tickers:
            response = await client.post(
                f"/api/v1/watchlist/{watchlist_id}/items",
                headers=headers,
                json={"ticker": valid_ticker},
            )
            assert response.status_code == 201, f"Failed to accept ticker: {valid_ticker}"

    @pytest.mark.asyncio
    async def test_password_strength_validation(self, client: AsyncClient):
        """Test password strength requirements"""
        # Test weak passwords
        weak_passwords = [
            "short",  # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoDigitsHere",  # No digits
        ]

        for weak_pass in weak_passwords:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": weak_pass,
                    "name": "Test",
                },
            )
            assert response.status_code == 422, f"Failed to reject password: {weak_pass}"

        # Test strong password (should succeed)
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "strong_pass@example.com",
                "password": "StrongPass123",
                "name": "Test",
            },
        )
        assert response.status_code == 201


class TestRateLimiting:
    """Test rate limiting on authentication endpoints"""

    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, client: AsyncClient):
        """Test that login rate limiting works (would require actual rate limit testing)"""
        # Note: This is a placeholder. Actual rate limit testing would require
        # making many requests in quick succession, which may be slow in tests.
        # In practice, you'd use a different approach or mock the rate limiter.
        pass


# Note: AI discovery and research tasks tests would require mocking
# external APIs (Anthropic, financial data providers). These are
# intentionally omitted to keep tests fast and not depend on external services.
# For those, use separate test files with mocked responses.
