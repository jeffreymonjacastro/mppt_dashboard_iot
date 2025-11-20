from fastapi import APIRouter, Request, Body
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/history",
    tags=["History"],
)

class LecturasRequest(BaseModel):
    time: int  # cantidad de tiempo
    unit: str  # 'min', 'hour', 'day'
    skip: int = 0  # para paginación
    limit: int = 100  # máximo de lecturas a retornar

@router.post(
        "/", 
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
    now = datetime.now()
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