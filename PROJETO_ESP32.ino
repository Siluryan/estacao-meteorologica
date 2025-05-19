#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>

#define DHTPIN 17
#define DHTTYPE DHT22

#define PINO_SENSOR_GAS 18
#define PINO_SENSOR_CHUVA 15
#define TEMT6000_PIN 34
#define ACS712_PIN 35

#define PMS_TX_PIN 16

#define GPS_RX 21
#define GPS_TX 22

#define LED_PIN 2

const float VCC = 3.3;
const int ADC_RESOLUTION = 4095;
const float ACS712_SENSIBILIDADE = 0.066; // 66mV/A
const float OFFSET = 2.2;

const char* WIFI_SSID = "";
const char* WIFI_PASSWORD = "";

const char* MQTT_BROKER = "www.agrostation.online";
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "";
const char* MQTT_PASSWORD = "";
const char* MQTT_TOPIC = "estacao/meteorologica";

DHT dht(DHTPIN, DHTTYPE);
HardwareSerial pmsSerial(1);
HardwareSerial gpsSerial(2);
TinyGPSPlus gps;
WiFiClient espClient;
PubSubClient mqttClient(espClient);

uint16_t pm1_0 = 0, pm2_5 = 0, pm10 = 0;

unsigned long ultimoTempoEnvio = 0;
unsigned long ultimoTempoLocalizacao = 0;

String ultimaLocalizacao = "";
double ultimaLat = 0;
double ultimaLng = 0;

bool precisaAtualizarLocalizacao = false;

// Remove acentos, mantém ASCII
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

void enviarDadosMQTT(float temperatura, float humidade, float lux, bool estaChovendo,
                     bool gasDetectado, float corrente,
                     double latitude, double longitude, const String& localizacao) {
  StaticJsonDocument<512> doc;

  doc["temperatura"]    = temperatura;
  doc["umidade"]        = humidade;
  doc["luminosidade"]   = lux;
  doc["chuva"]          = estaChovendo;
  doc["gas_detectado"]  = gasDetectado;
  doc["corrente"]       = corrente;
  doc["pm1_0"]          = pm1_0;
  doc["pm2_5"]          = pm2_5;
  doc["pm10"]           = pm10;
  doc["latitude"]       = latitude;
  doc["longitude"]      = longitude;
  doc["localizacao"]    = localizacao;

  char payload[512];
  serializeJson(doc, payload);

  if (!mqttClient.connected()) {
    connectMQTT();
  }
  mqttClient.publish(MQTT_TOPIC, payload);
  Serial.println("Dados enviados via MQTT: " + String(payload));
}

// Nova task para atualizar localização sem travar usando WiFiClient
void taskAtualizaLocalizacao(void * parameter) {
  for (;;) {
    if (precisaAtualizarLocalizacao) {
      precisaAtualizarLocalizacao = false;

      double lat = ultimaLat;
      double lng = ultimaLng;

      if (lat != 0 && lng != 0) {
        Serial.println("🔄 Atualizando localização via HTTP não bloqueante...");

        WiFiClient client;
        const char* host = "nominatim.openstreetmap.org";
        String url = "/reverse?format=jsonv2&lat=" + String(lat, 6) + "&lon=" + String(lng, 6);

        if (!client.connect(host, 80)) {
          Serial.println("❌ Falha ao conectar ao host");
          vTaskDelay(pdMS_TO_TICKS(1000));
          continue;
        }

        client.print(String("GET ") + url + " HTTP/1.1\r\n" +
                     "Host: " + host + "\r\n" +
                     "User-Agent: ESP32-GPS-Client\r\n" +
                     "Connection: close\r\n\r\n");

        unsigned long timeout = millis() + 3000;
        while (client.available() == 0) {
          if (millis() > timeout) {
            Serial.println("❌ Timeout esperando resposta");
            client.stop();
            break;
          }
          vTaskDelay(pdMS_TO_TICKS(10));
        }

        String response = "";
        while (client.available()) {
          response += (char)client.read();
        }
        client.stop();

        if (response.length() > 0) {
          int jsonStart = response.indexOf("\r\n\r\n");
          if (jsonStart >= 0) {
            String jsonStr = response.substring(jsonStart + 4);

            StaticJsonDocument<1024> doc;
            auto error = deserializeJson(doc, jsonStr);
            if (!error) {
              const char* city = doc["address"]["city"] | doc["address"]["town"] | doc["address"]["village"] | "";
              const char* state = doc["address"]["state"] | "";
              const char* country = doc["address"]["country"] | "";

              String result = "";
              if (city[0] != '\0') result += String(city) + ", ";
              if (state[0] != '\0') result += String(state) + ", ";
              if (country[0] != '\0') result += String(country);

              ultimaLocalizacao = removeAcentos(result);
              Serial.println("🌍 Localização atualizada: " + ultimaLocalizacao);
            } else {
              Serial.println("❌ Erro ao decodificar JSON na task (WiFiClient).");
            }
          } else {
            Serial.println("❌ Não encontrou corpo JSON na resposta.");
          }
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void setup() {
  Serial.begin(9600);
  dht.begin();

  pinMode(PINO_SENSOR_GAS, INPUT);
  pinMode(PINO_SENSOR_CHUVA, INPUT);
  pinMode(TEMT6000_PIN, INPUT);
  pinMode(ACS712_PIN, INPUT);
  analogReadResolution(12);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  pmsSerial.begin(9600, SERIAL_8N1, PMS_TX_PIN, -1);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);

  Serial.println("Sistema Iniciado...");

  // Cria a task de localização com 2k de stack e prioridade 1 no core 1
  xTaskCreatePinnedToCore(
    taskAtualizaLocalizacao,
    "TaskLocalizacao",
    4096,
    NULL,
    1,
    NULL,
    1);
}

void loop() {
  if (pmsSerial.available() >= 32) {
    if (pmsSerial.read() == 0x42 && pmsSerial.read() == 0x4D) {
      uint8_t buffer[30];
      pmsSerial.readBytes(buffer, 30);
      pm1_0 = (buffer[2] << 8) | buffer[3];
      pm2_5 = (buffer[4] << 8) | buffer[5];
      pm10  = (buffer[6] << 8) | buffer[7];
    }
  }

  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  unsigned long agora = millis();

  if (gps.location.isValid() && (agora - ultimoTempoLocalizacao > 60000)) {
    double latAtual = gps.location.lat();
    double lngAtual = gps.location.lng();

    if (abs(latAtual - ultimaLat) > 0.0001 || abs(lngAtual - ultimaLng) > 0.0001 || ultimaLocalizacao == "") {
      ultimaLat = latAtual;
      ultimaLng = lngAtual;

      precisaAtualizarLocalizacao = true;  // sinaliza para a task buscar localização

      ultimoTempoLocalizacao = agora;
    }
  }

  if (agora - ultimoTempoEnvio >= 2000) {
    ultimoTempoEnvio = agora;

    float humidade   = dht.readHumidity();
    float temperatura = dht.readTemperature();
    if (isnan(humidade) || isnan(temperatura)) {
      Serial.println("Falha na leitura do sensor DHT22!");
      return;
    }

    bool gasDetectado  = digitalRead(PINO_SENSOR_GAS) == LOW;
    bool estaChovendo  = digitalRead(PINO_SENSOR_CHUVA) == LOW;

    int analogValue    = analogRead(TEMT6000_PIN);
    float voltage      = analogValue * (3.3 / 4095.0);
    float lux          = voltage * 200.0;

    int acs712Value    = analogRead(ACS712_PIN);
    float sensorVoltage= (acs712Value * VCC) / ADC_RESOLUTION;
    float corrente     = abs((sensorVoltage - OFFSET) / ACS712_SENSIBILIDADE * 1000.0);

    enviarDadosMQTT(temperatura, humidade, lux, estaChovendo,
                    gasDetectado, corrente,
                    ultimaLat, ultimaLng, ultimaLocalizacao);

    Serial.printf("H: %.1f%%  T: %.1f°C  LUX: %.1f  Chuva: %s  Gás: %s  Corrente: %.0fmA\n",
                  humidade, temperatura, lux,
                  estaChovendo ? "SIM" : "NÃO",
                  gasDetectado ? "SIM" : "NÃO",
                  corrente);

    if (ultimaLat != 0 && ultimaLng != 0) {
      Serial.printf("GPS: %.6f, %.6f  Local: %s\n\n",
                    ultimaLat, ultimaLng, ultimaLocalizacao.c_str());
    }
  }

  mqttClient.loop();
}
