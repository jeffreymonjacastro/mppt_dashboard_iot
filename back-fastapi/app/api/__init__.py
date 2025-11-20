from fastapi import APIRouter
from .endpoints import basic, history, lora, websocket

router_api = APIRouter()

router_api.include_router(basic.router)
router_api.include_router(history.router)
router_api.include_router(lora.router)
router_api.include_router(websocket.router)