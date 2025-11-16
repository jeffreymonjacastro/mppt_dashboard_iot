# FastAPI Backend - Tutorial de Ejecución

## Requisitos Previos
- Python 3.8 o superior instalado
- pip (gestor de paquetes de Python)

## Pasos para Ejecutar el Backend

### 1. Navegar a la carpeta del API
```powershell
cd api
```

### 2. Crear un entorno virtual (opcional pero recomendado)
```powershell
python -m venv venv
```

### 3. Activar el entorno virtual
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Instalar las dependencias
```powershell
pip install -r requirements.txt
```

### 5. Ejecutar el servidor
```powershell
uvicorn main:app --reload --port 8000
```

El flag `--reload` permite que el servidor se reinicie automáticamente cuando detecte cambios en el código (útil para desarrollo).

### 6. Acceder al backend

Una vez que el servidor esté corriendo, podrás acceder a:

- **Endpoint principal**: http://localhost:8000/
  - Respuesta: `{"message": "Hello World"}`

- **Endpoint con parámetro**: http://localhost:8000/hello/TuNombre
  - Respuesta: `{"message": "Hello TuNombre"}`

- **Documentación interactiva (Swagger UI)**: http://localhost:8000/docs
  - FastAPI genera automáticamente una interfaz para probar tus endpoints

- **Documentación alternativa (ReDoc)**: http://localhost:8000/redoc

## Cambiar el Puerto

Si necesitas usar un puerto diferente, modifica el comando:
```powershell
uvicorn main:app --reload --port 3001
```

## Detener el Servidor

Presiona `Ctrl + C` en la terminal para detener el servidor.

## Desactivar el Entorno Virtual

Cuando termines de trabajar:
```powershell
deactivate
```
