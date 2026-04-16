from typing import Optional
from fastapi import WebSocket


class WebSocketManager:
    """Manages WebSocket connections grouped by conversation_id."""

    def __init__(self):
        # conversation_id -> set[WebSocket]
        self._connections: dict[str, set[WebSocket]] = {}
        # WebSocket -> Optional[str] (conversation_id)
        _ws_to_conv: dict[WebSocket, Optional[str]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self._connections:
            self._connections[conversation_id] = set()
        self._connections[conversation_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, conversation_id: str | None = None):
        if conversation_id and conversation_id in self._connections:
            self._connections[conversation_id].discard(websocket)
            if not self._connections[conversation_id]:
                del self._connections[conversation_id]

    async def send_to_conversation(self, conversation_id: str, data: dict):
        """Send a JSON message to all clients connected to this conversation."""
        import json
        if conversation_id in self._connections:
            payload = json.dumps(data)
            dead = set()
            for ws in self._connections[conversation_id]:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                self._connections[conversation_id].discard(ws)
            if not self._connections[conversation_id]:
                del self._connections[conversation_id]


# Global instance
ws_manager = WebSocketManager()
