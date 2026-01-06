import asyncio
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import redis.asyncio as redis

from app.core.config import settings
from app.core.security import decode_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
        # websocket -> subscribed tickers
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket, user_id: UUID):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    def subscribe(self, websocket: WebSocket, tickers: Set[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(tickers)

    def unsubscribe(self, websocket: WebSocket, tickers: Set[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket] -= tickers

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def broadcast_to_user(self, user_id: UUID, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await self.send_personal_message(message, connection)

    async def broadcast_news(self, ticker: str, news_data: dict):
        """Broadcast news to all users subscribed to this ticker"""
        for websocket, subscribed_tickers in self.subscriptions.items():
            if ticker in subscribed_tickers or "*" in subscribed_tickers:
                await self.send_personal_message(
                    {"type": "news", "ticker": ticker, "data": news_data},
                    websocket
                )


manager = ConnectionManager()


@router.websocket("/news")
async def websocket_news(
    websocket: WebSocket,
    token: str = Query(...),
):
    # Validate token
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = UUID(payload.get("sub"))
    await manager.connect(websocket, user_id)

    # Start Redis subscription listener
    redis_client = redis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("news_updates")

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    ticker = data.get("ticker")
                    if ticker:
                        await manager.broadcast_news(ticker, data)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe("news_updates")
            await redis_client.close()

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                tickers = set(data.get("tickers", []))
                manager.subscribe(websocket, tickers)
                await manager.send_personal_message(
                    {"type": "subscribed", "tickers": list(tickers)},
                    websocket
                )

            elif action == "unsubscribe":
                tickers = set(data.get("tickers", []))
                manager.unsubscribe(websocket, tickers)
                await manager.send_personal_message(
                    {"type": "unsubscribed", "tickers": list(tickers)},
                    websocket
                )

            elif action == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        listener_task.cancel()
    except Exception:
        manager.disconnect(websocket, user_id)
        listener_task.cancel()
