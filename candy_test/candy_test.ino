/*
  お菓子ディスペンサー 動作確認用スケッチ（部品を1つずつ確かめる）

  使い方
    1. このスケッチを書き込み、シリアルモニタを 115200bps で開く
       （何も出ないときは「ツール」→「USB CDC On Boot」を Enabled にして書き込み直す）
    2. 起動すると自動で ブザー → 青LED → RC522 の順に確かめる
    3. そのあとは、次のものを触ると結果が表示される
         ・ICカードをかざす        → カードの番号（UID）
         ・リモコンのボタンを押す  → ボタンのコード
         ・障害物センサーの前に手  → 「反応あり」
    4. シリアルモニタの入力欄に1文字送ると、次のテストをする
         b：ブザー   m：モーター1/4回転（穴1つ分）   r：逆に1/4回転   f：1回転
         s：センサーの状態   c：RC522の確認   h：この説明

  配線は本番（candy_dispenser.ino）と同じ。お菓子は入れずに確かめる。
*/
#include <SPI.h>
#include <MFRC522.h>
#define DECODE_NEC
#include <IRremote.hpp>

const int PIN_SCK = 4, PIN_MISO = 5, PIN_MOSI = 6, PIN_SS = 7, PIN_RST = 10;
const int PIN_IR = 2, PIN_BUZZER = 3, PIN_DROP = 9, PIN_LED = 8;
const int STEPPER_PIN[4] = {0, 1, 20, 21};
const double STEPS_PER_REV = 4075.7728;
const unsigned int STEP_DELAY_US = 1500;

MFRC522 rfid(PIN_SS, PIN_RST);

const uint8_t SEQ[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};
int seqIndex = 0;

void beep(int freq, int ms) { tone(PIN_BUZZER, freq); delay(ms); noTone(PIN_BUZZER); delay(40); }

void rotate(double turns) {
  long steps = lround(turns * STEPS_PER_REV);
  int dir = steps >= 0 ? 1 : -1;
  Serial.printf("モーター：%ldステップ回します（約%.1f秒）\n", labs(steps), labs(steps) * STEP_DELAY_US / 1e6);
  for (long i = 0; i < labs(steps); i++) {
    seqIndex = (seqIndex + dir + 8) % 8;
    for (int k = 0; k < 4; k++) digitalWrite(STEPPER_PIN[k], SEQ[seqIndex][k]);
    delayMicroseconds(STEP_DELAY_US);
  }
  for (int k = 0; k < 4; k++) digitalWrite(STEPPER_PIN[k], LOW);
  Serial.println("モーター：終わり（円盤がちょうど穴1つ分だけ回ったか見てください）");
}

void checkRfid() {
  byte v = rfid.PCD_ReadRegister(MFRC522::VersionReg);
  if (v == 0x91 || v == 0x92 || v == 0x88 || v == 0xB2) Serial.printf("RC522：OK（バージョン 0x%02X）\n", v);
  else Serial.printf("RC522：応答なし（0x%02X）→ SCK/MISO/MOSI/SDA/RST と 3.3V・GND を確認\n", v);
}

void help() {
  Serial.println("\n--- 送る文字 ---");
  Serial.println(" b：ブザー  m：モーター1/4回転  r：逆に1/4回転  f：1回転");
  Serial.println(" s：センサーの状態  c：RC522の確認  h：この説明");
  Serial.println(" カード・リモコン・センサーは触れば自動で表示されます\n");
}

void setup() {
  Serial.begin(115200);
  unsigned long t0 = millis();
  while (!Serial && millis() - t0 < 8000) delay(10);   // シリアルモニタがつながるまで最大8秒待つ
  delay(300);
  Serial.println("\n===== お菓子ディスペンサー 動作確認 =====");

  for (int k = 0; k < 4; k++) { pinMode(STEPPER_PIN[k], OUTPUT); digitalWrite(STEPPER_PIN[k], LOW); }
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_DROP, INPUT_PULLUP);

  Serial.println("ブザー：ド・ミ・ソ が鳴れば OK");
  beep(1047, 150); beep(1319, 150); beep(1568, 250);

  Serial.println("青LED（基板上）：3回点滅すれば OK");
  for (int i = 0; i < 3; i++) { digitalWrite(PIN_LED, LOW); delay(200); digitalWrite(PIN_LED, HIGH); delay(200); }

  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, PIN_SS);
  rfid.PCD_Init();
  checkRfid();

  IrReceiver.begin(PIN_IR, DISABLE_LED_FEEDBACK);
  Serial.println("リモコン：ボタンを押すとコードが出ます");

  Serial.printf("障害物センサー：今は %s（何もない状態なら「反応なし」が正しい）\n",
                digitalRead(PIN_DROP) == LOW ? "反応あり" : "反応なし");
  Serial.println("LEDモジュール：電源が入っている間ずっと光っていれば OK");
  help();
}

void loop() {
  // ICカード
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    Serial.print("カード：");
    for (byte i = 0; i < rfid.uid.size; i++) Serial.printf("%02X ", rfid.uid.uidByte[i]);
    Serial.println(" ← 読めました");
    beep(2000, 60);
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  // リモコン
  if (IrReceiver.decode()) {
    IRData& d = IrReceiver.decodedIRData;
    if (!(d.flags & IRDATA_FLAGS_IS_REPEAT) && d.command != 0)
      Serial.printf("リモコン：コード 0x%02X\n", d.command);
    IrReceiver.resume();
  }

  // 障害物センサー（変わったときだけ表示）
  static int last = -1;
  int now = digitalRead(PIN_DROP);
  if (now != last) {
    if (last != -1) Serial.println(now == LOW ? "センサー：反応あり" : "センサー：反応なし");
    last = now;
  }

  // シリアルから1文字
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'b') { Serial.println("ブザー"); beep(1500, 100); beep(2000, 100); }
    else if (c == 'm') rotate(0.25);
    else if (c == 'r') rotate(-0.25);
    else if (c == 'f') rotate(1.0);
    else if (c == 's') Serial.printf("センサー：%s\n", digitalRead(PIN_DROP) == LOW ? "反応あり" : "反応なし");
    else if (c == 'c') checkRfid();
    else if (c == 'h') help();
  }
}
