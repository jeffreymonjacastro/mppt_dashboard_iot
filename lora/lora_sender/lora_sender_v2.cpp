#include <HardwareSerial.h>

#define VRX_PIN 34
#define VRY_PIN 35
#define SW_PIN 23

  // CONFIGURACIÓN OPTIMIZADA PARA ALCANCE:
String FREQ_GRUPO = "923500000";  // Frec: 923.5 MHz (Ajustar a tu región)
String SF = "12";                  // SF: 12 (Máximo alcance, lento)
String BANDWIDTH = "125";         // BW: 125 (125kHz)
String CODING_RATE = "3";         // CR: 3 (Coding Rate 4/8 - Máxima protección de errores)
String PREAMBLE_LENGTH = "12";    // Preamble: 12
String TRANSMIT_POWER = "20";     // Power: 22 (Máxima potencia 22dBm)

HardwareSerial SerialRAK(2);

struct JoystickData {
  uint16_t x;
  uint16_t y;
  uint8_t sw;
};

void sendCommand(String cmd, int timeout = 2000) {
  SerialRAK.println(cmd);
  long startTime = millis();
  while (millis() - startTime < timeout) {
    if (SerialRAK.available()) {
      String response = SerialRAK.readStringUntil('\n');
      response.trim();
      if (response.length() > 0) {
        Serial.println("RAK: " + response);
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000); 

  while (!Serial) {}

  // Inicializar Serial para RAK (RX:16, TX:17)
  SerialRAK.begin(115200, SERIAL_8N1, 16, 17); 
  delay(2000); 
  
  // Serial.println("Configurando RAK3172 para LARGA DISTANCIA...");

  sendCommand("at+ver=?");
  sendCommand("at+NWM=0");

  sendCommand("at+P2P=" + FREQ_GRUPO + ":" + PREAMBLE_LENGTH + ":" + BANDWIDTH + ":" + CODING_RATE + ":" + PREAMBLE_LENGTH + ":" + TRANSMIT_POWER);
  
  sendCommand("at+PRECV=0"); // Solo transmisión

  pinMode(SW_PIN, INPUT_PULLUP);
}

void loop() {
  JoystickData data;

  // Leer sensores
  data.x = analogRead(VRX_PIN);
  data.y = analogRead(VRY_PIN);
  data.sw = (digitalRead(SW_PIN) == LOW) ? 1 : 0;

  // Usamos buffer: 4 chars para X, 4 para Y, 2 para SW + nulo = 11
  char payload[12]; 
  
  // %04X formatea un entero a 4 digitos hex (ej: 4095 -> 0FFF)
  // %02X formatea un byte a 2 digitos hex (ej: 1 -> 01)
  snprintf(payload, sizeof(payload), "%04X%04X%02X", data.x, data.y, data.sw);

  Serial.print("Enviando Payload Hex: ");
  Serial.println(payload);

  sendCommand("at+PSEND=" + String(payload));

  delay(10000); 
}