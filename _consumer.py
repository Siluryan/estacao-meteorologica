import os
import django
import json
import paho.mqtt.client as mqtt
import time
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone

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

        campos_esperados = ["temperatura", "umidade", "luminosidade", "gas_detectado", "chuva"]
        if not all(campo in payload for campo in campos_esperados):
            logger.warning(f"Payload incompleto: {payload}")
            return

        dado = DadoSensor(
            temperatura=payload["temperatura"],
            umidade=payload["umidade"],
            luminosidade=payload["luminosidade"],
            gas_detectado=payload["gas_detectado"],
            chuva=1.0 if payload["chuva"] else 0.0,
            qualidade_ar=0,
        )
        
        if "corrente" in payload:
            dado.corrente = payload["corrente"]
        if "pm1_0" in payload:
            dado.pm1_0 = payload["pm1_0"]
        if "pm2_5" in payload:
            dado.pm2_5 = payload["pm2_5"]
        if "pm10" in payload:
            dado.pm10 = payload["pm10"]
            
        dado.save()
        logger.info(f"Dado salvo no banco de dados com ID: {dado.id}")
        
        dados_ws = {
            "temperatura": dado.temperatura,
            "umidade": dado.umidade,
            "luminosidade": dado.luminosidade,
            "gas_detectado": dado.gas_detectado,
            "chuva": bool(dado.chuva), 
            "corrente": dado.corrente,
            "pm1_0": dado.pm1_0,
            "pm2_5": dado.pm2_5,
            "pm10": dado.pm10,
            "data_hora": timezone.localtime(dado.data).isoformat()
        }
        
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "dashboard",
                {
                    "type": "sensor_update",
                    "data": dados_ws
                }
            )
            logger.info("Dados enviados para o WebSocket com sucesso")
        except Exception as e:
            logger.error(f"Erro ao enviar dados para o WebSocket: {e}")
            import traceback
            logger.error(traceback.format_exc())
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        logger.error(f"Payload inválido: {msg.payload.decode()}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        import traceback
        logger.error(traceback.format_exc())

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