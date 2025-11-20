import json
from fastapi import APIRouter
from typing import Dict
from fastapi import Request
from app.lib.utils import parse_lora_data
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
    Recibe datos LoRa en formato JSON, parsea los datos y los almacena en MongoDB.
    - **data**: JSON con la clave `raw_data` (string en formato +EVT:RXP2P:POT:SNR:PAYLOAD)
    """
    linea = data.get("raw_data")
    if not linea:
        return {"status": "error", "mensaje": "No 'raw_data' key found"}
    
    print(f"Dato recibido: {linea}")
    
    parsed_data = parse_lora_data(linea)
    
    if parsed_data:
        structured_data = {
            "POT": parsed_data["POT"],
            "SNR": parsed_data["SNR"],
            "PAYLOAD": parsed_data["PAYLOAD"],
            "timestamp": data.get("timestamp"),
            "raw_data": linea  
        }
        
        print(f"Dato parseado: {structured_data}")
        
        # Guardar en MongoDB
        # try:
        #     collection = request.app.state.db["lecturas"]
        #     await collection.insert_one(structured_data)
        #     print("--- Dato guardado en MongoDB ---")
        # except Exception as e:
        #     print(f"!!! Error al guardar en MongoDB: {e}")
        
        for key, value in structured_data.items():
            if isinstance(value, ObjectId):
                structured_data[key] = str(value)

        await manager.broadcast(json.dumps(structured_data))
        
        return {
            "status": "ok", 
            "dato_recibido": linea,
            "dato_parseado": structured_data
        }
    else:
        print(f"No se pudo parsear el dato, guardando raw_data")
        fallback_data = {
            "raw_data": linea,
            "timestamp": data.get("timestamp")
        }
        
        try:
            collection = request.app.state.db["lecturas"]
            await collection.insert_one(fallback_data)
            print("--- Dato raw guardado en MongoDB ---")
        except Exception as e:
            print(f"!!! Error al guardar en MongoDB: {e}")
        
        await manager.broadcast(json.dumps(fallback_data))
        
        return {
            "status": "ok", 
            "dato_recibido": linea,
            "warning": "Datos no parseados, formato no reconocido"
        }