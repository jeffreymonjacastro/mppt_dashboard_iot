from typing import Dict

def hex_to_string(hex_str: str) -> str:
    """
    Convierte una cadena hexadecimal a su representación en texto.
    - **hex_str**: String en formato hexadecimal (ej: "48656C6C6F")
    - **return**: String decodificado (ej: "Hello")
    """
    try:
        result = ""
        for i in range(0, len(hex_str), 2):
            hex_pair = hex_str[i:i+2]
            result += chr(int(hex_pair, 16))
        return result
    except (ValueError, TypeError):
        return ""

def parse_lora_data(raw_data: str) -> Dict:
    """
    Parsea datos LoRa con formato: +EVT:RXP2P:POT:SNR:PAYLOAD
    - **raw_data**: String en formato LoRa
    - **return**: Dict con POT, SNR, PAYLOAD parseados
    """
    try:
        if not raw_data.startswith("+EVT:RXP2P:"):
            return None
        
        data_part = raw_data.replace("+EVT:RXP2P:", "")
        
        parts = data_part.split(":")
        
        if len(parts) >= 3:
            return {
                "POT": parts[0],
                "SNR": parts[1],
                "PAYLOAD": hex_to_string(parts[2])
            }
        return None
    except Exception as e:
        print(f"Error al parsear datos LoRa: {e}")
        return None

