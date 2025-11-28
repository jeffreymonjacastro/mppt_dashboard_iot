import json
from fastapi import APIRouter
from typing import Dict
from fastapi import Request
from bson import ObjectId
from app.core.websocket_manager import manager

router = APIRouter(
    prefix="/lora-data",
    tags=["lora-data"],
)

@router.post(
        "/", 
        summary="Recibe y almacena datos LoRa"
)
async def receive_lora_data(data: Dict, request: Request):
    """
    Recibe datos LoRa ya procesados en formato JSON y los almacena en MongoDB.
    Estructura esperada:
    {
        "duty": float,
        "voltage": float,
        "current": float,
        "pot": float/int,
        "snr": float/int,
        "timestamp": str (ISO format)
    }
    """
    print(f"Dato recibido: {data}")
    
    # Guardar en MongoDB
    # try:
    #     collection = request.app.state.db["lecturas"]
    #     await collection.insert_one(data.copy())
    #     print("--- Dato guardado en MongoDB ---")
    # except Exception as e:
    #     print(f"!!! Error al guardar en MongoDB: {e}")
    
    data_to_send = data.copy()
    for key, value in data_to_send.items():
        if isinstance(value, ObjectId):
            data_to_send[key] = str(value)

    await manager.broadcast(json.dumps(data_to_send))
    
    return {
        "status": "ok", 
        "dato_recibido": data
    }