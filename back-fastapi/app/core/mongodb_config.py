from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from os import getenv
from typing import AsyncGenerator 

load_dotenv()

@asynccontextmanager
async def lifespan_mongodb(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestiona la conexión/desconexión a MongoDB.
    """
    print("--- Iniciando y conectando a MongoDB... ---")

    MONGO_URI = getenv("MONGO_URI") 
    
    # Asigna el cliente y la base de datos al estado de la aplicación
    # para que sean accesibles desde cualquier lugar.
    app.state.mongo_client = AsyncIOMotorClient(MONGO_URI)
    app.state.db = app.state.mongo_client["lora_db"]

    print("--- Conectado a MongoDB Atlas ---")
    
    yield # <-- La aplicación se ejecuta aquí
    
    # --- Código de "shutdown" ---
    print("--- Cerrando conexión a MongoDB... ---")

    app.state.mongo_client.close()

    print("--- Desconectado de MongoDB Atlas ---")