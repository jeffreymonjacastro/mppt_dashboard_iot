#include <HardwareSerial.h>

// Definimos el puerto serie que usaremos para el RAK3172
// GPIO 16 (RX2)
// GPIO 17 (TX2)
HardwareSerial SerialRAK(2);

// Variables globales de tu código Mega
int num = 0;
String hexNum;

/**
 * @brief Envía un comando AT al módulo RAK y espera la respuesta.
 * @param cmd El comando AT a enviar (sin incluir \r\n).
 * @param timeout Tiempo máximo de espera por una respuesta.
 */
void sendCommand(String cmd, int timeout = 2000) {
  // Imprime en el monitor serie lo que vamos a enviar
  // Serial.println(">> Enviando: " + cmd);
  
  // Envía el comando al módulo RAK
  SerialRAK.println(cmd);

  // Espera por la respuesta
  long startTime = millis();
  while (millis() - startTime < timeout) {
    if (SerialRAK.available()) {
      // Lee la respuesta línea por línea
      String response = SerialRAK.readStringUntil('\n');
      response.trim(); // Limpia espacios en blanco o saltos de línea
      
      // Imprime la respuesta del RAK en el monitor serie
      if (response.length() > 0) {
        // Serial.println("<< RAK dice: " + response);
        Serial.println(response);
      }
    }
  }
  // Serial.println("--------------------");
}

/**
 * @brief Convierte un String de texto a su representación en Hex.
 * (Función de tu código Mega)
 */
String stringToHex(String str) {
  String hexString = "";
  for (int i = 0; i < str.length(); i++) {
    char hex[3];
    // Nota: Corregí " %02X" a "%02X" para evitar espacios en el payload
    sprintf(hex, "%02X", str[i]);
    hexString += hex;
  }
  return hexString;
}

void setup() {
  // Inicia el monitor serie (para depuración)
  Serial.begin(115200);
  
  while (!Serial) {
    ; // Espera a que se conecte el puerto serie
  }

  // Inicia la comunicación con el RAK3172
  SerialRAK.begin(115200, SERIAL_8N1, 16, 17); // GPIO 16 (RX2), GPIO 17 (TX2)

  delay(2000); // Espera a que ambos se estabilicen
  
  // Serial.println("Iniciando configuracion LoRa P2P en RAK (Transmisor)...");

  // --- Comandos de configuración P2P (de tu código Mega) ---

  sendCommand("at+ver=?");
  
  // Poner en modo LoRa P2P (NWM=0)
  sendCommand("at+NWM=0");
  
  // Configurar parámetros P2P: Freq:923.5MHz, SF:7, BW:125, CR:0, Preamble:10, Power:14
  sendCommand("at+P2P=923500000:7:125:0:10:14");
  
  // Deshabilitar recepción continua (modo TX)
  sendCommand("at+PRECV=0");

  // Serial.println("--------------------");
  // Serial.println("Configuracion completa. Iniciando transmision...");
}

void loop() {
  // --- Lógica de transmisión (de tu código Mega) ---
  
  num = num + 1;
  hexNum = stringToHex(String(num));
  
  // Imprimir el número incremental
  // Serial.println(num);
  
  // Enviar el payload
  sendCommand("at+PSEND=" + String(hexNum));
  
  // Esperar 5 segundos
  delay(5000);
}