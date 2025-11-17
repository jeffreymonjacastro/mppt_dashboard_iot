import serial
import time
import os
import sys
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

PORT = 'COM6'  
BAUD_RATE = 115200

FREQ_GRUPO = "923500000"
SF = 7
BANDWIDTH = 125
CODING_RATE = 0
PREAMBLE_LENGTH = 10
TRANSMIT_POWER = 14

LOG_DIR = 'logs'
RECONNECT_DELAY = 5 

BACKEND_URL = os.getenv("BACKEND_URL")

os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file_path = os.path.join(LOG_DIR, f"log_{timestamp}.txt")

print(f"Iniciando script... Log en: {output_file_path}")
print(f"Enviando datos en vivo a: {BACKEND_URL}")

def send_at_command(ser, cmd):
    """Envía un comando AT al RAK y muestra la respuesta."""

    print(f"Enviando al RAK: {cmd}")
    ser.write((cmd + '\r\n').encode('utf-8'))
    
    time.sleep(2) 
    
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode('utf-8')
    
    if response:
        print(f"Respuesta del RAK: {response.strip()}")
    return response


while True:
    ser = None 
    try:
        print(f"\nIntentando conectar al RAK receptor en {PORT}...")
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print(f"¡Conectado! Configurando módulo RAK...")

        send_at_command(ser, "AT+NWM=0")
        p2p_config_cmd = f"AT+P2P={FREQ_GRUPO}:{SF}:{BANDWIDTH}:{CODING_RATE}:{PREAMBLE_LENGTH}:{TRANSMIT_POWER}"
        send_at_command(ser, p2p_config_cmd)
        send_at_command(ser, "AT+PRECV=65534")
        
        print("--- Configuración de Receptor P2P completada ---")
        
        print(f"Escuchando mensajes... Guardando en {output_file_path} (Presiona Ctrl+C para parar)")
        
        with open(output_file_path, 'a') as f:
            f.write(f"--- (Re)conexión establecida: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.flush()
            
            while True:
                linea = ser.readline().decode('utf-8').strip()
                
                if linea:
                    print(linea)
                    f.write(linea + '\n')
                    f.flush() 

                    try:
                        requests.post(BACKEND_URL, json={"raw_data": linea}, timeout=5)
                    except requests.exceptions.RequestException as e:
                        print(f"!!! Error al enviar a la API: {e}")

    except serial.SerialException as e:
        print(f"\nError: {e}")
        print("El dispositivo se ha desconectado o no se pudo encontrar.")
        print(f"Esperando {RECONNECT_DELAY} segundos antes de reintentar...")
        
    except KeyboardInterrupt:
        print("\nDeteniendo la captura de datos por el usuario.")
        break 
        
    finally:
        if ser and ser.is_open:
            print("Cerrando puerto serial...")
            try:
                send_at_command(ser, "AT+PRECV=0")
            except Exception:
                pass 
            ser.close()
            print(f"Puerto serial {PORT} cerrado.")
            
    
    time.sleep(RECONNECT_DELAY)

print("Script finalizado.")