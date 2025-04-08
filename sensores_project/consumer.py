import os
import django
import json
import paho.mqtt.client as mqtt

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensores_project.settings")
django.setup()

from sensores.models import DadoSensor

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "estacao.meteorologica" 

def on_connect(client, userdata, flags, rc):
    print("Conectado ao broker MQTT com código:", rc)
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print("Mensagem recebida:", payload)

        campos_esperados = ["temperatura", "umidade", "luminosidade", "qualidade_ar", "chuva"]
        if not all(campo in payload for campo in campos_esperados):
            print("Payload incompleto:", payload)
            return

        dado = DadoSensor(
            temperatura=payload["temperatura"],
            umidade=payload["umidade"],
            luminosidade=payload["luminosidade"],
            qualidade_ar=payload["qualidade_ar"],
            chuva=payload["chuva"],        )
        dado.save()
        print("Salvo no banco:", dado)
    except Exception as e:
        print("Erro ao salvar:", e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
