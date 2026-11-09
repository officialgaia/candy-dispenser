/*
  お菓子ディスペンサー（ESP32-C3 SuperMini）
  ------------------------------------------------------------
  使い方（操作はICカードだけ）
    1. 登録済みのカードをRC522にかざす
       → 「ピピッ」のあと、今日あと何回使えるかを短い音の数で知らせる。この時点で1杯
    2. 増やしたいときは、同じカードを一度離してまたかざす。かざすたびに1杯増える（最大MAX_PORTIONS杯）
       最後にかざしてからTAP_WAIT_MS（2.5秒）たつと出し始める
       1杯＝円盤の穴1つ分（M&Mで約5粒。4〜6粒のばらつきあり）
    3. 円盤が1/4回転するごとに1杯分落ち、終わったらメロディが鳴る
       障害物センサーで1杯ごとに落ちたかを確かめ、空振りした分は追加で回す。
       何回回しても落ちてこなければ「空か詰まり」としてエラー音で止まる
       （1杯も出なかったときは、その回は使用回数に数えない）

  管理カード（カードの登録・削除・詰まり解消用）
    ・カードが1枚も登録されていない状態で最初にかざしたカードが管理カードになる
      （管理カードではお菓子は出ない）
    ・管理カードをかざす → 青LEDが点滅（INPUT_TIMEOUT_MS＝10秒受付）
        → 未登録のカードをかざす：登録 / 登録済みのカードをかざす：削除
        → もう一度管理カードをかざす：詰まり解消（円盤を少し戻して前に送る。お菓子は出ない）
    ・管理カードをなくしたら、RESET_ADMIN を true にして書き込み → 次にかざしたカードが新しい管理カード
      （そのあと false に戻して書き込み直す）

  配線（ESP32-C3 SuperMini）
    RC522    3.3V→3V3  GND→GND  SCK→GPIO4  MISO→GPIO5  MOSI→GPIO6
             SDA(SS)→GPIO7  RST→GPIO10   ※RC522は必ず3.3V
    パッシブブザー  S→150Ω→GPIO3  −→GND
             ※基板にトランジスタが付いている型なら抵抗なしでVCCを3V3へ
    ULN2003  IN1→GPIO0  IN2→GPIO1  IN3→GPIO20  IN4→GPIO21
             ＋→5V  −→GND（28BYJ-48の白コネクタはそのまま差す）
    電解コンデンサ  470µF：ULN2003の＋と−のあいだ（＋側を5Vへ）
                   10µF ：RC522の3.3VとGNDのあいだ（＋側を3.3Vへ）
    障害物検知モジュール  ＋→3V3  GND→GND  OUT→GPIO9  EN→ジャンパーのまま
             ※反応距離は半固定抵抗で3cm程度に。何もないときOUTがHIGHになること
               （GPIO9は起動時にLOWだと書き込みモードになるため、筒が空の状態で電源を入れる）
    スリットのLED（RGB/3色LEDモジュール）  −→GND  光らせる色→220Ω→5V（ESP32のピンは使わない）

  ライブラリ（Arduino IDEのライブラリマネージャで入れる）
    MFRC522（GithubCommunity / miguelbalboa版）
  ボード設定：ESP32C3 Dev Module、USB CDC On Boot = Enabled
*/

#include <WiFi.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Preferences.h>
#include <time.h>

// ===================== 設定 =====================
// Wi-Fiは「1日の回数制限」の日付を取るためだけに使う。なくても他の機能はすべて動く。
// Wi-Fiなし（USE_WIFI=false、またはつながらないとき）は、電源を入れてから24時間ごと、
// または電源を入れ直したときに回数がリセットされる。
const bool  USE_WIFI  = true;
const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASS = "YOUR_PASSWORD";

const int DAILY_LIMIT    = 3;    // カード1枚が1日に使える回数
const int DEFAULT_PORTIONS = 1;  // カードを1回かざしたときの杯数（1杯≈5粒）
const int MAX_PORTIONS     = 6;  // 1回に出せる最大の杯数
const int POCKETS          = 4;  // 円盤の穴の数（穴Φ24・深さ14mm）
const bool REVERSE_DIR   = false;           // 回る向きが逆ならtrue
const unsigned int STEP_DELAY_US = 1500;    // 小さいほど速い。円盤が大きく重いので遅めにして力を出す
const unsigned long INPUT_TIMEOUT_MS = 10000; // 管理カードの受付（登録・削除）がキャンセルされるまでの時間
const unsigned long TAP_WAIT_MS = 2500;       // 最後にカードをかざしてから出し始めるまでの時間（この間にかざすと1杯増える）
const bool RESET_ADMIN = false;               // 管理カードをなくしたときだけtrueにして書き込む

const bool USE_DROP_SENSOR   = true;  // 障害物センサーで数えるか（falseなら回した数で決める）
const int  MAX_EMPTY_IN_ROW  = 4;     // 続けて何回（穴何個分）落ちてこなければ「空か詰まり」とするか（4＝1周）
const int  MAX_EXTRA_TURNS   = 4;     // 空振り分として追加で回す上限（穴の数）
const unsigned long DROP_WAIT_MS   = 400; // 1穴分回したあと、落ちてくるのを待つ時間
const unsigned long DROP_DEBOUNCE_MS = 40; // 反応のばたつきを無視する間隔

// ===================== ピン =====================
const int PIN_SCK = 4, PIN_MISO = 5, PIN_MOSI = 6, PIN_SS = 7, PIN_RST = 10;
const int PIN_BUZZER = 3;
const int PIN_LED    = 8;                    // 基板上の青LED（LOWで点灯）
const int PIN_DROP   = 9;                    // 障害物センサーOUT（検知でLOW）
const int STEPPER_PIN[4] = {0, 1, 20, 21};   // ULN2003 IN1〜IN4

const double STEPS_PER_REV = 4075.7728;      // 28BYJ-48のハーフステップ1回転分

MFRC522 rfid(PIN_SS, PIN_RST);

// 状態（Arduino IDEが関数の宣言を自動で先頭に入れるので、最初の関数より前に書いておく）
enum Mode { IDLE, COUNTING, ADMIN };   // 待機 / 杯数を数えている / 管理カードの受付中
Mode mode = IDLE;
unsigned long modeSince = 0;
String cardKey;   // 受け付け中のカード
int portions = 0; // 出す杯数
void setMode(Mode m);

volatile unsigned int dropCount = 0;
volatile unsigned long lastDropMs = 0;
void IRAM_ATTR onDrop() {
  unsigned long now = millis();
  if (now - lastDropMs >= DROP_DEBOUNCE_MS) { dropCount++; lastDropMs = now; }
}
Preferences prefs;


// ===================== ステッピングモーター =====================
const uint8_t SEQ[8][4] = {
  {1,0,0,0},{1,1,0,0},{0,1,0,0},{0,1,1,0},
  {0,0,1,0},{0,0,1,1},{0,0,0,1},{1,0,0,1}
};
int seqIndex = 0;
long curPos = 0;        // 実際に進んだステップ数
double targetPos = 0;   // 小数を含む目標位置（穴の間隔の端数が積み重ならないように）

void stepOnce(int dir) {
  int d = REVERSE_DIR ? -dir : dir;
  seqIndex = (seqIndex + d + 8) % 8;
  for (int i = 0; i < 4; i++) digitalWrite(STEPPER_PIN[i], SEQ[seqIndex][i]);
  curPos += dir;
  delayMicroseconds(STEP_DELAY_US);
}

void coilsOff() {  // 止まっているあいだは電流を止めて発熱を防ぐ
  for (int i = 0; i < 4; i++) digitalWrite(STEPPER_PIN[i], LOW);
}

void rotatePockets(double pockets) {
  targetPos += pockets * STEPS_PER_REV / POCKETS;
  long t = lround(targetPos);
  while (curPos < t) stepOnce(+1);
  while (curPos > t) stepOnce(-1);
}

// ===================== ブザー =====================
void beep(int freq, int ms) {
  tone(PIN_BUZZER, freq);
  delay(ms);
  noTone(PIN_BUZZER);
  delay(40);
}
void sndKey()        { beep(2000, 40); }
void sndAccept()     { beep(1500, 80); beep(2000, 80); }
void sndError()      { beep(300, 200); beep(300, 200); }
void sndLimit()      { beep(300, 150); beep(300, 150); beep(300, 150); }
void sndCancel()     { beep(800, 150); }
void sndRegistered() { beep(2000, 80); beep(2500, 80); beep(3000, 150); }
void sndRemoved()    { beep(3000, 80); beep(2500, 80); beep(2000, 150); }
void sndReady()      { beep(2000, 60); beep(3000, 60); }
void sndDone()       { beep(1568, 100); beep(2093, 100); beep(2637, 100); beep(3136, 250); }
void sndCount(int n) { for (int i = 0; i < n; i++) { beep(2500, 60); delay(120); } }

// ===================== 日付と使用回数 =====================
uint32_t bootNo = 0;  // 電源を入れた回数（Wi-Fiなしのときの「日」の区切りに使う）

uint32_t today() {  // 例：20261107。時刻が取れないときは「起動番号＋起動からの日数」を日付の代わりにする
  struct tm t;
  if (getLocalTime(&t, 0) && t.tm_year + 1900 >= 2024)
    return (t.tm_year + 1900) * 10000UL + (t.tm_mon + 1) * 100UL + t.tm_mday;
  // 30000000〜38999999：本物の日付（2千万台）とは重ならない
  return 30000000UL + (bootNo % 9000) * 1000UL + (millis() / 86400000UL) % 1000;
}

// 保存形式：日付×100＋その日の回数
int usedToday(const String& key) {
  prefs.begin("usage", true);
  uint32_t v = prefs.getUInt(key.c_str(), 0);
  prefs.end();
  if (v / 100 != today()) return 0;
  return v % 100;
}

void addUse(const String& key) {
  uint32_t d = today();
  int u = usedToday(key) + 1;
  prefs.begin("usage", false);
  prefs.putUInt(key.c_str(), d * 100 + u);
  prefs.end();
}

bool isRegistered(const String& key) {
  prefs.begin("cards", true);
  bool r = prefs.getBool(key.c_str(), false);
  prefs.end();
  return r;
}

String uidKey() {  // 保存用のキー（NVSのキーは15文字までなので最大7バイト）
  String s;
  int n = min((int)rfid.uid.size, 7);
  for (int i = 0; i < n; i++) {
    char b[3];
    sprintf(b, "%02X", rfid.uid.uidByte[i]);
    s += b;
  }
  return s;
}

// ===================== 動作 =====================
void setMode(Mode m) {
  mode = m;
  modeSince = millis();
  if (m == IDLE) { portions = 0; cardKey = ""; }
}

void dispense(int n) {
  Serial.printf("%d杯出します\n", n);
  digitalWrite(PIN_LED, LOW);

  if (!USE_DROP_SENSOR) {               // センサーなし：回した数で決める
    for (int i = 0; i < n; i++) { rotatePockets(1); delay(120); }
    coilsOff();
    addUse(cardKey);
    sndDone();
    setMode(IDLE);
    return;
  }

  // センサーあり：穴1つ分回すごとに「何か落ちたか」を確かめる（5粒前後がまとめて落ちるので粒は数えない）
  noInterrupts(); dropCount = 0; interrupts();
  int turns = 0, emptyInRow = 0, done = 0;
  while (done < n && turns < n + MAX_EXTRA_TURNS) {
    unsigned int before = dropCount;
    rotatePockets(1);
    turns++;
    unsigned long t0 = millis();
    while (millis() - t0 < DROP_WAIT_MS && dropCount == before) delay(5);
    delay(100);                         // 固まりが落ち切るのを待つ
    if (dropCount > before) { done++; emptyInRow = 0; }
    else if (++emptyInRow >= MAX_EMPTY_IN_ROW) break;
  }
  coilsOff();
  Serial.printf("出た杯数: %d / %d（%d回転）\n", done, n, turns);

  if (done > 0) addUse(cardKey);        // 1杯も出なければ使用回数に数えない
  if (done >= n) sndDone();
  else { sndError(); sndCount(done); }  // 足りなかった：エラー音＋出た杯数
  setMode(IDLE);
}

String adminKey() {
  prefs.begin("sys", true);
  String a = prefs.getString("admin", "");
  prefs.end();
  return a;
}

void unjam() {                          // 詰まり解消（差し引きゼロなのでお菓子は出ない）
  rotatePockets(-0.3);
  rotatePockets(+0.3);
  coilsOff();
}

void handleCard(const String& key) {
  Serial.printf("カード: %s\n", key.c_str());
  String admin = adminKey();

  // 管理カードがまだない：最初にかざしたカードを管理カードにする
  if (admin.length() == 0) {
    prefs.begin("sys", false); prefs.putString("admin", key); prefs.end();
    Serial.println("管理カードを登録しました");
    sndRegistered(); setMode(IDLE); return;
  }

  if (key == admin) {
    if (mode == ADMIN) { sndKey(); unjam(); setMode(IDLE); }      // 2回目：詰まり解消
    else if (mode == COUNTING) { sndError(); }                      // 杯数の受付中は無視
    else { setMode(ADMIN); sndKey(); }                              // 1回目：登録・削除の受付
    return;
  }

  if (mode == ADMIN) {
    if (isRegistered(key)) {
      prefs.begin("cards", false); prefs.remove(key.c_str()); prefs.end();
      prefs.begin("usage", false); prefs.remove(key.c_str()); prefs.end();
      sndRemoved();
    } else {
      prefs.begin("cards", false); prefs.putBool(key.c_str(), true); prefs.end();
      sndRegistered();
    }
    setMode(IDLE); return;
  }

  if (mode == COUNTING) {               // 杯数の受付中に同じカード：1杯増やす
    if (key != cardKey) { sndError(); return; }
    if (portions >= MAX_PORTIONS) { sndError(); }
    else { portions++; sndKey(); }
    modeSince = millis();
    return;
  }

  if (!isRegistered(key)) { sndError(); return; }

  int left = DAILY_LIMIT - usedToday(key);
  if (left <= 0) { sndLimit(); setMode(IDLE); return; }

  setMode(COUNTING);
  cardKey = key;
  portions = DEFAULT_PORTIONS;
  sndAccept();
  delay(150);
  sndCount(left);   // 今日あと何回使えるか
  modeSince = millis();
}

void updateLed() {
  bool on = false;
  if (mode == COUNTING) on = true;
  else if (mode == ADMIN) on = (millis() / 200) % 2;
  digitalWrite(PIN_LED, on ? LOW : HIGH);
}

// ===================== setup / loop =====================
void setup() {
  Serial.begin(115200);

  for (int i = 0; i < 4; i++) { pinMode(STEPPER_PIN[i], OUTPUT); digitalWrite(STEPPER_PIN[i], LOW); }
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, HIGH);

  SPI.begin(PIN_SCK, PIN_MISO, PIN_MOSI, PIN_SS);
  rfid.PCD_Init();
  pinMode(PIN_DROP, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_DROP), onDrop, FALLING);

  // 保存領域を最初に作っておく
  prefs.begin("cards", false); prefs.end();
  prefs.begin("usage", false); prefs.end();
  prefs.begin("sys", false);
  bootNo = prefs.getUInt("boot", 0) + 1; prefs.putUInt("boot", bootNo);
  if (RESET_ADMIN) { prefs.remove("admin"); Serial.println("管理カードを消しました。次にかざしたカードが管理カードになります"); }
  prefs.end();

  // Wi-Fiは日付を取るためだけ。つながらなくても動く（その間は起動から24時間ごとに回数リセット）
  if (USE_WIFI) {
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    WiFi.setTxPower(WIFI_POWER_8_5dBm);  // SuperMiniはこれでつながりやすくなる個体が多い
    configTzTime("JST-9", "ntp.nict.jp", "pool.ntp.org");
    unsigned long t0 = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - t0 < 15000) delay(200);
    Serial.println(WiFi.status() == WL_CONNECTED ? "Wi-Fi接続OK" : "Wi-Fiにつながりません（後で自動再接続）");
  } else {
    WiFi.mode(WIFI_OFF);
    Serial.println("Wi-Fiなしで動作（回数は起動から24時間ごと、または電源の入れ直しでリセット）");
  }

  sndReady();
}

void loop() {
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String key = uidKey();
    rfid.PICC_HaltA();       // かざしっぱなしで連続反応しないように
    rfid.PCD_StopCrypto1();
    handleCard(key);
  }

  if (mode == COUNTING && millis() - modeSince > TAP_WAIT_MS) dispense(portions);
  if (mode == ADMIN && millis() - modeSince > INPUT_TIMEOUT_MS) { sndCancel(); setMode(IDLE); }

  updateLed();
}
