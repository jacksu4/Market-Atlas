# Market Atlas - Coding Conventions & Architecture

This document outlines the coding conventions, architecture patterns, and best practices for Market Atlas development.

## Project Structure

```
Market-Atlas/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Core functionality (config, db, security)
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic layer
│   │   └── tasks/       # Celery background tasks
│   ├── alembic/         # Database migrations
│   └── tests/           # Test suite
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/         # Next.js App Router
│       ├── components/  # React components
│       ├── lib/         # Utilities
│       └── types/       # TypeScript types
└── docker/              # Docker configuration
```

## Backend Architecture

### Layered Architecture

1. **API Layer** (`app/api/`)
   - FastAPI route handlers
   - Request validation
   - Response serialization
   - Authentication/authorization

2. **Service Layer** (`app/services/`)
   - Business logic
   - External API integrations
   - Data transformations
   - Reusable functions

3. **Model Layer** (`app/models/`)
   - SQLAlchemy ORM models
   - Database schema definitions
   - Relationships

4. **Schema Layer** (`app/schemas/`)
   - Pydantic models for validation
   - Request/response schemas
   - Data transfer objects

### Coding Conventions

#### Python Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use f-strings for string formatting

```python
# Good
async def get_stock_price(ticker: str) -> Optional[float]:
    """Get current stock price."""
    return await service.fetch_price(ticker)

# Bad
def get_stock_price(ticker):
    return service.fetch_price(ticker)
```

#### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case()`
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`

```python
# Good
class StockService:
    DEFAULT_TIMEOUT = 30

    async def get_company_news(self, ticker: str) -> List[News]:
        pass

# Bad
class stockService:
    default_timeout = 30

    async def GetCompanyNews(self, Ticker: str):
        pass
```

#### Import Organization

```python
# Standard library imports
import json
from datetime import datetime
from typing import List, Optional

# Third-party imports
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select

# Local imports
from app.core.config import settings
from app.models.stock import Stock
from app.schemas.stock import StockResponse
```

### Database Patterns

#### Using Async Sessions

```python
from app.core.database import get_db

@router.get("/stocks/{ticker}")
async def get_stock(
    ticker: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Stock).where(Stock.ticker == ticker)
    )
    stock = result.scalar_one_or_none()
    return stock
```

#### Avoiding N+1 Queries

Use `selectinload` or `joinedload` for relationships:

```python
from sqlalchemy.orm import selectinload

# Good - Single query with eager loading
result = await db.execute(
    select(Watchlist)
    .options(selectinload(Watchlist.items).selectinload(WatchlistItem.stock))
    .where(Watchlist.id == watchlist_id)
)

# Bad - N+1 queries
watchlist = await db.get(Watchlist, watchlist_id)
# Each item access triggers a separate query
for item in watchlist.items:
    print(item.stock.company_name)
```

### Error Handling

```python
from fastapi import HTTPException, status

# Use appropriate HTTP status codes
@router.get("/stocks/{ticker}")
async def get_stock(ticker: str):
    stock = await service.get_stock(ticker)

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {ticker} not found"
        )

    return stock
```

### Logging

Use structured logging:

```python
from app.core.logging_config import app_logger, log_external_api_call

# Log with context
app_logger.info(
    "Processing watchlist",
    extra={"watchlist_id": str(watchlist_id), "user_id": str(user.id)}
)

# Log external API calls
log_external_api_call(
    service="finnhub",
    endpoint="/company-news",
    status_code=200
)
```

### Caching

Use Redis caching for expensive operations:

```python
from app.core.cache import cached

@cached("stock_price", ttl=300)  # Cache for 5 minutes
async def get_stock_price(ticker: str) -> Optional[float]:
    # Expensive API call
    return await external_api.get_price(ticker)
```

### Background Tasks

Use Celery for long-running tasks:

```python
from app.core.celery_app import celery_app
from app.core.metrics import track_celery_task

@celery_app.task
@track_celery_task("fetch_news")
def fetch_news_for_ticker(ticker: str):
    """Background task to fetch news."""
    # Task implementation
    pass

# Trigger from API
fetch_news_for_ticker.delay(ticker)
```

### Testing

#### Test Structure

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_watchlist(client: AsyncClient):
    """Test watchlist creation with authentication."""
    # Arrange
    access_token = await get_test_token(client)

    # Act
    response = await client.post(
        "/api/v1/watchlist",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"name": "My Watchlist"}
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == "My Watchlist"
```

#### Test Coverage Goals

- **Critical paths**: 100% coverage
- **Authentication**: 100% coverage
- **Business logic**: 90%+ coverage
- **Overall**: 70%+ coverage

### Integration Testing

Integration tests verify complete user workflows and system interactions.

#### Test Complete User Workflows

```python
@pytest.mark.asyncio
async def test_complete_user_workflow(client: AsyncClient):
    """
    Test: Register -> Login -> Create Watchlist -> Add Stock -> Verify
    """
    # 1. Register user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "name": "Test User"
        }
    )
    assert register_response.status_code == 201

    # 2. Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "SecurePass123"}
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 3. Create watchlist
    watchlist_response = await client.post(
        "/api/v1/watchlist",
        headers=headers,
        json={"name": "Tech Stocks"}
    )
    watchlist_id = watchlist_response.json()["id"]

    # 4. Add stock to watchlist
    stock_response = await client.post(
        f"/api/v1/watchlist/{watchlist_id}/items",
        headers=headers,
        json={"ticker": "AAPL", "notes": "Apple Inc."}
    )
    assert stock_response.status_code == 201

    # 5. Verify watchlist contains stock
    get_response = await client.get(
        f"/api/v1/watchlist/{watchlist_id}",
        headers=headers
    )
    watchlist = get_response.json()
    assert len(watchlist["items"]) == 1
    assert watchlist["items"][0]["ticker"] == "AAPL"
```

#### Test AI Discovery Workflow

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_ai_discovery_integration(client: AsyncClient):
    """
    Test: Login -> Run AI Discovery -> Verify Results
    """
    # Login as user
    headers = await get_auth_headers(client)

    # Mock Anthropic API
    with patch('app.services.ai_service.anthropic.AsyncAnthropic') as mock_client:
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.content = [
            AsyncMock(text='{"stocks": [{"ticker": "NVDA", "rationale": "AI leader"}]}')
        ]
        mock_client.return_value.messages.create = AsyncMock(
            return_value=mock_response
        )

        # Run discovery
        discovery_response = await client.post(
            "/api/v1/research/discover",
            headers=headers,
            json={"themes": ["artificial intelligence", "semiconductors"]}
        )

        assert discovery_response.status_code == 200
        results = discovery_response.json()
        assert "stocks" in results
        assert any(s["ticker"] == "NVDA" for s in results["stocks"])
```

#### Test Database State Verification

```python
@pytest.mark.asyncio
async def test_verify_database_state(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Verify database state after operations"""
    headers = await get_auth_headers(client)

    # Create watchlist
    watchlist_response = await client.post(
        "/api/v1/watchlist",
        headers=headers,
        json={"name": "Growth Stocks"}
    )
    watchlist_id = watchlist_response.json()["id"]

    # Verify in database
    from app.models.watchlist import Watchlist
    result = await db_session.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id)
    )
    db_watchlist = result.scalar_one()
    assert db_watchlist.name == "Growth Stocks"
```

#### Integration Test Checklist

Run these integration tests before each PR:

- [ ] User registration and authentication flow
- [ ] Watchlist creation and management
- [ ] Stock addition and removal
- [ ] Token refresh and rotation
- [ ] Input validation (tickers, passwords)
- [ ] Error handling and edge cases
- [ ] Database state consistency
- [ ] Rate limiting enforcement
- [ ] AI discovery workflow (with mocks)
- [ ] News analysis pipeline (with mocks)
- [ ] Research task lifecycle

#### Running Integration Tests

```bash
# Run all integration tests
pytest backend/tests/test_integration.py -v

# Run specific workflow test
pytest backend/tests/test_integration.py::TestUserWatchlistWorkflow -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html

# Run integration tests in parallel (faster)
pytest backend/tests/test_integration.py -n auto
```

## Frontend Architecture

### TypeScript Conventions

```typescript
// Use interfaces for object shapes
interface Stock {
  ticker: string;
  companyName: string;
  sector?: string;
}

// Use type for unions and primitives
type Status = "active" | "inactive" | "pending";

// Prefer async/await over promises
async function fetchStock(ticker: string): Promise<Stock> {
  const response = await fetch(`/api/stocks/${ticker}`);
  return response.json();
}
```

### Component Structure

```typescript
// Use functional components with hooks
import { useState, useEffect } from "react";

interface StockCardProps {
  ticker: string;
  onSelect?: (ticker: string) => void;
}

export function StockCard({ ticker, onSelect }: StockCardProps) {
  const [data, setData] = useState<Stock | null>(null);

  useEffect(() => {
    // Load data
  }, [ticker]);

  return <div>{/* Component JSX */}</div>;
}
```

### API Client

```typescript
// Use the centralized API client
import { api } from "@/lib/api";

// In component
const stocks = await api.getStocks();
const watchlist = await api.createWatchlist({ name: "Tech Stocks" });
```

## Performance Best Practices

### Database

1. **Use indexes** on frequently queried columns
2. **Eager load** relationships to avoid N+1 queries
3. **Batch operations** when possible
4. **Use database-level filtering** instead of application-level

### Caching

1. **Cache expensive computations** (stock data, API responses)
2. **Set appropriate TTLs** (5 min for prices, 1 hour for company info)
3. **Invalidate cache** when data changes
4. **Use cache prefixes** for organization

### API Design

1. **Pagination** for list endpoints
2. **Field selection** for large objects
3. **Compression** for responses
4. **Rate limiting** to prevent abuse

## Security Guidelines

1. **Never log sensitive data** (passwords, tokens, API keys)
2. **Validate all inputs** using Pydantic schemas
3. **Use parameterized queries** (SQLAlchemy ORM)
4. **Implement rate limiting** on auth endpoints
5. **Keep dependencies updated**

## Git Workflow

### Branch Naming

- Features: `feat/short-description`
- Bugfixes: `fix/short-description`
- Hotfixes: `hotfix/short-description`
- Docs: `docs/short-description`

### Commit Messages

```
type(scope): Short description

Longer description if needed.

- Bullet points for details
- More context

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Template

1. **Summary**: What does this PR do?
2. **Changes**: Bullet list of changes
3. **Test Plan**: How to verify the changes
4. **Screenshots**: For UI changes
5. **Notes**: Any additional context

## Documentation

### Code Comments

```python
# Good - Explain WHY, not WHAT
# Use cached results to avoid rate limiting on Finnhub API
cached_data = cache.get(cache_key)

# Bad - States the obvious
# Get data from cache
cached_data = cache.get(cache_key)
```

### Docstrings

```python
async def fetch_company_news(
    ticker: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> List[News]:
    """
    Fetch company news from external API.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format

    Returns:
        List of news articles

    Raises:
        HTTPException: If API request fails
    """
    pass
```

## Monitoring & Observability

1. **Structured Logging**: All logs in JSON format
2. **Metrics**: Prometheus metrics for key operations
3. **Tracing**: Track request flow through system
4. **Alerts**: Set up for critical errors

## Development Workflow

1. **Create branch** from main
2. **Implement changes** following conventions
3. **Write tests** for new functionality
4. **Run linters**: `black`, `ruff`, `mypy`
5. **Run tests**: `pytest`
6. **Create PR** with description
7. **Address review** comments
8. **Merge** when approved

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
