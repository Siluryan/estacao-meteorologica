import os
import time
import json
import random
import socket
import logging
import requests
import unicodedata
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mqtt_simulator')

MQTT_BROKER = os.getenv("MQTT_BROKER", "rabbitmq")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "estacao.meteorologica.local")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

def is_rabbitmq_available():
    try:
        socket.gethostbyname(MQTT_BROKER)
        return True
    except socket.gaierror:
        return False

if MQTT_BROKER == "rabbitmq" and not is_rabbitmq_available():
    MQTT_BROKER = "localhost"
    logger.info("Usando localhost para conexão local")

GEO_API_URL = os.getenv("GEO_API_URL", "https://nominatim.openstreetmap.org/reverse")

def gerar_dados_sensores():
    return {
        "temperatura": round(random.uniform(15.0, 35.0), 1),
        "umidade": round(random.uniform(30.0, 90.0), 1),
        "luminosidade": round(random.uniform(100.0, 1000.0), 1),
        "luminosidade": 30,
        "chuva": random.choice([True, False]),
        "gas_detectado": random.choice([True, False]),
        "corrente": round(random.uniform(500.0, 3500.0), 1),
        "pm1_0": round(random.uniform(0.0, 50.0), 1),
        "pm2_5": round(random.uniform(0.0, 75.0), 1),
        "pm10": round(random.uniform(0.0, 100.0), 1)
    }

def get_gps_coordinates():
    return -23.024859, -49.472434

def get_location_name(lat, lon):
    params = {
        'format': 'jsonv2',
        'lat': lat,
        'lon': lon
    }
    headers = {'User-Agent': 'mqtt-simulator/1.0'}
    try:
        resp = requests.get(GEO_API_URL, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json().get('address', {})
        parts = [data.get(key) for key in ('city', 'town', 'village', 'state', 'country') if data.get(key)]
        return ", ".join(parts)
    except Exception as e:
        logger.warning(f"Falha no reverse geocoding: {e}")
        return None

def remove_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize('NFKD', texto)
    return nfkd.encode('ASCII', 'ignore').decode('ASCII')

def setup_mqtt_client():
    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    def on_connect(cl, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Conectado ao broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        else:
            logger.error(f"Falha na conexão MQTT, código: {rc}")

    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)
    return client

def main():
    client = setup_mqtt_client()
    client.loop_start()

    try:
        logger.info("Iniciando envio de dados MQTT...")
        while True:
            sensores = gerar_dados_sensores()

            lat, lon = get_gps_coordinates()
            local_bruto = get_location_name(lat, lon) or ""
            local_ascii = remove_acentos(local_bruto)

            payload = {
                **sensores,
                'latitude': lat,
                'longitude': lon,
                'localizacao': local_ascii
            }
            msg = json.dumps(payload, ensure_ascii=True)

            result = client.publish(MQTT_TOPIC, msg)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Enviado ao tópico '{MQTT_TOPIC}': {msg}")
            else:
                logger.error(f"Erro ao enviar mensagem MQTT, código: {result.rc}")

            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("Encerrando simulador MQTT...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == '__main__':
    main()