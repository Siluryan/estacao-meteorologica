import os
import django
import json
import paho.mqtt.client as mqtt
import time
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mqtt_consumer')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensores_project.settings")
django.setup()

from sensores.models import DadoSensor

MQTT_BROKER = os.environ.get("MQTT_BROKER", "rabbitmq")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "estacao.meteorologica")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"Conectado ao broker MQTT com sucesso")
        logger.info(f"Inscrito no tópico: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Falha na conexão com código: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"Mensagem recebida: {payload}")

        campos_esperados = ["temperatura", "umidade", "luminosidade", "qualidade_ar", "chuva"]
        if not all(campo in payload for campo in campos_esperados):
            logger.warning(f"Payload incompleto: {payload}")
            return

        dado = DadoSensor(
            temperatura=payload["temperatura"],
            umidade=payload["umidade"],
            luminosidade=payload["luminosidade"],
            qualidade_ar=payload["qualidade_ar"],
            chuva=payload["chuva"],
        )
        dado.save()
        logger.info(f"Salvo no banco: {dado.id} - {dado.temperatura}°C")

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "dashboard",
            {
                "type": "sensor_update",
                "data": {
                    "temperatura": dado.temperatura,
                    "umidade": dado.umidade,
                    "luminosidade": dado.luminosidade,
                    "qualidade_ar": dado.qualidade_ar,
                    "chuva": dado.chuva,
                    "data_hora": dado.data.isoformat()
                }
            }
        )
        logger.info("Dados enviados para o WebSocket")

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        logger.error(f"Payload inválido: {msg.payload.decode()}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        logger.error(f"Payload que causou o erro: {msg.payload.decode()}")

def connect_with_retry(client, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            logger.info(f"Tentativa {attempt + 1} de {max_retries} para conectar ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}")
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            return True
        except Exception as e:
            logger.error(f"Erro na tentativa {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Aguardando {delay} segundos antes da próxima tentativa...")
                time.sleep(delay)
    return False

def main():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    if connect_with_retry(client):
        logger.info("Conectado com sucesso! Iniciando loop...")
        client.loop_forever()
    else:
        logger.error("Falha ao conectar após várias tentativas. Encerrando...")

if __name__ == "__main__":
    main()