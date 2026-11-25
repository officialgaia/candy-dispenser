/*
  モーターだけを動かすテスト（28BYJ-48 ＋ ULN2003）

  書き込みが終わって起動したら、すぐに同じ向きへずっと回り続ける（止まらない）
  1回転は約6秒。シリアルモニタは使わない

  ・回っている間、基板の青LEDがつく（1回転ごとに一瞬消える）
  ・ULN2003の4つの赤いLED（A〜D）が順番に光れば、ESP32からの信号は届いている
  ・配線：GPIO0→IN1、GPIO1→IN2、GPIO20→IN3、GPIO21→IN4、ULN2003の＋→5V、−→GND
*/

const int STEPPER_PIN[4] = {0, 1, 20, 21};
const int PIN_LED = 8;                       // 基板上の青LED（LOWで点灯）
const double STEPS_PER_REV = 4075.7728;      // ハーフステップで1回転
const unsigned int STEP_DELAY_US = 1500;     // 小さいほど速い（1200より小さいと止まりやすい）

const uint8_t SEQ[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};
int seqIndex = 0;

void rotate(double turns) {
  long steps = lround(turns * STEPS_PER_REV);
  int dir = steps >= 0 ? 1 : -1;
  digitalWrite(PIN_LED, LOW);
  for (long i = 0; i < labs(steps); i++) {
    seqIndex = (seqIndex + dir + 8) % 8;
    for (int k = 0; k < 4; k++) digitalWrite(STEPPER_PIN[k], SEQ[seqIndex][k]);
    delayMicroseconds(STEP_DELAY_US);
  }
  for (int k = 0; k < 4; k++) digitalWrite(STEPPER_PIN[k], LOW);   // 止まったら電流を切る
  digitalWrite(PIN_LED, HIGH);
}

void setup() {
  for (int k = 0; k < 4; k++) { pinMode(STEPPER_PIN[k], OUTPUT); digitalWrite(STEPPER_PIN[k], LOW); }
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH);
}

void loop() {
  rotate(1.0);   // 1回転。loopなのでずっと回り続ける
}
