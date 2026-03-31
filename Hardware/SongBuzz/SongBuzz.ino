#include <WiFi.h>
#include <WiFiUdp.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>
#include <Wire.h>

const char* WIFI_SSID     = "MeinWLAN";
const char* WIFI_PASSWORD = "MeinPasswort";

const int PIN_BTN_L = 5, PIN_BTN_BIG = 2, PIN_BTN_R = 6;
Adafruit_SSD1306 display(128, 64, &Wire, -1);
Adafruit_NeoPixel pixels(8, 3, NEO_GRB + NEO_KHZ800);
WiFiUDP udp;
WebSocketsClient webSocket;
bool connected = false;

// Erweiterte Hilfsfunktion für Text
void drawText(int line, String txt, bool clearFirst, String mode = "", int customSize = 0) {
  display.stopscroll();
  if (clearFirst) display.clearDisplay();
  display.setTextWrap(true);

  display.setTextColor(SSD1306_WHITE);

  if (mode == "fullscreen") {
    display.clearDisplay();
    // Nutze customSize falls gesetzt (>0), sonst Standard 3
    display.setTextSize(customSize > 0 ? customSize : 3);

    int16_t x1, y1;
    uint16_t w, h;
    display.getTextBounds(txt, 0, 0, &x1, &y1, &w, &h);
    // Zentrieren
    display.setCursor((128 - w) / 2, (64 - h) / 2);
    display.print(txt);
  } else {
    // Nutze customSize falls gesetzt, sonst Standard 1
    display.setTextSize(customSize > 0 ? customSize : 1);
    display.setCursor(0, line * 12);
    display.println(txt);

    if (mode == "scroll") {
      display.setTextWrap(false);

      display.display();
      int startPage = 3;
      int endPage = 7;

      display.startscrollleft(startPage, endPage);
      return;
    }
  }
  display.display();
}

void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  if (type == WStype_TEXT) {
    StaticJsonDocument<400> doc;  // Etwas größerer Buffer für mehr Parameter
    deserializeJson(doc, payload);
    String cmd = doc["cmd"];

    if (cmd == "write") {
      // JSON Struktur: {"cmd": "write", "line": 0, "txt": "...", "clear": true, "mode": "...", "size": 2}
      drawText(
        doc["line"] | 0,
        doc["txt"] | "",
        doc["clear"] | false,
        doc["mode"] | "",
        doc["size"] | 0);
    } else if (cmd == "led") {
      pixels.fill(pixels.Color(doc["r"], doc["g"], doc["b"]));
      pixels.show();
    }
  } else if (type == WStype_CONNECTED) {
    connected = true;
    drawText(0, "WS VERBUNDEN", true, "fullscreen");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN_L, INPUT_PULLUP);
  pinMode(PIN_BTN_BIG, INPUT_PULLUP);
  pinMode(PIN_BTN_R, INPUT_PULLUP);

  Wire.begin(9, 8);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("SSD1306 Fehler");
  }

  display.clearDisplay();
  drawText(0, "WLAN SUCHE...", true);

  pixels.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Punkt 1: Sofortige Rückmeldung nach WLAN-Verbindung
  display.clearDisplay();
  drawText(0, "WLAN OK!", false);
  drawText(2, WiFi.localIP().toString(), false);
  drawText(4, "SUCHE SERVER...", false);

  udp.begin(8888);
}

void loop() {
  webSocket.loop();
  if (!connected) {
    int packetSize = udp.parsePacket();
    if (packetSize) {
      char buffer[255];
      int len = udp.read(buffer, 255);
      buffer[len] = 0;
      if (String(buffer).indexOf("SONGBUZZ_SERVER") >= 0) {
        webSocket.begin(udp.remoteIP().toString(), 8000, "/ws/buzzer/" + WiFi.macAddress());
        webSocket.onEvent(webSocketEvent);
      }
    }
  } else {
    static bool l_last = HIGH, b_last = HIGH, r_last = HIGH;
    bool l = digitalRead(PIN_BTN_L), b = digitalRead(PIN_BTN_BIG), r = digitalRead(PIN_BTN_R);
    if (l == LOW && l_last == HIGH) webSocket.sendTXT("{\"type\":\"BTN\", \"val\":\"LEFT\"}");
    if (b == LOW && b_last == HIGH) webSocket.sendTXT("{\"type\":\"BTN\", \"val\":\"BIG\"}");
    if (r == LOW && r_last == HIGH) webSocket.sendTXT("{\"type\":\"BTN\", \"val\":\"RIGHT\"}");
    l_last = l;
    b_last = b;
    r_last = r;
    delay(10);
  }
}