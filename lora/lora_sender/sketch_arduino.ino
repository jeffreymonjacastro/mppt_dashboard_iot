#include <HardwareSerial.h>
#define VRX_PIN 34
#define VRY_PIN 35
#define SW_PIN 23

HardwareSerial SerialRAK(2);

int valx = 0;
int valy = 0;
bool valsw = 0;

//int num = 0;
//String hexNum;
String hexValx;
String hexValy;
String hexValsw;
String message;

void sendCommand(String cmd, int timeout = 2000) {
  SerialRAK.println(cmd);

  long startTime = millis();
  while (millis() - startTime < timeout) {
    if (SerialRAK.available()) {
      String response = SerialRAK.readStringUntil('\n');
      response.trim(); // Limpia espacios en blanco o saltos de línea
      
      if (response.length() > 0) {
        Serial.println(response);
      }
    }
  }
  // Serial.println("--------------------");
}

String stringToHex(String str) {
  String hexString = "";
  for (int i = 0; i < str.length(); i++) {
    char hex[3];
    sprintf(hex, "%02X", str[i]);
    hexString += hex;
  }
  return hexString;
}

void setup() {
  // RAK LoRa
  Serial.begin(115200);
  
  while (!Serial) {
    ; 
  }

  SerialRAK.begin(115200, SERIAL_8N1, 16, 17); 

  delay(2000); 
  
  // Serial.println("Iniciando configuracion LoRa P2P en RAK (Transmisor)...");

  sendCommand("at+ver=?");
  
  sendCommand("at+NWM=0");
  
  sendCommand("at+P2P=923500000:7:125:0:10:14");
  
  sendCommand("at+PRECV=0");

  // Serial.println("--------------------");
  // Serial.println("Configuracion completa. Iniciando transmision...");

  // Input > Joystick
  pinMode(SW_PIN, INPUT_PULLUP);
}

void loop() {
  //num = num + 1;
  //hexNum = stringToHex(String(num));
  
  // Serial.println(num);
  
  //sendCommand("at+PSEND=" + String(hexNum));
  
  valx = analogRead(VRX_PIN);
  valy = analogRead(VRY_PIN);
  valsw = digitalRead(SW_PIN) == LOW;

  hexValx = stringToHex(String(valx) + " ");
  hexValy = stringToHex(String(valy) + " ");
  hexValsw = stringToHex(String(valsw));

  message = hexValx + hexValy + hexValsw;

  sendCommand("at+PSEND=" + message);

  delay(5000);
}