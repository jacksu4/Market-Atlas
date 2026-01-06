from fastapi import APIRouter

from app.api.v1 import auth, watchlist, news, research, websocket, stocks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(watchlist.router, prefix="/watchlists", tags=["Watchlists"])
api_router.include_router(news.router, prefix="/news", tags=["News"])
api_router.include_router(research.router, prefix="/research", tags=["Research"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
