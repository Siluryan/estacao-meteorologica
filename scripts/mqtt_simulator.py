import json
import logging
import os
import random
import socket
import time
import unicodedata

import paho.mqtt.client as mqtt
import requests
from dotenv import load_dotenv
from pathlib import Path

env_files = [Path(".env.local"), Path(".env")]
env_loaded = False
for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        env_loaded = True
        break

if not env_loaded:
    load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mqtt_simulator")

MQTT_BROKER = os.getenv("MQTT_BROKER", "rabbitmq")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "estacao/meteorologica")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

if not MQTT_USERNAME:
    MQTT_USERNAME = "mqtt_local_user"
    logger.warning(
        "MQTT_USERNAME não definido, usando valor padrão para desenvolvimento local"
    )
if not MQTT_PASSWORD:
    MQTT_PASSWORD = "mqttlocalpassword"
    logger.warning(
        "MQTT_PASSWORD não definido, usando valor padrão para desenvolvimento local"
    )

GEO_API_URL = os.getenv("GEO_API_URL", "https://nominatim.openstreetmap.org/reverse")


def is_rabbitmq_available():
    """Verifica se o RabbitMQ está disponível via DNS."""
    try:
        socket.gethostbyname(MQTT_BROKER)
        return True
    except socket.gaierror:
        return False


if MQTT_BROKER == "rabbitmq" and not is_rabbitmq_available():
    MQTT_BROKER = "127.0.0.1"
    logger.info("RabbitMQ não disponível via DNS, usando 127.0.0.1 para conexão local")

if not MQTT_BROKER or MQTT_BROKER.strip() == "":
    logger.error("MQTT_BROKER não pode ser vazio")
    exit(1)

if MQTT_BROKER.lower() in ["localhost", "local"]:
    MQTT_BROKER = "127.0.0.1"
    logger.info("Host normalizado: localhost -> 127.0.0.1")


def gerar_dados_sensores():
    """Gera dados simulados dos sensores."""
    return {
        "temperatura": round(random.uniform(15.0, 35.0), 1),
        "umidade": round(random.uniform(30.0, 90.0), 1),
        "luminosidade": round(random.uniform(100.0, 1000.0), 1),
        "chuva": random.choice([True, False]),
        "gas_detectado": random.choice([True, False]),
        "corrente": round(random.uniform(500.0, 3500.0), 1),
        "pm1_0": round(random.uniform(0.0, 50.0), 1),
        "pm2_5": round(random.uniform(0.0, 75.0), 1),
        "pm10": round(random.uniform(0.0, 100.0), 1),
        "vento_kmh": round(random.uniform(0.0, 50.0), 1),
        "vento_ms": round(random.uniform(0.0, 13.9), 1),
        "umidade_solo_pct": round(random.uniform(20.0, 80.0), 1),
        "pressao_hpa": round(random.uniform(980.0, 1020.0), 1),
        "altitude_m": round(random.uniform(0.0, 1000.0), 1),
        "temperatura_bmp": round(random.uniform(15.0, 35.0), 1),
    }


def get_gps_coordinates():
    """Retorna coordenadas GPS fixas para simulação."""
    return -23.024859, -49.472434


def get_location_name(lat, lon):
    """Obtém nome da localização via reverse geocoding."""
    params = {"format": "jsonv2", "lat": lat, "lon": lon}
    headers = {"User-Agent": "mqtt-simulator/1.0"}

    try:
        resp = requests.get(GEO_API_URL, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json().get("address", {})
        parts = [
            data.get(key)
            for key in ("city", "town", "village", "state", "country")
            if data.get(key)
        ]
        return ", ".join(parts)
    except Exception as e:
        logger.warning(f"Falha no reverse geocoding: {e}")
        return None


def remove_acentos(texto):
    """Remove acentos do texto."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return nfkd.encode("ASCII", "ignore").decode("ASCII")


def validar_payload(payload):
    """Valida se o payload contém todos os campos esperados."""
    campos_obrigatorios = ["temperatura"]
    campos_opcionais = [
        "umidade",
        "luminosidade",
        "chuva",
        "gas_detectado",
        "corrente",
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

    faltando = [campo for campo in campos_obrigatorios if campo not in payload]
    if faltando:
        logger.error(f"Campos obrigatórios faltando: {faltando}")
        return False

    presente = [campo for campo in campos_opcionais if campo in payload]
    logger.info(
        f"Validação OK: {len(campos_obrigatorios)} obrigatórios, "
        f"{len(presente)}/{len(campos_opcionais)} opcionais presentes"
    )
    return True


def formatar_resumo_dados(payload):
    """Formata um resumo legível dos dados sendo enviados."""
    resumo = []
    resumo.append("Dados sendo enviados:")
    resumo.append(f"  Temperatura: {payload.get('temperatura', 'N/A')}°C")
    resumo.append(f"  Umidade: {payload.get('umidade', 'N/A')}%")
    resumo.append(f"  Luminosidade: {payload.get('luminosidade', 'N/A')} lux")
    resumo.append(f"  Chuva: {'Sim' if payload.get('chuva') else 'Não'}")
    resumo.append(
        f"  Gás detectado: {'Sim' if payload.get('gas_detectado') else 'Não'}"
    )
    resumo.append(f"  Corrente: {payload.get('corrente', 'N/A')} mA")

    if "pm1_0" in payload:
        resumo.append(
            f"  Qualidade do ar - PM1.0: {payload['pm1_0']}, "
            f"PM2.5: {payload.get('pm2_5', 'N/A')}, "
            f"PM10: {payload.get('pm10', 'N/A')}"
        )

    if "latitude" in payload and "longitude" in payload:
        resumo.append(f"  GPS: {payload['latitude']}, {payload['longitude']}")
        if "localizacao" in payload:
            resumo.append(f"  Local: {payload['localizacao']}")

    if "vento_kmh" in payload:
        resumo.append(
            f"  Vento: {payload['vento_kmh']} km/h "
            f"({payload.get('vento_ms', 'N/A')} m/s)"
        )

    if "umidade_solo_pct" in payload:
        resumo.append(f"  Umidade solo: {payload['umidade_solo_pct']}%")

    if "pressao_hpa" in payload:
        resumo.append(
            f"  Pressão: {payload['pressao_hpa']} hPa, "
            f"Altitude: {payload.get('altitude_m', 'N/A')}m"
        )
        resumo.append(f"  Temp BMP280: {payload.get('temperatura_bmp', 'N/A')}°C")

    return "\n".join(resumo)


def setup_mqtt_client():
    """Configura e retorna cliente MQTT."""
    try:
        client = mqtt.Client(
            client_id="mqtt_simulator",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
    except AttributeError:
        client = mqtt.Client(client_id="mqtt_simulator")

    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        logger.info(f"Autenticação configurada: usuário '{MQTT_USERNAME}'")
    else:
        logger.error("Credenciais MQTT não fornecidas! O RabbitMQ requer autenticação.")
        logger.error("Defina MQTT_USERNAME e MQTT_PASSWORD no .env.local")

    stats = {"enviados": 0, "erros": 0, "conectado": False}

    def on_connect(cl, userdata, flags, reason_code, properties=None):
        rc = reason_code if isinstance(reason_code, int) else reason_code.value
        if rc == 0:
            stats["conectado"] = True
            logger.info(f"Conectado ao broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
            logger.info(f"Tópico configurado: {MQTT_TOPIC}")
        else:
            stats["conectado"] = False
            logger.error(f"Falha na conexão MQTT, código: {rc}")
            if rc == 1:
                logger.error("Razão: Conexão recusada - versão do protocolo incorreta")
            elif rc == 2:
                logger.error(
                    "Razão: Conexão recusada - identificador de cliente rejeitado"
                )
            elif rc == 3:
                logger.error("Razão: Conexão recusada - servidor indisponível")
            elif rc == 4:
                logger.error("Razão: Conexão recusada - credenciais inválidas")
            elif rc == 5:
                logger.error("Razão: Conexão recusada - não autorizado")
            elif rc >= 128:
                logger.error(f"Razão: Erro de rede ou conexão (código: {rc})")
                logger.error(
                    "O broker MQTT pode não estar rodando ou não ser acessível"
                )
                logger.error(f"Verifique: {MQTT_BROKER}:{MQTT_PORT}")
            else:
                logger.error(f"Razão: Erro desconhecido (código: {rc})")

    def on_publish(cl, userdata, mid, reason_code=None, properties=None):
        stats["enviados"] += 1
        logger.info(f"Mensagem #{stats['enviados']} publicada com sucesso (mid: {mid})")

    def on_disconnect(cl, userdata, rc, reason_code=None, properties=None):
        disconnect_code = (
            rc if isinstance(rc, int) else (reason_code.value if reason_code else 0)
        )
        stats["conectado"] = False
        if disconnect_code != 0:
            logger.warning(f"Desconectado inesperadamente (código: {disconnect_code})")
        else:
            logger.info("Desconectado normalmente")

    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.stats = stats

    try:
        logger.info(f"Tentando conectar a {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except ValueError as e:
        logger.error(f"Host inválido: {e}")
        logger.error(f"Host fornecido: '{MQTT_BROKER}'")
        logger.error("Use um endereço IP (ex: 127.0.0.1) ou hostname válido")
    except Exception as e:
        logger.error(f"Erro ao conectar: {e}")
        logger.error(f"Verifique se o broker está rodando em {MQTT_BROKER}:{MQTT_PORT}")

    return client


def main():
    """Função principal do simulador."""
    logger.info("=" * 60)
    logger.info("Iniciando Simulador MQTT")
    logger.info("=" * 60)
    logger.info(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
    logger.info(f"Tópico: {MQTT_TOPIC}")
    logger.info("-" * 60)

    client = setup_mqtt_client()

    logger.info("Iniciando loop do cliente MQTT...")
    client.loop_start()

    for i in range(5):
        if client.stats["conectado"]:
            break
        time.sleep(1)
        if i == 4:
            logger.warning("Ainda aguardando conexão...")

    if not client.stats["conectado"]:
        logger.error("Não foi possível conectar ao broker MQTT")
        logger.error(
            "Verifique se o broker está rodando e as credenciais estão corretas"
        )
        client.loop_stop()
        return

    try:
        logger.info("Conectado! Iniciando envio de dados...")
        logger.info("-" * 60)
        ciclo = 0

        while True:
            ciclo += 1
            logger.info(f"\nCiclo #{ciclo}")
            logger.info("-" * 60)

            sensores = gerar_dados_sensores()
            lat, lon = get_gps_coordinates()
            local_bruto = get_location_name(lat, lon) or ""
            local_ascii = remove_acentos(local_bruto)

            payload = {
                **sensores,
                "latitude": lat,
                "longitude": lon,
                "localizacao": local_ascii,
            }

            if not validar_payload(payload):
                logger.error("Payload inválido, pulando envio")
                client.stats["erros"] += 1
                time.sleep(5)
                continue

            logger.info("\n" + formatar_resumo_dados(payload))

            try:
                msg = json.dumps(payload, ensure_ascii=True)
            except Exception as e:
                logger.error(f"Erro ao serializar JSON: {e}")
                client.stats["erros"] += 1
                time.sleep(5)
                continue

            try:
                result = client.publish(MQTT_TOPIC, msg, qos=1)
                result.wait_for_publish(timeout=2)

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Enviado para tópico: {MQTT_TOPIC}")
                    logger.debug(f"Payload JSON: {msg}")
                else:
                    logger.error(f"Erro ao enviar mensagem MQTT, código: {result.rc}")
                    client.stats["erros"] += 1
            except Exception as e:
                logger.error(f"Exceção ao publicar: {e}")
                client.stats["erros"] += 1

            total = client.stats["enviados"] + client.stats["erros"]
            if total > 0:
                taxa_sucesso = (
                    client.stats["enviados"] / total * 100 if total > 0 else 0
                )
                logger.info(
                    f"Estatísticas: {client.stats['enviados']} enviados, "
                    f"{client.stats['erros']} erros "
                    f"({taxa_sucesso:.1f}% sucesso)"
                )

            logger.info("-" * 60)
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Encerrando simulador MQTT...")
        logger.info(f"Total enviado: {client.stats['enviados']}")
        logger.info(f"Total erros: {client.stats['erros']}")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("Desconectado do broker MQTT")


if __name__ == "__main__":
    main()
