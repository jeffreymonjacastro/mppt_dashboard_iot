from fastapi import APIRouter

router = APIRouter(
    prefix="/basic",
    tags=["basic"],
)

@router.get(
        "/health", 
        summary="Verifica el estado de la API"
)
async def health_check():
    """Endpoint simple para verificar que la API está corriendo correctamente."""

    return {"status": "ok"}