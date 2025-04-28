#include <DHT.h>
#include <HardwareSerial.h>

// Definições do DHT22
#define DHTPIN 17             
#define DHTTYPE DHT22         

// Definições de sensores
#define PINO_SENSOR_GAS 18    
#define PINO_SENSOR_CHUVA 15  
#define TEMT6000_PIN 34       
#define ACS712_PIN 35         // Pino para leitura do ACS712

// Definição para PMS3003
#define PMS_TX_PIN 16         

// Threshold de luminosidade
const float LUX_THRESHOLD = 50.0;

// Constantes para o ACS712 de 30A
const float VCC = 3.3;                // Tensão do ESP32
const int ADC_RESOLUTION = 4095;      // Resolução ADC
const float ACS712_SENSIBILIDADE = 0.066; // Sensibilidade em V/A para o modelo 30A (66mV/A)
const float OFFSET = 2.2;             // Novo Offset ajustado para 2,2V

// Definir o limite de corrente máxima
const float LIMITE_CORRENTE = 4000.0;  // Limite de 4A (4000mA)

// Instâncias
DHT dht(DHTPIN, DHTTYPE);
HardwareSerial pmsSerial(1);

// Variáveis globais para partículas
uint16_t pm1_0 = 0, pm2_5 = 0, pm10 = 0;
unsigned long ultimoTempo = 0;

void setup() {
  Serial.begin(9600);
  dht.begin();

  pinMode(PINO_SENSOR_GAS, INPUT);
  pinMode(PINO_SENSOR_CHUVA, INPUT);
  pinMode(TEMT6000_PIN, INPUT);
  pinMode(ACS712_PIN, INPUT);
  analogReadResolution(12);

  // Iniciar serial do PMS3003
  pmsSerial.begin(9600, SERIAL_8N1, PMS_TX_PIN, -1);

  Serial.println("Sistema Iniciado...");
}

void loop() {
  // Leitura contínua do PMS3003
  if (pmsSerial.available() >= 32) {
    if (pmsSerial.read() == 0x42) {
      if (pmsSerial.read() == 0x4D) {
        uint8_t buffer[30];
        pmsSerial.readBytes(buffer, 30);

        pm1_0  = (buffer[2] << 8) | buffer[3];
        pm2_5  = (buffer[4] << 8) | buffer[5];
        pm10   = (buffer[6] << 8) | buffer[7];
      }
    }
  }

  // A cada 2 segundos, exibe todos os dados
  if (millis() - ultimoTempo >= 2000) {
    ultimoTempo = millis();

    // Leitura do DHT22
    float humidade = dht.readHumidity();
    float temperatura = dht.readTemperature();

    if (isnan(humidade) || isnan(temperatura)) {
      Serial.println("Falha na leitura do sensor DHT22!");
    } else {
      Serial.print("HUMIDADE: ");
      Serial.print(humidade);
      Serial.print(" %\tTEMPERATURA: ");
      Serial.print(temperatura);
      Serial.println(" ºC");
    }

    // Leitura do sensor de gás
    bool gasDetectado = digitalRead(PINO_SENSOR_GAS) == LOW;
    Serial.print("Sensor de Gás: ");
    Serial.println(gasDetectado ? "GÁS DETECTADO" : "Sem gás detectado");

    // Leitura do sensor de luminosidade (TEMT6000)
    int analogValue = analogRead(TEMT6000_PIN);
    float voltage = analogValue * (3.3 / 4095.0);
    float lux = voltage * 200.0;

    Serial.print("Luz - ADC: ");
    Serial.print(analogValue);
    Serial.print(" | Tensão: ");
    Serial.print(voltage, 2);
    Serial.print(" V | Lux: ");
    Serial.print(lux, 1);
    Serial.print(" -> ");
    Serial.println(lux < LUX_THRESHOLD ? "Está ESCURO" : "Está CLARO");

    // Leitura do sensor de chuva
    bool estaChovendo = digitalRead(PINO_SENSOR_CHUVA) == LOW;
    Serial.print("Sensor de Chuva: ");
    Serial.println(estaChovendo ? "ESTÁ CHOVENDO" : "SEM CHUVA");

    // Leitura da corrente (ACS712)
    int acs712Value = analogRead(ACS712_PIN);
    float sensorVoltage = (acs712Value * VCC) / ADC_RESOLUTION;  // Converte a leitura em tensão
    float corrente = (sensorVoltage - OFFSET) / ACS712_SENSIBILIDADE;

    Serial.print("Corrente medida pelo ACS712: ");
    Serial.print(corrente * 1000.0, 2); // Converte para mA (miliampères)
    Serial.println(" mA");

    // Avaliação da corrente
    if (corrente * 1000.0 > LIMITE_CORRENTE) {
        Serial.println("ALERTA: Corrente muito alta para este circuito! Consumo acima de 4A.");
    } else if (corrente * 1000.0 > 2500.0) {
        Serial.println("Corrente elevada. Verifique o consumo dos componentes.");
    } else if (corrente * 1000.0 > 1500.0) {
        Serial.println("Corrente razoável para o ESP32. Pode ser que o Wi-Fi ou outros periféricos estejam consumindo mais.");
    } else {
        Serial.println("Corrente dentro do esperado para um circuito de baixo consumo.");
    }

    // Exibir os dados do PMS3003
    Serial.print("PMS3003 -> PM1.0: ");
    Serial.print(pm1_0);
    Serial.print(" µg/m³ | PM2.5: ");
    Serial.print(pm2_5);
    Serial.print(" µg/m³ | PM10: ");
    Serial.print(pm10);
    Serial.println(" µg/m³");

    Serial.println("\n------------------------------\n");
  }
}
