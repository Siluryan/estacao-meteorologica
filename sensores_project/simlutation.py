import time
import json
import random
import paho.mqtt.client as mqtt

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "estacao.meteorologica"

def gerar_dados_sensores():
    return {
        "temperatura": round(random.uniform(15.0, 35.0), 1),
        "umidade": round(random.uniform(30.0, 90.0), 1), 
        "luminosidade": round(random.uniform(990.0, 1035.0), 1),
        "qualidade_ar": round(random.uniform(990.0, 1035.0), 1),
        "chuva": round(random.uniform(0.0, 10.0), 1)
    }

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

try:
    print("Enviando dados simulados para RabbitMQ via MQTT...")
    while True:
        dados = gerar_dados_sensores()
        payload = json.dumps(dados)
        client.publish(MQTT_TOPIC, payload)
        print(f"Enviado: {payload}")
        time.sleep(5)

except KeyboardInterrupt:
    print("\nEncerrando envio de dados.")
    client.disconnect()