from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.mongodb_config import lifespan_mongodb
from app.api import router_api

app = FastAPI(
    title="MPPT Dashboard IoT API",
    description="API para gestión y visualización de datos LoRa, almacenamiento en MongoDB y comunicación en tiempo real vía WebSocket.",
    version="1.0.0",
    lifespan=lifespan_mongodb
)

app.include_router(router_api, prefix="/api/v1")

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the MPPT Dashboard IoT API!"}