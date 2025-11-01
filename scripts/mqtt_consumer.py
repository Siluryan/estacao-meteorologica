import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path

import django
import paho.mqtt.client as mqtt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensores_project.settings")
django.setup()

from sensores.models import DadoSensor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mqtt_consumer")

MQTT_BROKER = os.environ.get("MQTT_BROKER", "rabbitmq")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "estacao/meteorologica")
MQTT_USERNAME = os.environ.get("MQTT_USERNAME")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD")


def on_connect(client, userdata, flags, rc):
    """Callback chamado quando o cliente MQTT conecta ao broker."""
    if rc == 0:
        logger.info(f"Conectado ao broker MQTT com sucesso")
        logger.info(f"Inscrito no tópico: {MQTT_TOPIC}")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Falha na conexão com código: {rc}")


def extract_payload_fields(payload):
    """Extrai e normaliza campos do payload MQTT."""
    return {
        "temperatura": payload.get("temperatura")
        or payload.get("temperatura_dht")
        or 0,
        "umidade": payload.get("umidade") or payload.get("umidade_dht") or 0,
        "luminosidade": payload.get("luminosidade")
        or payload.get("luminosidade_lux")
        or 0,
        "gas_detectado": payload.get("gas_detectado", False),
        "chuva": payload.get("chuva", False),
        "corrente": payload.get("corrente") or payload.get("corrente_mA") or 0,
    }


def create_sensor_data(payload, fields):
    """Cria instância de DadoSensor a partir do payload."""
    dado = DadoSensor(
        temperatura=fields["temperatura"],
        umidade=fields["umidade"],
        luminosidade=fields["luminosidade"],
        gas_detectado=fields["gas_detectado"],
        chuva=1.0 if fields["chuva"] else 0.0,
        qualidade_ar=0,
        corrente=fields["corrente"],
    )

    optional_fields = [
        "pm1_0",
        "pm2_5",
        "pm10",
        "latitude",
        "longitude",
        "localizacao",
        "vento_kmh",
        "vento_ms",
        "umidade_solo_pct",
        "pressao_hpa",
        "altitude_m",
        "temperatura_bmp",
    ]

    for field in optional_fields:
        if field in payload:
            setattr(dado, field, payload[field])

    return dado


def build_websocket_data(dado):
    """Constrói dicionário com dados para envio via WebSocket."""
    return {
        "temperatura": dado.temperatura,
        "umidade": dado.umidade,
        "luminosidade": dado.luminosidade,
        "gas_detectado": dado.gas_detectado,
        "chuva": bool(dado.chuva),
        "corrente": dado.corrente,
        "pm1_0": dado.pm1_0,
        "pm2_5": dado.pm2_5,
        "pm10": dado.pm10,
        "data_hora": timezone.localtime(dado.data).isoformat(),
        "latitude": dado.latitude,
        "longitude": dado.longitude,
        "localizacao": dado.localizacao,
        "vento_kmh": dado.vento_kmh if dado.vento_kmh else 0,
        "vento_ms": dado.vento_ms if dado.vento_ms else 0,
        "umidade_solo_pct": dado.umidade_solo_pct if dado.umidade_solo_pct else 0,
        "pressao_hpa": dado.pressao_hpa if dado.pressao_hpa else 0,
        "altitude_m": dado.altitude_m if dado.altitude_m else 0,
        "temperatura_bmp": dado.temperatura_bmp if dado.temperatura_bmp else 0,
    }


def send_websocket_update(dados_ws):
    """Envia atualização para o grupo WebSocket."""
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            logger.error("Channel layer não encontrado!")
            return

        logger.info(f"Enviando dados para o grupo 'dashboard': {dados_ws}")
        async_to_sync(channel_layer.group_send)(
            "dashboard", {"type": "sensor_update", "data": dados_ws}
        )
        logger.info("Dados enviados para o WebSocket com sucesso")
    except Exception as e:
        logger.error(f"Erro ao enviar dados para o WebSocket: {e}")
        logger.error(traceback.format_exc())


def on_message(client, userdata, msg):
    """Callback chamado quando uma mensagem MQTT é recebida."""
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"Mensagem recebida: {payload}")

        campos_esperados = ["temperatura", "temperatura_dht"]
        if not any(campo in payload for campo in campos_esperados):
            logger.warning(f"Payload incompleto: {payload}")
            return

        fields = extract_payload_fields(payload)
        dado = create_sensor_data(payload, fields)
        dado.save()
        logger.info(f"Dado salvo no banco de dados com ID: {dado.id}")

        dados_ws = build_websocket_data(dado)
        send_websocket_update(dados_ws)

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON: {e}")
        logger.error(f"Payload inválido: {msg.payload.decode()}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")
        logger.error(traceback.format_exc())


def connect_with_retry(client, max_retries=5, delay=5):
    """Tenta conectar ao broker MQTT com retry."""
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Tentativa {attempt + 1} de {max_retries} "
                f"para conectar ao broker MQTT em {MQTT_BROKER}:{MQTT_PORT}"
            )
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            return True
        except Exception as e:
            logger.error(f"Erro na tentativa {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                logger.info(
                    f"Aguardando {delay} segundos antes da próxima tentativa..."
                )
                time.sleep(delay)
    return False


def main():
    """Função principal que inicia o consumer MQTT."""
    logger.info("Iniciando MQTT Consumer...")
    client = mqtt.Client()

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        logger.info(f"Autenticação MQTT configurada com usuário: {MQTT_USERNAME}")
    else:
        logger.info("Iniciando sem autenticação MQTT")

    client.on_connect = on_connect
    client.on_message = on_message

    if connect_with_retry(client):
        logger.info("Conectado com sucesso! Iniciando loop...")
        client.loop_forever()
    else:
        logger.error("Falha ao conectar após várias tentativas. Encerrando...")


if __name__ == "__main__":
    main()
