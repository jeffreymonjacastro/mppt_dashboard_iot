from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket_manager import manager

router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)

@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para enviar datos LoRa en tiempo real a los clientes conectados.
    """
    await manager.connect(websocket)
    print("Nuevo cliente frontend conectado.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente frontend desconectado.")

