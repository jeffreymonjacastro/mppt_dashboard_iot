#include <ESP32Servo.h>
#include <Stepper.h>


Servo servo;  //creamos un objeto servo

int servoPos=0;
const int threshold = 50;
int servoInitialPosition = 0;


#define LIGHT_SENSOR_UP_PIN 33
#define LIGHT_SENSOR_DOWN_PIN 35

#define LIGHT_SENSOR_EAST_PIN 27
#define LIGHT_SENSOR_SOUTH_PIN 32
#define LIGHT_SENSOR_WEST_PIN 25
#define LIGHT_SENSOR_NORTH_PIN 14

#define IN1 23
#define IN2 22
#define IN3 21
#define IN4 19

const int STEPS_PER_REVOLUTION = 2048;
Stepper horizontalStepper(STEPS_PER_REVOLUTION, IN1, IN3, IN2, IN4);

long currentStepperSteps = 0;
const long MAX_STEPS = STEPS_PER_REVOLUTION;


const long LDR_MAX = 4095;


void setup(){
  servo.attach(26);
  Serial.begin(9600); // iniciamos el puerto serial
  servo.write(0);
  currentStepperSteps = 0;

  horizontalStepper.setSpeed(10);
}



void loop() {

  int ldrUp = analogRead(LIGHT_SENSOR_UP_PIN);
  int ldrDown = analogRead(LIGHT_SENSOR_DOWN_PIN);

  int diffVertical = ldrUp - ldrDown;

 // Only move if difference is significant
  if (abs(diffVertical) > threshold) {
    if (diffVertical > 0) {
      // Go Up
      servoPos -= 5;
    } else {
      // Go down
      servoPos += 5;
    }

  	servoPos = constrain(servoPos, 0, 40);
    servo.write(servoPos);

    Serial.print("Moving to: ");
    Serial.println(servoPos);
  } else {
    Serial.print("Balanced - No movement. diff: ");
    Serial.println(diffVertical);
  }


  // Read all LDRs
  int north = analogRead(LIGHT_SENSOR_NORTH_PIN);
  int south = analogRead(LIGHT_SENSOR_SOUTH_PIN);
  int east  = analogRead(LIGHT_SENSOR_EAST_PIN);
  int west  = analogRead(LIGHT_SENSOR_WEST_PIN);

  // Find the sensor with the highest reading
  int minLight = north;
  String direction = "North";

  if (east < minLight) {
    minLight = east;
    direction = "East";
  }
  if (west < minLight) {
    minLight = west;
    direction = "West";
  }
  if (south < minLight) {
    minLight = south;
    direction = "South";
  }

  // Only move if North is NOT the brightest, or difference > threshold
  int diffHorizontal = north - minLight;


  if (diffHorizontal > threshold) {
    int steps = map(diffHorizontal, threshold, LDR_MAX, 1, STEPS_PER_REVOLUTION);
    steps = constrain(steps, 1,  STEPS_PER_REVOLUTION);
    //Serial.println(steps);
    if (direction == "East" || direction == "South") {
      // East is brightest → rotate **anticlockwise** to bring North toward light
      if (currentStepperSteps + steps <= MAX_STEPS) {
        horizontalStepper.step(+steps);
        currentStepperSteps += steps;
        //Serial.println("Rotating Anticlockwise (East → North)");
      }
    } else if (direction == "West" || direction == "South") {
      // West or South brightest → rotate **clockwise** to bring North toward light
      if (currentStepperSteps + steps >= -MAX_STEPS) {
        horizontalStepper.step(-steps);
        currentStepperSteps -= steps;
        //Serial.println("Rotating Clockwise (West/South → North)");
      }
    }
  } else {
    //Serial.println("North is dominant - No rotation needed");
  }

  Serial.print("Up:");
  Serial.print(ldrUp);
  Serial.print(" Down:");
  Serial.print(ldrDown);
  // Serial.println();
  //Serial.print(" N:");
  //Serial.print(north);
  //Serial.print(" E:");
  //Serial.print(east);
  //Serial.print(" W:");
  //Serial.print(west);
  //Serial.print(" S:");
  //Serial.print(south);
  //Serial.print(" | Max:");
  //Serial.print(minLight);
  //Serial.print(" (");
  //Serial.print(direction);
  //Serial.print(") | Stepper:");
  //Serial.print(currentStepperSteps);
  //Serial.print(" | Servo:");
  //Serial.print(servoPos);
  Serial.println();

  int wait = 1000;
  delay(wait);
}
