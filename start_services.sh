#!/bin/bash

# Array para almacenar los IDs de los procesos
pids=()

# Función de limpieza para matar los procesos al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo todos los servicios..."
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
        fi
    done
    echo "✅ Todo cerrado."
    exit 0
}

# Capturar Ctrl+C (SIGINT)
trap cleanup SIGINT

echo "🚀 Iniciando sistema..."

# 1. Backend
echo "----------------------------------------"
echo "📡 Iniciando Backend (FastAPI)..."
(
    cd back-fastapi
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    uvicorn app.main:app --reload > /dev/null 2>&1
) &
pids+=($!)

# Esperar un poco para que el backend arranque
sleep 3

# 2. Frontend
echo "----------------------------------------"
echo "💻 Iniciando Frontend (Next.js)..."
(
    cd front-nextjs
    npm run dev > /dev/null 2>&1
) &
pids+=($!)

# Esperar un poco para que el frontend arranque
sleep 3

# 3. LoRa Receiver
echo "----------------------------------------"
echo "📻 Iniciando LoRa Receiver..."
(
    cd lora
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    cd lora_receiver
    python lora_receiver_v3.py
) &
pids+=($!)

echo "----------------------------------------"
echo "✨ Todos los servicios están corriendo."
echo "Presiona Ctrl + C para detener todo."

# Esperar indefinidamente
wait
