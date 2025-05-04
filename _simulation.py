import os
import time
import json
import random
import paho.mqtt.client as mqtt
import logging
import socket
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mqtt_simulator')

def is_rabbitmq_available():
    try:
        socket.gethostbyname("rabbitmq")
        return True
    except socket.gaierror:
        return False

MQTT_BROKER = os.environ.get("MQTT_BROKER", "rabbitmq")
if MQTT_BROKER == "rabbitmq" and not is_rabbitmq_available():
    MQTT_BROKER = "localhost"
    logger.info("Usando localhost para conexão local")

MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "estacao.meteorologica.local")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "mqtt_local_user")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "mqttlocalpassword")


def gerar_dados_sensores():
    temperatura = round(random.uniform(15.0, 35.0), 1)
    umidade = round(random.uniform(30.0, 90.0), 1)
    luminosidade = round(random.uniform(100.0, 1000.0), 1)
    chuva = random.choice([True, False])
    gas_detectado = random.choice([True, False])
    corrente = round(random.uniform(500.0, 3500.0), 1)
    pm1_0 = round(random.uniform(0.0, 50.0), 1)
    pm2_5 = round(random.uniform(0.0, 75.0), 1)
    pm10 = round(random.uniform(0.0, 100.0), 1)
    
    return {
        "temperatura": temperatura,
        "umidade": umidade, 
        "luminosidade": luminosidade,
        "chuva": chuva,
        "gas_detectado": gas_detectado,
        "corrente": corrente,
        "pm1_0": pm1_0,
        "pm2_5": pm2_5,
        "pm10": pm10
    }

def main():
    client = mqtt.Client()
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Conectado ao broker MQTT com sucesso! ({MQTT_BROKER}:{MQTT_PORT})")
            logger.info(f"Tópico: {MQTT_TOPIC}")
        else:
            logger.error(f"Falha na conexão com código: {rc}")
    
    client.on_connect = on_connect
    
    try:
        logger.info(f"Conectando ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_start()
        
        logger.info("Iniciando envio de dados simulados...")
        while True:
            dados = gerar_dados_sensores()
            payload = json.dumps(dados)
            result = client.publish(MQTT_TOPIC, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Enviado: {payload}")
            else:
                logger.error(f"Erro ao enviar: {result.rc}")
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("\nEncerrando envio de dados.")
    except Exception as e:
        logger.error(f"Erro: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()