String FREQ_GRUPO = "923500000";  
String SF = "7";                 
String BANDWIDTH = "125";         
String CODING_RATE = "0";         
String PREAMBLE_LENGTH = "10";    
String TRANSMIT_POWER = "14";     

#define SerialRAK Serial1 

struct MPPTData {
  uint16_t duty;
  uint16_t voltage;
  uint16_t current;
};  

MPPTData data;

int pin = 9;

float emav = 0;
float alpha_v = 0.05; 
float emac = 0;
float alpha_c = 0.05;

const float sensitivity = 0.100; 
float zero_offset_volts = 2.5;

// --- AJUSTE 1: Arrancar mas cerca del MPP ---
int dutyCycle = 80; 
int maxDuty = 150;
int minDuty = 10;
int stepSize = 5; 

const int NUM_MUESTRAS_MEDIANA = 15; 
int bufferV[NUM_MUESTRAS_MEDIANA];
int bufferI[NUM_MUESTRAS_MEDIANA];

float last_v = 0.0;
float last_i = 0.0;
float current_v = 0.0;
float current_i = 0.0;

// --- AJUSTE 2: Tolerancia fina ---
float tolerance = 0.01; 

void sendRAK(String message) {
  Serial.print("Comando enviado: ");
  Serial.println(message);

  while(Serial2.available()) { Serial2.read(); }

  Serial2.println(message);
  Serial.print("Esperando respuesta");

  while (Serial2.available() == 0) {
    delay(500);         
    Serial.print(".");  
  }
  
  Serial.println(""); 
  
  String response = "";
  while (Serial2.available() > 0) {
    char c = (char)Serial2.read();
    response += c;
    delay(2); 
  }
  
  Serial.print("Respuesta RAK: ");
  Serial.println(response);
}

int leerMediana(int pinADC) {
  int rawValues[NUM_MUESTRAS_MEDIANA];
  
  for (int i = 0; i < NUM_MUESTRAS_MEDIANA; i++) {
    rawValues[i] = analogRead(pinADC);
    delayMicroseconds(50); 
  }

  for (int i = 0; i < NUM_MUESTRAS_MEDIANA - 1; i++) {
    for (int j = 0; j < NUM_MUESTRAS_MEDIANA - i - 1; j++) {
      if (rawValues[j] > rawValues[j + 1]) {
        int temp = rawValues[j];
        rawValues[j] = rawValues[j + 1];
        rawValues[j + 1] = temp;
      }
    }
  }
  return rawValues[NUM_MUESTRAS_MEDIANA / 2];
}

void setup() {
  Serial.begin(115200); 
  Serial2.begin(115200); 

  delay(1000);

  Serial.println("Iniciando configuracion...");

  while (!Serial) {}

  sendRAK("at+ver=?");
  delay(1000);
  sendRAK("at+NWM=0");
  delay(1000);
  sendRAK("at+P2P=" + FREQ_GRUPO + ":" + SF + ":" + BANDWIDTH + ":" + CODING_RATE + ":" + PREAMBLE_LENGTH + ":" + TRANSMIT_POWER);
  delay(1000);
  sendRAK("at+PRECV=0"); 
  delay(1000);

  pinMode(pin, OUTPUT);

  TCCR1B = (TCCR1B & 0b11111000) | 0x01;

  Serial.println("CALIBRANDO SENSOR...");
  
  long totalRaw = 0;
  for(int i=0; i<200; i++) {
    totalRaw += leerMediana(A3); 
    delay(2);
  }
  zero_offset_volts = (totalRaw / 200.0) * (5.0 / 1023.0);
  
  Serial.print("Cero calibrado (V): ");
  Serial.println(zero_offset_volts, 4);
  
  analogWrite(pin, dutyCycle);
  delay(200);

  long sumV = 0;
  for(int i=0; i<20; i++) sumV += leerMediana(A5);
  emav = (sumV/20.0) * (25.0 / 1023.0); 
  
  last_v = emav;
  last_i = 0;
}

int Lora_timer = 0;

void leerSensores() {
  long sumV = 0;
  long sumI = 0;
  int MUESTRAS_PROMEDIO = 10; 
  
  for(int i=0; i<MUESTRAS_PROMEDIO; i++) {
    sumV += leerMediana(A5); 
    sumI += leerMediana(A3); 
  }
  
  float rawV_limpio = sumV / (float)MUESTRAS_PROMEDIO;
  float rawI_limpio = sumI / (float)MUESTRAS_PROMEDIO;

  double voltage = rawV_limpio * (25.0 / 1023.0); 
  emav = alpha_v * voltage + (1.0 - alpha_v) * emav;

  float voltad = rawI_limpio * (5.0 / 1023.0);
  float diff = abs(voltad - zero_offset_volts);
  float current_raw = diff / sensitivity;

  if (current_raw < 0.10) current_raw = 0;

  emac = alpha_c * current_raw + (1.0 - alpha_c) * emac;
  
  current_v = emav;
  current_i = emac;
}

void MPPT_control(){
 
 if (current_v < 1.0) {
    dutyCycle = 20; 
    return;
 }

 float dv = current_v -  last_v;
 float di = current_i - last_i;
 
 float incCond = 0;
 if (abs(dv) > 0.001) incCond = di / dv; 
 float instCond = -1.0 * (current_i / current_v);

 // --- Lógica Híbrida: Si dV es casi cero, usar P&O básico ---
 if(abs(dv) < tolerance){
    // Estamos en una zona plana, usar cambio de corriente/potencia para decidir
    if(abs(di) > tolerance){ 
      if(di > 0){
         // Si la corriente subió (y voltaje igual), potencia subió -> Seguir mismo camino
         // Asumimos subida de duty
         dutyCycle += stepSize;
      }else{
         // Corriente bajó -> Retroceder
         dutyCycle -= stepSize;
      }
    }
    // Si ni V ni I cambian, es estable (MPP o ruido)
 }
 else {
     // Si hay cambios de voltaje, usar Conductancia Incremental
     if(abs(incCond - instCond) < tolerance) {
        Serial.println("ECONTRANDO ");
     }else if(incCond > instCond){
       dutyCycle -= stepSize; 
     }else if(incCond < instCond){
       dutyCycle += stepSize; 
     }
  }

  dutyCycle = constrain(dutyCycle, minDuty, maxDuty);
  
  last_v = current_v;
  last_i = current_i;
}

void loop() {
 
  analogWrite(pin, dutyCycle);

  delay(100); 

  for(int i=0; i<20; i++) {
    leerSensores();
    delay(2);
  }

  MPPT_control();

  Serial.print(dutyCycle);
  Serial.print(",");
  Serial.print(current_v, 3);
  Serial.print(",");
  Serial.println(current_i, 3);

      Lora_timer = millis();
      data.voltage = current_v * 1000;
      data.current = current_i * 1000;
      data.duty = dutyCycle;

      char payload[13]; 
      snprintf(payload, sizeof(payload), "%04X%04X%04X", data.duty, data.voltage, data.current);

      Serial.print("Enviando LoRa: ");
      Serial.println(payload);

      sendRAK("at+PSEND=" + String(payload));
 
}