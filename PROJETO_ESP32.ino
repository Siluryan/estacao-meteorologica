#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>
#include <HTTPClient.h>

// DHT22
#define DHTPIN 17
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// Sensores diversos
#define PINO_SENSOR_GAS 18
#define PINO_SENSOR_CHUVA 15
#define TEMT6000_PIN 34
#define ACS712_PIN 35

// PMS3003
#define PMS_TX_PIN 16
HardwareSerial pmsSerial(1);

// GPS NEO-6M
#define GPS_RX 21
#define GPS_TX 22
HardwareSerial gpsSerial(2);
TinyGPSPlus gps;

// Config Wi-Fi
const char* WIFI_SSID = "SEU_WIFI";
const char* WIFI_PASSWORD = "SUA_SENHA";

// Config MQTT
const char* MQTT_BROKER = "www.agrostation.online";
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "mqtt_username";
const char* MQTT_PASSWORD = "";
const char* MQTT_TOPIC = "estacao/meteorologica";

// MQTT Client
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// PM variáveis
uint16_t pm1_0 = 0, pm2_5 = 0, pm10 = 0;

// Controle de tempo
unsigned long ultimoTempo = 0;
String localizacaoCache = "";
bool localizacaoObtida = false;

String removeAcentos(const String& input) {
  String output;
  for (unsigned int i = 0; i < input.length(); i++) {
    char c = input[i];
    if ((uint8_t)c < 128) {
      output += c;
    }
  }
  return output;
}

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi conectado. IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Conectando ao MQTT...");
    if (mqttClient.connect("ESP32Client", MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("Conectado!");
    } else {
      Serial.print("Falha. Código: ");
      Serial.print(mqttClient.state());
      Serial.println(" Tentando em 5s...");
      delay(5000);
    }
  }
}

String getLocationName(double lat, double lng) {
  HTTPClient http;
  String url = "https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=" 
               + String(lat, 6) + "&lon=" + String(lng, 6);

  http.begin(url);
  http.addHeader("User-Agent", "ESP32-GPS-Client");

  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<1024> doc;
    DeserializationError error = deserializeJson(doc, payload);
    http.end();
    if (error) {
      Serial.println("Erro no JSON do Nominatim.");
      return "";
    }

    const char* city = doc["address"]["city"]    | doc["address"]["town"] 
                     | doc["address"]["village"] | "";
    const char* state = doc["address"]["state"] | "";
    const char* country = doc["address"]["country"] | "";

    String result = "";
    if (city[0]) result += String(city) + ", ";
    if (state[0]) result += String(state) + ", ";
    if (country[0]) result += String(country);

    return removeAcentos(result);
  } else {
    Serial.printf("Erro HTTP: %d\n", httpCode);
    http.end();
    return "";
  }
}

void enviarDadosMQTT(float temp, float hum, float lux, bool chovendo,
                     bool gas, float corrente, double lat, double lon,
                     const String& localizacao) {
  StaticJsonDocument<512> doc;

  doc["temperatura"]    = temp;
  doc["umidade"]        = hum;
  doc["luminosidade"]   = lux;
  doc["chuva"]          = chovendo;
  doc["gas_detectado"]  = gas;
  doc["corrente"]       = corrente;
  doc["pm1_0"]          = pm1_0;
  doc["pm2_5"]          = pm2_5;
  doc["pm10"]           = pm10;
  doc["latitude"]       = lat;
  doc["longitude"]      = lon;
  doc["localizacao"]    = localizacao;

  char payload[512];
  serializeJson(doc, payload);

  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.publish(MQTT_TOPIC, payload);
  Serial.println("Publicado MQTT: " + String(payload));
}

void setup() {
  Serial.begin(9600);
  dht.begin();

  pinMode(PINO_SENSOR_GAS, INPUT);
  pinMode(PINO_SENSOR_CHUVA, INPUT);
  pinMode(TEMT6000_PIN, INPUT);
  pinMode(ACS712_PIN, INPUT);
  analogReadResolution(12);

  pmsSerial.begin(9600, SERIAL_8N1, PMS_TX_PIN, -1);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("Sistema pronto.");
}

void loop() {
  // PMS3003
  if (pmsSerial.available() >= 32) {
    if (pmsSerial.read() == 0x42 && pmsSerial.read() == 0x4D) {
      uint8_t buffer[30];
      pmsSerial.readBytes(buffer, 30);
      pm1_0 = (buffer[2] << 8) | buffer[3];
      pm2_5 = (buffer[4] << 8) | buffer[5];
      pm10  = (buffer[6] << 8) | buffer[7];
    }
  }

  // GPS
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  if (millis() - ultimoTempo >= 5000 && gps.location.isValid()) {
    ultimoTempo = millis();

    float temperatura = dht.readTemperature();
    float umidade = dht.readHumidity();
    if (isnan(temperatura) || isnan(umidade)) {
      Serial.println("Falha na leitura do DHT22");
      return;
    }

    int analogValue = analogRead(TEMT6000_PIN);
    float lux = analogValue * (3.3 / 4095.0) * 1000;

    bool gas = digitalRead(PINO_SENSOR_GAS) == LOW;
    bool chuva = digitalRead(PINO_SENSOR_CHUVA) == LOW;

    int adcValue = analogRead(ACS712_PIN);
    float voltage = adcValue * (VCC / ADC_RESOLUTION);
    float corrente = (voltage - OFFSET) / ACS712_SENSIBILIDADE;

    double lat = gps.location.lat();
    double lon = gps.location.lng();

    // Só busca localização uma vez
    if (!localizacaoObtida) {
      localizacaoCache = getLocationName(lat, lon);
      if (localizacaoCache.length() > 0) {
        localizacaoObtida = true;
      }
    }

    enviarDadosMQTT(temperatura, umidade, lux, chuva, gas, corrente, lat, lon, localizacaoCache);
  }
}