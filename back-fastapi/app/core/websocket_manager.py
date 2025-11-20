from typing import List
from fastapi import WebSocket

# --- Administrador de Conexiones WebSocket ---
class ConnectionManager:
    """Gestiona las conexiones WebSocket activas."""
    def __init__(self):
        # Lista de WebSockets activos.
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()