import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, OperationFailure

MONGO_URI = "mongodb+srv://mongo:123@cluster0.75movzl.mongodb.net/?appName=Cluster0"


async def test_mongo_connection():
    print(f"Intentando conectar a: {MONGO_URI.split('@')[-1]}")
    client = None
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        await client.admin.command('ping')
        
        print("\n******************************************")
        print("¡ÉXITO! Conexión y autenticación correctas.")
        print("******************************************")

    except OperationFailure as e:
        print("\n¡ERROR DE AUTENTICACIÓN!")
        print("La conexión al servidor fue exitosa, pero el usuario o contraseña son incorrectos.")
        print(f"Detalle del error: {e.details.get('errmsg', e)}")
        print("\nRECUERDA: Si esto sigue fallando, la causa más probable")
        print("es un carácter especial (@ : / %) en tu contraseña.")
        
    except ConnectionFailure as e:
        print("\n¡ERROR DE CONEXIÓN!")
        print("No se pudo conectar al servidor. Revisa 'Network Access' (debe ser 0.0.0.0/0).")
        print(f"Detalle del error: {e}")
        
    except Exception as e:
        print(f"\nOcurrió un error inesperado: {e}")
        
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    asyncio.run(test_mongo_connection())