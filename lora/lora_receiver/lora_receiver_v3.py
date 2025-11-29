import serial
import time
import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

PORT = 'COM6'  
BAUD_RATE = 115200

# --- CONFIGURACIÓN DE LARGA DISTANCIA (Debe coincidir con el Sender) ---
FREQ_GRUPO = "923500000"
SF = 7                # CAMBIO: Subimos a 12 para igualar al sender
BANDWIDTH = 125
CODING_RATE = 0        # CAMBIO: 3 equivale a 4/8 (Mayor corrección de errores)
PREAMBLE_LENGTH = 10   # CAMBIO: Aumentado para mejor detección
TRANSMIT_POWER = 14    # CAMBIO: Máxima potencia (para cuando el receptor tenga que responder)

LOG_DIR = 'logs'
RECONNECT_DELAY = 5 

BACKEND_URL = os.getenv("BACKEND_URL")

os.makedirs(LOG_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file_path = os.path.join(LOG_DIR, f"log_{timestamp}.txt")

print(f"Iniciando Receptor LoRa (SF{SF})... Log en: {output_file_path}")

def send_at_command(ser, cmd):
    """Envía un comando AT al RAK y muestra la respuesta."""
    print(f"Enviando al RAK: {cmd}")
    ser.write((cmd + '\r\n').encode('utf-8'))
    time.sleep(1) # Un poco menos de delay suele ser suficiente
    
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    
    if response:
        print(f"Respuesta del RAK: {response.strip()}")
    return response

def parse_lora_packet(raw_line):
    """
    Intenta extraer y decodificar el payload hexadecimal.
    Formato esperado RAK: +EVT:RXP2P:RSSI:SNR:PAYLOAD
    Ejemplo Payload Hex: 0FFF080001 (X: 0FFF, Y: 0800, SW: 01)
    """
    try:
        if "+EVT:RXP2P" in raw_line:
            parts = raw_line.split(':')
            payload_hex = parts[-1].strip()
            
            if len(payload_hex) == 12:
                duty = int(payload_hex[0:4], 16) 
                voltage = int(payload_hex[4:8], 16) / 1000.0
                current = int(payload_hex[8:12], 16) / 1000.0
                
                pot = int(parts[-3]) if len(parts) >= 3 else 0
                snr = int(parts[-2]) if len(parts) >= 2 else 0

                return {
                    "valid": True,
                    "duty": duty,
                    "voltage": voltage,
                    "current": current,
                    "pot": pot,
                    "snr": snr,
                    "raw_hex": payload_hex
                }
    except Exception as e:
        print(f"Error parseando linea: {e}")
        
    return {"valid": False}

while True:
    ser = None 
    try:
        print(f"\nConectando al RAK receptor en {PORT}...")
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
        print(f"¡Conectado! Configurando parámetros LoRa SF{SF}...")

        # Detener recepción anterior por si acaso
        send_at_command(ser, "AT+PRECV=0")
        
        send_at_command(ser, "AT+NWM=0")
        p2p_config_cmd = f"AT+P2P={FREQ_GRUPO}:{SF}:{BANDWIDTH}:{CODING_RATE}:{PREAMBLE_LENGTH}:{TRANSMIT_POWER}"
        send_at_command(ser, p2p_config_cmd)
        send_at_command(ser, "AT+PRECV=65534")
        
        print("--- Receptor Listo y Escuchando ---")
        
        with open(output_file_path, 'a') as f:
            f.write(f"--- Inicio de sesión: {datetime.now()} ---\n")
            
            while True:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if linea:
                    print(f"[RAW] {linea}")
                    f.write(linea + '\n')
                    f.flush() 

                    data = parse_lora_packet(linea)
                    
                    if data["valid"]:
                        print(f">>> DECÓDIFICADO: duty={data['duty']}, voltage={data['voltage']}, current={data['current']}")
                        
                        json_data = {
                            "duty": data['duty'],
                            "voltage": data['voltage'],
                            "current": data['current'],
                            "pot": data['pot'],
                            "snr": data['snr'],
                            "timestamp": datetime.now().isoformat()
                        }

                        # Enviar a la API
                        if BACKEND_URL:
                            try:
                                requests.post(f"{BACKEND_URL}/api/v1/lora-data", json=json_data, timeout=2)
                            except requests.exceptions.RequestException as e:
                                print(f"   [!] Error API: {e}")
                    
    except serial.SerialException as e:
        print(f"\nError Serial: {e}")
        print(f"Reintentando en {RECONNECT_DELAY} segundos...")
        
    except KeyboardInterrupt:
        print("\nDeteniendo script...")
        break 
        
    finally:
        if ser and ser.is_open:
            try:
                ser.close()
            except: pass
            print("Puerto cerrado.")
            
    time.sleep(RECONNECT_DELAY)