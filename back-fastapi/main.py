import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from datetime import datetime, timezone, timedelta
from os import getenv
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.responses import JSONResponse

load_dotenv()

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


app = FastAPI(
    title="MPPT Dashboard IoT API",
    description="API para gestión y visualización de datos LoRa, almacenamiento en MongoDB y comunicación en tiempo real vía WebSocket.",
    version="1.0.0",
    lifespan=lifespan
)

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

@app.get(
        "/health", 
        tags=["Utilidad"], 
        summary="Verifica el estado de la API"
)
async def health_check():
    """Endpoint simple para verificar que la API está corriendo correctamente."""
    return {"status": "ok"}

@app.post(
        "/api/lora-data", 
        tags=["LoRa"], 
        summary="Recibe y almacena datos LoRa"
)
async def receive_lora_data(data: Dict, request: Request):
    """
    Recibe datos LoRa en formato JSON, los almacena en MongoDB y los transmite a los clientes WebSocket conectados.
    - **data**: JSON con la clave `raw_data` (string)
    """
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


# --- Endpoint para lecturas históricas con paginación y filtro de tiempo ---

class LecturasRequest(BaseModel):
    time: int  # cantidad de tiempo
    unit: str  # 'min', 'hour', 'day'
    skip: int = 0  # para paginación
    limit: int = 100  # máximo de lecturas a retornar

@app.post(
        "/api/lecturas", 
        tags=["Lecturas"], 
        summary="Obtiene lecturas históricas de LoRa"
)
async def get_lecturas(
    params: LecturasRequest = Body(..., example={"time": 30, "unit": "min", "skip": 0, "limit": 100}),
    request: Request = None
):
    """
    Devuelve lecturas históricas almacenadas en MongoDB, filtradas por rango de tiempo y paginadas.
    - **time**: cantidad de tiempo (entero)
    - **unit**: unidad de tiempo ('min', 'hour', 'day')
    - **skip**: cantidad de lecturas a omitir (para paginación)
    - **limit**: máximo de lecturas a retornar
    """
    now = datetime.now(BOGOTA_TZ)
    if params.unit == 'min':
        delta = timedelta(minutes=params.time)
    elif params.unit == 'hour':
        delta = timedelta(hours=params.time)
    elif params.unit == 'day':
        delta = timedelta(days=params.time)
    else:
        return JSONResponse(status_code=400, content={"error": "Unidad de tiempo no soportada"})
    start_time = now - delta
    collection = request.app.state.db["lecturas"]
    cursor = collection.find({"timestamp": {"$gte": start_time}}).sort("timestamp", 1).skip(params.skip).limit(params.limit)
    lecturas = []
    async for doc in cursor:
        lecturas.append({
            "raw_data": doc.get("raw_data"),
            "timestamp": doc.get("timestamp").isoformat() if doc.get("timestamp") else None
        })
    return {"lecturas": lecturas}