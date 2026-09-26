// ========================================
// 2-DIRECTION TRAFFIC LIGHT SYSTEM
// Arduino Mega 2560
// ========================================

// IR SENSORS
const int IR1 = 2;
const int IR2 = 3;

// TRAFFIC LIGHT 1
const int GREEN1  = 8;
const int YELLOW1 = 9;
const int RED1    = 10;

// TRAFFIC LIGHT 2
const int GREEN2  = 11;
const int YELLOW2 = 12;
const int RED2    = 13;


// Previous obstacle states
bool previous1 = false;
bool previous2 = false;


// Yellow states
bool yellow1 = false;
bool yellow2 = false;


// Yellow timers
unsigned long yellowStart1 = 0;
unsigned long yellowStart2 = 0;


void setup() {

  // IR sensors
  pinMode(IR1, INPUT);
  pinMode(IR2, INPUT);

  // Traffic light 1
  pinMode(GREEN1, OUTPUT);
  pinMode(YELLOW1, OUTPUT);
  pinMode(RED1, OUTPUT);

  // Traffic light 2
  pinMode(GREEN2, OUTPUT);
  pinMode(YELLOW2, OUTPUT);
  pinMode(RED2, OUTPUT);


  // Start both at RED

  digitalWrite(GREEN1, LOW);
  digitalWrite(YELLOW1, LOW);
  digitalWrite(RED1, HIGH);

  digitalWrite(GREEN2, LOW);
  digitalWrite(YELLOW2, LOW);
  digitalWrite(RED2, HIGH);
}


void loop() {

  // LOW = obstacle detected
  bool obstacle1 = (digitalRead(IR1) == LOW);
  bool obstacle2 = (digitalRead(IR2) == LOW);


  // ========================================
  // TRAFFIC LIGHT 1
  // ========================================

  if (obstacle1) {

    yellow1 = false;

    digitalWrite(GREEN1, HIGH);
    digitalWrite(YELLOW1, LOW);
    digitalWrite(RED1, LOW);

  }

  else if (previous1 && !yellow1) {

    yellow1 = true;
    yellowStart1 = millis();

    digitalWrite(GREEN1, LOW);
    digitalWrite(YELLOW1, HIGH);
    digitalWrite(RED1, LOW);
  }

  if (yellow1 && millis() - yellowStart1 >= 1000) {

    yellow1 = false;

    digitalWrite(YELLOW1, LOW);
    digitalWrite(RED1, HIGH);
  }


  // ========================================
  // TRAFFIC LIGHT 2
  // ========================================

  if (obstacle2) {

    yellow2 = false;

    digitalWrite(GREEN2, HIGH);
    digitalWrite(YELLOW2, LOW);
    digitalWrite(RED2, LOW);

  }

  else if (previous2 && !yellow2) {

    yellow2 = true;
    yellowStart2 = millis();

    digitalWrite(GREEN2, LOW);
    digitalWrite(YELLOW2, HIGH);
    digitalWrite(RED2, LOW);
  }

  if (yellow2 && millis() - yellowStart2 >= 1000) {

    yellow2 = false;

    digitalWrite(YELLOW2, LOW);
    digitalWrite(RED2, HIGH);
  }


  // Save sensor states
  previous1 = obstacle1;
  previous2 = obstacle2;
}