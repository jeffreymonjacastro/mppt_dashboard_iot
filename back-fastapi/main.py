import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager # <--- ¡IMPORTAR ESTO!

BOGOTA_TZ = timezone(timedelta(hours=-5))

# --- Administrador de Conexiones WebSocket 
class ConnectionManager:
    def __init__(self):
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Código de "startup" (antes del yield) ---
    print("--- Iniciando y conectando a MongoDB... ---")

    MONGO_URI = getenv("MONGO_URI")
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
    app.state.db = app.state.mongo_client["lora_db"]

    print("--- Conectado a MongoDB Atlas ---")
    
    yield # <-- La aplicación se ejecuta aquí
    
    # --- Código de "shutdown" (después del yield) ---
    print("--- Cerrando conexión a MongoDB... ---")

    app.state.mongo_client.close()

    print("--- Desconectado de MongoDB Atlas ---")


app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://mppt-dashboard-iot.vercel.app", 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/lora-data")
async def receive_lora_data(data: Dict, request: Request):
    linea = data.get("raw_data")

    if linea:
        print(f"Dato recibido: {linea}")
        try:
            collection = request.app.state.db["lecturas"]
            documento = {
                "raw_data": linea,
                "timestamp": datetime.now(BOGOTA_TZ)
            }
            await collection.insert_one(documento)
            print("--- Dato guardado en MongoDB ---")
        except Exception as e:
            print(f"!!! Error al guardar en MongoDB: {e}")
        
        await manager.broadcast(linea)
        return {"status": "ok", "dato_recibido": linea}
    else:
        return {"status": "error", "mensaje": "No 'raw_data' key found"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    print("Nuevo cliente frontend conectado.")

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Cliente frontend desconectado.")