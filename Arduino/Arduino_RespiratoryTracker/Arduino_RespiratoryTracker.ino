
/* Arduino sketch to sample from analog pins at a fixed sample rate.

 @author Jeffrey B. Wang
  
*/

//Set the sampling rate here:
const unsigned long interval = 20; //Sampling Interval, in ms

//Global Variables here
static const uint8_t analog_pins[] = {A0,A1,A2,A3};
unsigned long previousMillis = 0;
char incomingByte;
bool isStreaming;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 115200 bits per second:
  Serial.begin(9600);
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
}

// the loop routine runs over and over again forever:
void loop() {

  //Check the Serial port
  if (Serial.available() > 0) {
    incomingByte = Serial.read();
    processCmd(incomingByte);
  }

  //If sample interval is completed, then sample
  unsigned long currentMillis = millis();
  if (isStreaming && ((unsigned long) (currentMillis - previousMillis) >= interval)) {
    previousMillis = currentMillis;
    String line = "";
    for(int i = 0; i < 4; i++) {
      line += analogRead(analog_pins[i]);
      if (i != 3) {
        line += ",";
      }
    }
    Serial.println(line);
  }
  
}

void processCmd(char input) {
  switch (input) {
    case 'h':
      Serial.println("Hi");
      break;
    case 'y':
      isStreaming = true;
      break;
    case 'n':
      isStreaming = false;
      break;
  }
}
