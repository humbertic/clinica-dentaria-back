# src/mensagens/ws.py
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}  # ex.: "clinica-3"

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        self.rooms.setdefault(room, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        self.rooms.get(room, set()).discard(websocket)

    async def broadcast(self, room: str, data: dict):
        dead = []
        for ws in self.rooms.get(room, set()):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.rooms[room].discard(ws)

manager = ConnectionManager()


async def clinic_chat_ws(websocket: WebSocket, clinica_id: int, user_id: int):
    room = f"clinica-{clinica_id}"
    await manager.connect(websocket, room)
    try:
        while True:
            await asyncio.sleep(60)  # ping noop para manter ligação
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
