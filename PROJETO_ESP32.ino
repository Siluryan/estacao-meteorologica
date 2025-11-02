#include <WiFi.h>
#define MQTT_MAX_PACKET_SIZE 2048
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HardwareSerial.h>
#include <TinyGPSPlus.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>

// ---------------- Pinos ----------------
#define DHTPIN 17
#define DHTTYPE DHT22

#define PINO_SENSOR_GAS 18
#define PINO_SENSOR_CHUVA 15
#define TEMT6000_PIN 34
#define ACS712_PIN 35
#define SENSOR_SOLO_PIN 33
#define PMS_TX_PIN 16
#define GPS_RX 21
#define GPS_TX 22
#define LED_PIN 2
#define ANEMOMETRO_PIN 27  // reed switch

// ---------------- Constantes ----------------
const float VCC = 3.3;
const int ADC_RESOLUTION = 4095;
const float ACS712_SENSIBILIDADE = 0.066; // 66 mV/A
const float OFFSET = 2.2; // tensão offset do sensor (ajustar se necessário)
const float FATOR_VENTO = 2.4; // cada pulso ≈ 2.4 km/h (ajuste experimental)

const char* WIFI_SSID = "";
const char* WIFI_PASSWORD = "";

const char* MQTT_BROKER = "";
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "";
const char* MQTT_PASSWORD = "";
const char* MQTT_TOPIC = "estacao/meteorologica";

// ---------------- Objetos / Variáveis ----------------
volatile unsigned long contagemPulsos = 0;
unsigned long ultimoTempoVento = 0;

DHT dht(DHTPIN, DHTTYPE);
HardwareSerial pmsSerial(1);   // UART1 para sensor PMS
HardwareSerial gpsSerial(2);   // UART2 para GPS
TinyGPSPlus gps;
Adafruit_BMP280 bmp;

uint16_t pm1_0 = 0, pm2_5 = 0, pm10 = 0;
unsigned long ultimoTempoLeitura = 0;
double ultimaLat = 0;
double ultimaLng = 0;
String ultimaLocalizacao = "";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long ultimoTempoEnvio = 0;
unsigned long ultimoTempoLocalizacao = 0;
bool precisaAtualizarLocalizacao = false;

// ---------------- Prototipos ----------------
void connectWiFi();
void connectMQTT();
void enviarDadosMQTT(float temperatura, float humidade, float lux, bool estaChovendo,
                     bool gasDetectado, float corrente,
                     double latitude, double longitude, const String& localizacao,
                     float vento_kmh, float vento_ms, float umidadeSolo,
                     float pressao_hpa, float altitude_m, float tempBMP);

// ---------------- Funções auxiliares ----------------
// Remove caracteres não ASCII (remove acentos simples)
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

// ---------------- Interrupção do anemômetro ----------------
void IRAM_ATTR contarPulso() {
  contagemPulsos++;
}

// ---------------- Task: reverse geocoding não-bloqueante ----------------
void taskAtualizaLocalizacao(void * parameter) {
  (void) parameter;
  for (;;) {
    if (precisaAtualizarLocalizacao) {
      precisaAtualizarLocalizacao = false;

      double lat = ultimaLat;
      double lng = ultimaLng;

      if (lat != 0 && lng != 0) {
        Serial.println("Atualizando localização via HTTP não bloqueante...");

        WiFiClient client;
        const char* host = "nominatim.openstreetmap.org";
        String url = "/reverse?format=jsonv2&lat=" + String(lat, 6) + "&lon=" + String(lng, 6);

        if (!client.connect(host, 80)) {
          Serial.println("Falha ao conectar ao host de reverse geocoding");
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
            Serial.println("Timeout esperando resposta do host");
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
              Serial.println("Localização atualizada: " + ultimaLocalizacao);
            } else {
              Serial.println("Erro ao decodificar JSON na task de localização.");
            }
          } else {
            Serial.println("Não encontrou corpo JSON na resposta de reverse geocoding.");
          }
        }
      }
    }
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

// ---------------- Conexões Wi-Fi / MQTT ----------------
void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando ao Wi-Fi");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    // opcional: evitar ficar num loop infinito travando a task principal
    if (millis() - start > 15000) {
      Serial.println("\nAinda tentando conectar ao Wi-Fi...");
      start = millis();
    }
  }
  Serial.println("\nConectado! IP: " + WiFi.localIP().toString());
}

void connectMQTT() {
  if (mqttClient.connected()) {
    mqttClient.loop();
    return;
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi desconectado. Reconectando...");
    connectWiFi();
    return;
  }

  String clientId = "ESP32Client-";
  clientId += WiFi.macAddress();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setKeepAlive(60);
  
  unsigned long start = millis();
  int tentativas = 0;
  const int MAX_TENTATIVAS = 3;
  
  while (!mqttClient.connected() && tentativas < MAX_TENTATIVAS) {
    Serial.print("Conectando ao broker MQTT ");
    Serial.print(MQTT_BROKER);
    Serial.print(":");
    Serial.print(MQTT_PORT);
    Serial.print(" (tentativa ");
    Serial.print(tentativas + 1);
    Serial.print("/");
    Serial.print(MAX_TENTATIVAS);
    Serial.println(")...");
    
    if (mqttClient.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD)) {
      Serial.println("Conectado ao MQTT!");
      Serial.print("ClientID: ");
      Serial.println(clientId);
      return;
    } else {
      tentativas++;
      Serial.print("Falha na conexão. Código: ");
      Serial.println(mqttClient.state());
      
      switch(mqttClient.state()) {
        case -4: Serial.println("Erro: Timeout de conexão"); break;
        case -3: Serial.println("Erro: Conexão perdida"); break;
        case -2: Serial.println("Erro: Falha ao conectar"); break;
        case -1: Serial.println("Erro: Cliente desconectado"); break;
        case 1: Serial.println("Erro: Versão de protocolo inválida"); break;
        case 2: Serial.println("Erro: Client ID rejeitado"); break;
        case 3: Serial.println("Erro: Servidor indisponível"); break;
        case 4: Serial.println("Erro: Credenciais inválidas"); break;
        case 5: Serial.println("Erro: Não autorizado"); break;
        default: Serial.print("Erro desconhecido: "); Serial.println(mqttClient.state()); break;
      }
      
      if (tentativas < MAX_TENTATIVAS) {
        Serial.println("Tentando novamente em 5s...");
        delay(5000);
      }
      
      if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi desconectado durante tentativa. Reconectando...");
        connectWiFi();
      }
    }
    
    if (millis() - start > 60000) {
      Serial.println("Timeout: mais de 60s tentando conectar");
      start = millis();
    }
  }
  
  if (tentativas >= MAX_TENTATIVAS) {
    Serial.println("Falha ao conectar após várias tentativas. Tente novamente no próximo ciclo.");
  }
}

// ---------------- Envio MQTT ----------------
void enviarDadosMQTT(float temperatura, float humidade, float lux, bool estaChovendo,
                     bool gasDetectado, float corrente,
                     double latitude, double longitude, const String& localizacao,
                     float vento_kmh, float vento_ms, float umidadeSolo,
                     float pressao_hpa, float altitude_m, float tempBMP) {
  StaticJsonDocument<2048> doc;

  doc["temperatura"]       = temperatura;
  doc["umidade"]           = humidade;
  doc["luminosidade"]      = lux;
  doc["chuva"]             = estaChovendo;
  doc["gas_detectado"]     = gasDetectado;
  doc["corrente"]          = corrente;
  doc["pm1_0"]             = pm1_0;
  doc["pm2_5"]             = pm2_5;
  doc["pm10"]              = pm10;
  doc["latitude"]          = latitude;
  doc["longitude"]         = longitude;
  doc["localizacao"]       = localizacao;
  doc["vento_kmh"]         = vento_kmh;
  doc["vento_ms"]          = vento_ms;
  doc["umidade_solo_pct"]  = umidadeSolo;
  doc["pressao_hpa"]       = pressao_hpa;
  doc["altitude_m"]        = altitude_m;
  doc["temperatura_bmp"]   = tempBMP;

  char payload[2048];
  size_t len = serializeJson(doc, payload, sizeof(payload));
  
  if (len >= sizeof(payload) - 1) {
    Serial.println("ERRO: Payload muito grande! Reduzindo tamanho...");
    len = sizeof(payload) - 1;
  }
  payload[len] = '\0';

  if (!mqttClient.connected()) {
    connectMQTT();
  }
  
  if (!mqttClient.connected()) {
    Serial.println("ERRO: Não conectado ao MQTT. Tentando reconectar...");
    connectMQTT();
    return;
  }
  
  mqttClient.loop();
  
  bool ok = mqttClient.publish(MQTT_TOPIC, payload, false);
  
  if (ok) {
    Serial.println("Dados publicados via MQTT:");
    Serial.println(payload);
  } else {
    Serial.print("Falha ao publicar no MQTT. Estado: ");
    Serial.println(mqttClient.state());
    Serial.println(payload);
  }
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(9600);
  dht.begin();

  // pinos
  pinMode(PINO_SENSOR_GAS, INPUT);
  pinMode(PINO_SENSOR_CHUVA, INPUT);
  pinMode(TEMT6000_PIN, INPUT);
  pinMode(ACS712_PIN, INPUT);
  pinMode(SENSOR_SOLO_PIN, INPUT);
  analogReadResolution(12);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);

  // anemômetro
  pinMode(ANEMOMETRO_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(ANEMOMETRO_PIN), contarPulso, FALLING);

  // Seriais
  pmsSerial.begin(9600, SERIAL_8N1, PMS_TX_PIN, -1);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  // I2C para BMP280 (escolhi pinos SDA=19, SCL=23 conforme seu código)
  Wire.begin(19, 23);
  if (!bmp.begin(0x76)) {
    Serial.println("Erro ao inicializar BMP280! Verifique conexões e endereço (0x76 ou 0x77).");
  } else {
    Serial.println("BMP280 inicializado com sucesso!");
  }

  // WiFi + MQTT
  connectWiFi();
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setBufferSize(MQTT_MAX_PACKET_SIZE);

  // Cria a task de localização (FreeRTOS) no core 1
  xTaskCreatePinnedToCore(
    taskAtualizaLocalizacao,
    "TaskLocalizacao",
    4096,
    NULL,
    1,
    NULL,
    1);

  Serial.println("Sistema iniciado. Monitorando sensores...");
  ultimoTempoVento = millis();
}

// ---------------- Loop principal ----------------
void loop() {
  // --- Leitura do sensor de partículas (PMS) ---
  if (pmsSerial.available() >= 32) {
    if (pmsSerial.read() == 0x42 && pmsSerial.read() == 0x4D) {
      uint8_t buffer[30];
      pmsSerial.readBytes(buffer, 30);
      pm1_0 = (buffer[2] << 8) | buffer[3];
      pm2_5 = (buffer[4] << 8) | buffer[5];
      pm10  = (buffer[6] << 8) | buffer[7];
    }
  }

  // --- GPS (decodifica contínua) ---
  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  unsigned long agora = millis();

  // Atualiza localização reversa a cada 60s se tiver GPS válido e mudança relevante
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

  // Loop de leitura/ envio a cada 2000 ms
  if (agora - ultimoTempoEnvio >= 2000) {
    ultimoTempoEnvio = agora;

    // --- DHT22 ---
    float humidade = dht.readHumidity();
    float temperatura = dht.readTemperature();
    if (isnan(humidade) || isnan(temperatura)) {
      Serial.println("Falha na leitura do DHT22! Pulando envio deste ciclo.");
      // não retorna completamente; apenas pula envio deste ciclo
      // continuar para manter mqttClient.loop() e leitura de outros sensores
    }

    // --- Sensores digitais ---
    bool gasDetectado = digitalRead(PINO_SENSOR_GAS) == LOW;
    bool estaChovendo = digitalRead(PINO_SENSOR_CHUVA) == LOW;

    // --- Luminosidade (TEMT6000) ---
    int analogValue = analogRead(TEMT6000_PIN);
    float voltage = analogValue * (3.3 / 4095.0);
    float lux = voltage * 200.0;

    // --- Corrente (ACS712) ---
    int acs712Value = analogRead(ACS712_PIN);
    float sensorVoltage = (acs712Value * VCC) / ADC_RESOLUTION;
    float corrente = abs((sensorVoltage - OFFSET) / ACS712_SENSIBILIDADE * 1000.0); // mA

    // --- BMP280 ---
    float pressao = bmp.readPressure() / 100.0F; // hPa
    float altitude = bmp.readAltitude(1013.25); // m
    float tempBMP = bmp.readTemperature();

    // --- Umidade do solo ---
    int valorSolo = analogRead(SENSOR_SOLO_PIN); // 0..4095
    // converte para % (assumindo 4095 = seco, 0 = molhado) - ajuste conforme sensor
    float umidadeSolo = (1.0 - ((float)valorSolo / (float)ADC_RESOLUTION)) * 100.0;
    if (umidadeSolo < 0) umidadeSolo = 0;
    if (umidadeSolo > 100) umidadeSolo = 100;

    // --- GPS: atualiza última posição válida ---
    if (gps.location.isValid()) {
      ultimaLat = gps.location.lat();
      ultimaLng = gps.location.lng();
    }

    // --- Velocidade do vento (anemômetro) ---
    noInterrupts();
    unsigned long pulsos = contagemPulsos;
    contagemPulsos = 0;
    interrupts();

    unsigned long intervaloMs = agora - ultimoTempoVento;
    ultimoTempoVento = agora;

    float velocidadeVento_kmh = 0.0;
    if (intervaloMs > 0 && pulsos > 0) {
      // pulsos por intervalo -> velocidade (km/h)
      velocidadeVento_kmh = ( (float)pulsos * FATOR_VENTO ) / ( (float)intervaloMs / 1000.0 );
    }
    float velocidadeVento_ms = velocidadeVento_kmh / 3.6;

    // --- Filtro simples para evitar picos falsos ---
    static float ventoAnterior = 0;
    if (velocidadeVento_kmh > ventoAnterior * 1.5 && velocidadeVento_kmh > 20) {
      velocidadeVento_kmh = ventoAnterior;
    }
    ventoAnterior = velocidadeVento_kmh;

    // --- Envia por MQTT (certificando conexão) ---
    if (!isnan(temperatura) && !isnan(humidade)) {
      // garante conexão MQTT
      if (!mqttClient.connected()) {
        connectMQTT();
      }
      enviarDadosMQTT(temperatura, humidade, lux, estaChovendo,
                      gasDetectado, corrente,
                      ultimaLat, ultimaLng, ultimaLocalizacao,
                      velocidadeVento_kmh, velocidadeVento_ms,
                      umidadeSolo, pressao, altitude, tempBMP);
    } else {
      Serial.println("Leituras essenciais inválidas, envio MQTT pulado.");
    }

    // --- Exibe tudo no serial ---
    Serial.println("------------------------------------------------");
    if (!isnan(temperatura)) Serial.printf("Temperatura (DHT22): %.2f °C\n", temperatura);
    else Serial.println("Temperatura (DHT22): N/A");

    if (!isnan(humidade)) Serial.printf("Umidade: %.2f %%\n", humidade);
    else Serial.println("Umidade: N/A");

    Serial.printf("Luminosidade: %.2f LUX\n", lux);
    Serial.printf("Umidade do Solo: %.2f %%\n", umidadeSolo);
    Serial.printf("Chuva: %s\n", estaChovendo ? "SIM" : "NÃO");
    Serial.printf("Gás detectado: %s\n", gasDetectado ? "SIM" : "NÃO");
    Serial.printf("Corrente: %.0f mA\n", corrente);
    Serial.printf("PM1.0: %u µg/m³ | PM2.5: %u µg/m³ | PM10: %u µg/m³\n", pm1_0, pm2_5, pm10);
    Serial.printf("BMP280 - Temperatura: %.2f °C | Pressão: %.2f hPa | Altitude: %.2f m\n", tempBMP, pressao, altitude);
    Serial.printf("Velocidade do vento: %.2f km/h (%.2f m/s)\n", velocidadeVento_kmh, velocidadeVento_ms);

    if (ultimaLat != 0 && ultimaLng != 0) {
      Serial.printf("GPS: %.6f, %.6f  Local: %s\n", ultimaLat, ultimaLng, ultimaLocalizacao.c_str());
    } else {
      Serial.println("GPS: aguardando sinal...");
    }
    Serial.println("------------------------------------------------\n");
  }

  // Mantém client MQTT responsivo
  if (mqttClient.connected()) {
    mqttClient.loop();
  } else {
    // tenta reconectar de forma não bloqueante
    connectMQTT();
  }
}
