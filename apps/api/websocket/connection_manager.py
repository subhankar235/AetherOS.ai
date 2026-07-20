import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger("websocket.connection_manager")


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)
        logger.info(f"WebSocket connected: user={user_id}, total={self._count(user_id)}")

    async def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if conns:
            conns.discard(websocket)
            if not conns:
                del self._connections[user_id]
        logger.info(f"WebSocket disconnected: user={user_id}, remaining={self._count(user_id)}")

    async def broadcast_to_user(self, user_id: str, event: dict[str, Any]) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        dead: set[WebSocket] = set()
        for ws in conns:
            try:
                await ws.send_json(event)
            except Exception:
                dead.add(ws)
        if dead:
            for ws in dead:
                conns.discard(ws)
            if not conns:
                del self._connections[user_id]

    def is_connected(self, user_id: str) -> bool:
        return user_id in self._connections and bool(self._connections[user_id])

    def _count(self, user_id: str) -> int:
        return len(self._connections.get(user_id, set()))


connection_manager = ConnectionManager()
