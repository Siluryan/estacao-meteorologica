#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>
#include <HTTPClient.h>

// Definições do DHT22
#define DHTPIN 17
#define DHTTYPE DHT22

// Definições de sensores
#define PINO_SENSOR_GAS 18
#define PINO_SENSOR_CHUVA 15
#define TEMT6000_PIN 34
#define ACS712_PIN 35

// Definições para PMS3003
#define PMS_TX_PIN 16

// Definições para GPS NEO-6M
#define GPS_RX 21
#define GPS_TX 22

// Threshold de luminosidade
const float LUX_THRESHOLD = 50.0;

// Constantes para o ACS712 de 30A
const float VCC = 3.3;
const int ADC_RESOLUTION = 4095;
const float ACS712_SENSIBILIDADE = 0.066; // 66mV/A
const float OFFSET = 2.2;
const float LIMITE_CORRENTE = 4000.0;

// Configurações Wi-Fi
const char* WIFI_SSID = "FERNANDA";
const char* WIFI_PASSWORD = "Fernanda2024@";

// Configurações MQTT
const char* MQTT_BROKER = "www.agrostation.online";
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "mqtt_username";
const char* MQTT_PASSWORD = "IaNGEstErysCAMboIdivEreRiMITHIGEogrAHOLInDEFiANtrI";
const char* MQTT_TOPIC = "estacao/meteorologica";

// Instâncias
DHT dht(DHTPIN, DHTTYPE);
HardwareSerial pmsSerial(1); // Para PMS3003
HardwareSerial gpsSerial(2); // Para GPS NEO-6M
TinyGPSPlus gps;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Variáveis globais
uint16_t pm1_0 = 0, pm2_5 = 0, pm10 = 0;
unsigned long ultimoTempo = 0;

void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando ao Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectado! IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Conectando ao broker MQTT...");
    if (mqttClient.connect("ESP32Client", MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("Conectado!");
    } else {
      Serial.print("Falha. Código: ");
      Serial.print(mqttClient.state());
      Serial.println(" Tentando novamente em 5s...");
      delay(5000);
    }
  }
}

String getLocationName(double lat, double lng) {
  HTTPClient http;
  String url = "https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=" + String(lat, 6) + "&lon=" + String(lng, 6);

  http.begin(url);
  http.addHeader("User-Agent", "ESP32-GPS-Client");

  int httpResponseCode = http.GET();
  if (httpResponseCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload);
    http.end();
    if (error) {
      Serial.println("Erro ao decodificar JSON do Nominatim.");
      return "";
    }

    const char* city = doc["address"]["city"] | doc["address"]["town"] | doc["address"]["village"] | "";
    const char* state = doc["address"]["state"] | "";
    const char* country = doc["address"]["country"] | "";

    String result = "";
    if (city[0] != '\0') result += String(city) + ", ";
    if (state[0] != '\0') result += String(state) + ", ";
    if (country[0] != '\0') result += String(country);
    return result;
  } else {
    Serial.print("Erro HTTP: ");
    Serial.println(httpResponseCode);
    http.end();
    return "";
  }
}

void enviarDadosMQTT(float temperatura, float humidade, float lux, bool estaChovendo, bool gasDetectado, float corrente) {
  StaticJsonDocument<256> doc;

  doc["temperatura"] = temperatura;
  doc["umidade"] = humidade;
  doc["luminosidade"] = lux;
  doc["chuva"] = estaChovendo;
  doc["gas_detectado"] = gasDetectado;
  doc["corrente"] = corrente;
  doc["pm1_0"] = pm1_0;
  doc["pm2_5"] = pm2_5;
  doc["pm10"] = pm10;

  char payload[256];
  serializeJson(doc, payload);

  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.publish(MQTT_TOPIC, payload);
  Serial.println("Dados enviados via MQTT: " + String(payload));
}

void setup() {
  Serial.begin(9600);
  dht.begin();

  pinMode(PINO_SENSOR_GAS, INPUT);
  pinMode(PINO_SENSOR_CHUVA, INPUT);
  pinMode(TEMT6000_PIN, INPUT);
  pinMode(ACS712_PIN, INPUT);
  analogReadResolution(12);

  pmsSerial.begin(9600, SERIAL_8N1, PMS_TX_PIN, -1); // PMS3003
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX); // GPS

  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("Sistema Iniciado...");
}

void loop() {
  // Leitura PMS3003
  if (pmsSerial.available() >= 32) {
    if (pmsSerial.read() == 0x42 && pmsSerial.read() == 0x4D) {
      uint8_t buffer[30];
      pmsSerial.readBytes(buffer, 30);
      pm1_0 = (buffer[2] << 8) | buffer[3];
      pm2_5 = (buffer[4] << 8) | buffer[5];
      pm10 = (buffer[6] << 8) | buffer[7];
    }
  }

  // Processamento GPS
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  if (millis() - ultimoTempo >= 5000) {
    ultimoTempo = millis();

    float humidade = dht.readHumidity();
    float temperatura = dht.readTemperature();
    if (isnan(humidade) || isnan(temperatura)) {
      Serial.println("Falha na leitura do sensor DHT22!");
      return;
    }

    bool gasDetectado = digitalRead(PINO_SENSOR_GAS) == LOW;
    int analogValue = analogRead(TEMT6000_PIN);
    float voltage = analogValue * (3.3 / 4095.0);
    float lux = voltage * 200.0;

    bool estaChovendo = digitalRead(PINO_SENSOR_CHUVA) == LOW;

    int acs712Value = analogRead(ACS712_PIN);
    float sensorVoltage = (acs712Value * VCC) / ADC_RESOLUTION;
    float corrente = abs((sensorVoltage - OFFSET) / ACS712_SENSIBILIDADE * 1000.0); // mA

    enviarDadosMQTT(temperatura, humidade, lux, estaChovendo, gasDetectado, corrente);

    Serial.print("HUMIDADE: "); Serial.print(humidade); Serial.print(" %\tTEMPERATURA: "); Serial.println(temperatura);
    Serial.print("Sensor de Gás: "); Serial.println(gasDetectado ? "GÁS DETECTADO" : "Sem gás detectado");
    Serial.print("Luz - ADC: "); Serial.print(analogValue); Serial.print(" | Lux: "); Serial.println(lux);
    Serial.print("Sensor de Chuva: "); Serial.println(estaChovendo ? "ESTÁ CHOVENDO" : "SEM CHUVA");
    Serial.print("Corrente: "); Serial.print(corrente, 2); Serial.println(" mA");
    Serial.print("PMS3003 -> PM1.0: "); Serial.print(pm1_0); Serial.print(" | PM2.5: "); Serial.print(pm2_5); Serial.print(" | PM10: "); Serial.println(pm10);

    // GPS + Localização
    if (gps.location.isValid()) {
      double lat = gps.location.lat();
      double lng = gps.location.lng();

      Serial.print("Latitude: "); Serial.println(lat, 6);
      Serial.print("Longitude: "); Serial.println(lng, 6);
      Serial.print("Altitude: "); Serial.println(gps.altitude.meters());
      Serial.print("Satélites: "); Serial.println(gps.satellites.value());
      Serial.print("Precisão (HDOP): "); Serial.println(gps.hdop.hdop());

      String locationName = getLocationName(lat, lng);
      if (locationName.length() > 0) {
        Serial.print("Localização aproximada: ");
        Serial.println(locationName);
      } else {
        Serial.println("Falha ao obter localização detalhada.");
      }
    } else {
      Serial.println("Localização GPS inválida.");
    }

    Serial.println("\n------------------------------\n");
  }

  mqttClient.loop();
}
