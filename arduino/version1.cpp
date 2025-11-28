String FREQ_GRUPO = "923500000";  // Frec: 923.5 MHz (Ajustar a tu región)
String SF = "7";                 // SF: 12 (Máximo alcance, lento)
String BANDWIDTH = "125";         // BW: 125 (125kHz)
String CODING_RATE = "0";         // CR: 3 (Coding Rate 4/8 - Máxima protección de errores)
String PREAMBLE_LENGTH = "10";    // Preamble: 12
String TRANSMIT_POWER = "14";     // Power: 22 (Máxima potencia 22dBm)

#define SerialRAK Serial1 

struct MPPTData {
  uint16_t duty;
  uint16_t voltage;
  uint16_t current;
};  

MPPTData data;

float const resistance = 0.001;
int pin = 9;

// --- CONFIGURACIÓN DE FILTRADO ---
// El Alpha determina la "inercia". 0.1 es rápido, 0.01 es muy lento pero suave.
float emav = 0;
float alpha_v = 0.05; 

float emac = 0;
float alpha_c = 0.05;

const float sensitivity = 0.100; // Ajustar según tu sensor (0.100 para 20A, 0.185 para 5A, etc.)
float zero_offset_volts = 2.5;

int dutyCycle = 0;
int maxDuty = 245;
int stepSize = 5;
bool experimentoTerminado = false;

// Variables para el filtro de mediana
const int NUM_MUESTRAS_MEDIANA = 15; // Debe ser impar
int bufferV[NUM_MUESTRAS_MEDIANA];
int bufferI[NUM_MUESTRAS_MEDIANA];

// Funciones LoRa
void sendRAK(String message) {
  Serial.print("Comando enviado: ");
  Serial.println(message);

  // 1. Limpiar cualquier basura que haya quedado en el buffer del RAK
  while(Serial2.available()) { Serial2.read(); }

  // 2. Enviar el mensaje al RAK
  Serial2.println(message);
  Serial.print("Esperando respuesta");

  // El código se queda aquí atrapado hasta que el RAK diga algo.
  while (Serial2.available() == 0) {
    delay(500);         // Revisar cada medio segundo
    Serial.print(".");  // Imprimir un punto para saber que sigue vivo
  }
  
  Serial.println(""); // Salto de línea estético
  
  // 4. Leer la respuesta completa del RAK
  String response = "";
  while (Serial2.available() > 0) {
    char c = (char)Serial2.read();
    response += c;
    delay(2); // Pequeña espera para no leer más rápido de lo que llegan los datos
  }
  
  Serial.print("Respuesta RAK: ");
  Serial.println(response);
}

void setup() {
  Serial.begin(115200); 
  Serial2.begin(115200); 

  delay(1000);

  Serial.println("Iniciando configuracion LoRa P2P en RAK (Transmisor)...");

  //Serial.begin(9600);

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

  // Frecuencia PWM alta (~31kHz en pines 9 y 10 para Arduino Uno/Nano)
  // Esto mueve el ruido a una frecuencia que es más fácil de filtrar
  TCCR1B = (TCCR1B & 0b11111000) | 0x01;

  //Serial.println("CALIBRANDO SENSOR...");
  
  // Calibración inicial robusta
  long totalRaw = 0;
  for(int i=0; i<200; i++) {
    totalRaw += leerMediana(A3); // Usamos la mediana incluso para calibrar
    delay(2);
  }
  zero_offset_volts = (totalRaw / 200.0) * (5.0 / 1023.0);
  
  //Serial.print("Cero calibrado (V): ");
  //Serial.println(zero_offset_volts, 4);
  
  // Pre-llenar filtros
  emav = leerMediana(A5) * (25.0 / 1023.0); 
  
  //Serial.println("Duty,Voltaje,Corriente"); 
  delay(1000);
}

// --- FUNCIÓN MAGICA: Filtro de Mediana ---
// Toma N lecturas, las ordena y devuelve la del centro.
// Esto ignora totalmente los picos de ruido esporádicos.
int leerMediana(int pinADC) {
  int rawValues[NUM_MUESTRAS_MEDIANA];
  
  // 1. Tomar lecturas rápidas
  for (int i = 0; i < NUM_MUESTRAS_MEDIANA; i++) {
    rawValues[i] = analogRead(pinADC);
    delayMicroseconds(50); // Pequeña pausa para estabilidad ADC
  }

  // 2. Ordenar el array (Bubble sort simple)
  for (int i = 0; i < NUM_MUESTRAS_MEDIANA - 1; i++) {
    for (int j = 0; j < NUM_MUESTRAS_MEDIANA - i - 1; j++) {
      if (rawValues[j] > rawValues[j + 1]) {
        int temp = rawValues[j];
        rawValues[j] = rawValues[j + 1];
        rawValues[j + 1] = temp;
      }
    }
  }

  // 3. Devolver el valor central
  return rawValues[NUM_MUESTRAS_MEDIANA / 2];
}

int Lora_timer = 0;

void leerSensores() {
  // En lugar de leer 1 vez, leemos la MEDIANA de varias lecturas
  // y luego aplicamos un promedio de esas medianas para ultra-estabilidad.
  
  long sumV = 0;
  long sumI = 0;
  int MUESTRAS_PROMEDIO = 10; 
  
  for(int i=0; i<MUESTRAS_PROMEDIO; i++) {
    sumV += leerMediana(A5); // Sensor Voltaje
    sumI += leerMediana(A3); // Sensor Corriente
  }
  
  float rawV_limpio = sumV / (float)MUESTRAS_PROMEDIO;
  float rawI_limpio = sumI / (float)MUESTRAS_PROMEDIO;

  // Conversión a Voltaje Real (Divisor de voltaje, ajusta 25.0 si es diferente)
  double voltage = rawV_limpio * (25.0 / 1023.0); 
  
  // Filtro EMA (Suavizado temporal)
  emav = alpha_v * voltage + (1.0 - alpha_v) * emav;

  // Conversión a Corriente
  float voltad = rawI_limpio * (5.0 / 1023.0);
  float diff = abs(voltad - zero_offset_volts);
  float current_raw = diff / sensitivity;

  // Deadband (Banda muerta) para eliminar ruido en cero
  if (current_raw < 0.10) current_raw = 0;

  emac = alpha_c * current_raw + (1.0 - alpha_c) * emac;
}



void loop() {
 

  if (experimentoTerminado) {
    analogWrite(pin, 0); // Apagar PWM al terminar
    return;
  }

  analogWrite(pin, dutyCycle);

  // Dar tiempo al inductor/capacitor para estabilizarse físicamente
  delay(100); 

  // "Purgar" el filtro EMA con el nuevo valor antes de reportar
  for(int i=0; i<30; i++) {
    leerSensores();
  }

  Serial.print(dutyCycle);
  Serial.print(",");
  Serial.print(emav, 3);
  Serial.print(",");
  Serial.println(emac, 3);

  dutyCycle += stepSize;

   if(millis()-Lora_timer > 10000){
      Lora_timer = millis();
      data.voltage = emav * 1000;
      data.current = emac * 1000;
      data.duty = dutyCycle;

      char payload[13]; 
      snprintf(payload, sizeof(payload), "%04X%04X%04X", data.duty, data.voltage, data.current);

      Serial.print("Enviando LoRa: ");
      Serial.println(payload);

      sendRAK("at+PSEND=" + String(payload));
    }
}