# Market Atlas

AI-powered investment research platform for fund managers.

## Features

- **Watchlist Management** - Track stocks with real-time news monitoring
- **SEC Filing Analysis** - Automatic analysis of 10-K, 10-Q, 8-K filings
- **Earnings Call Analysis** - AI-powered analysis of earnings transcripts
- **AI Discovery Engine** - Discover potential investment opportunities based on themes
- **Telegram Notifications** - Get notified when research completes or important news arrives

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python FastAPI, SQLAlchemy, Celery
- **Database**: PostgreSQL, Redis
- **AI**: Anthropic Claude API
- **Data Sources**: Finnhub, Polygon.io, SEC EDGAR, Financial Modeling Prep

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+
- Python 3.12+

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jacksu4/Market-Atlas.git
cd Market-Atlas
```

2. Copy environment file and add your API keys:
```bash
cp .env.example .env
```

Required API keys:
- `ANTHROPIC_API_KEY` - [Get from Anthropic](https://console.anthropic.com)
- `FINNHUB_API_KEY` - [Get from Finnhub](https://finnhub.io)
- `POLYGON_API_KEY` - [Get from Polygon](https://polygon.io)
- `FMP_API_KEY` - [Get from FMP](https://financialmodelingprep.com)
- `TELEGRAM_BOT_TOKEN` - [Get from @BotFather](https://t.me/BotFather)

3. Start with Docker Compose:
```bash
cd docker
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Celery Worker:**
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

**Celery Beat (scheduler):**
```bash
cd backend
celery -A app.core.celery_app beat --loglevel=info
```

## Project Structure

```
Market-Atlas/
├── frontend/              # Next.js frontend
│   ├── src/
│   │   ├── app/          # App router pages
│   │   ├── components/   # React components
│   │   ├── lib/          # Utilities and API client
│   │   ├── hooks/        # Custom React hooks
│   │   └── types/        # TypeScript types
│   └── ...
│
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── tasks/        # Celery tasks
│   ├── alembic/          # Database migrations
│   └── ...
│
├── docker/                # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
└── .env                   # Environment variables (not in git)
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License - see [LICENSE](LICENSE) for details.
