import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import logging
from django.utils import timezone

logger = logging.getLogger('websocket_consumer')

class DashboardConsumer(WebsocketConsumer):
    def connect(self):
        logger.info("WebSocket connection attempt")
        async_to_sync(self.channel_layer.group_add)(
            "dashboard",
            self.channel_name
        )
        self.accept()
        logger.info("WebSocket connection established")
        
        from .models import DadoSensor
        
        ultimo_dado = DadoSensor.objects.order_by('-data').first()
        
        if ultimo_dado:
            self.send(text_data=json.dumps({
                'temperatura': ultimo_dado.temperatura,
                'umidade': ultimo_dado.umidade,
                'luminosidade': ultimo_dado.luminosidade,
                'gas_detectado': ultimo_dado.gas_detectado,
                'chuva': bool(ultimo_dado.chuva),
                'corrente': ultimo_dado.corrente,
                'pm1_0': ultimo_dado.pm1_0,
                'pm2_5': ultimo_dado.pm2_5,
                'pm10': ultimo_dado.pm10,
                'data_hora': timezone.localtime(ultimo_dado.data).isoformat()
            }))
            logger.info(f"Enviando dados do último registro: {ultimo_dado.data}")
        else:
            data_atual = timezone.now()
            self.send(text_data=json.dumps({
                'temperatura': 25.0,
                'umidade': 60.0,
                'luminosidade': 800.0,
                'gas_detectado': False,
                'chuva': False,
                'corrente': 1000.0,
                'pm1_0': 10.0,
                'pm2_5': 25.0,
                'pm10': 50.0,
                'data_hora': data_atual.isoformat()
            }))
            logger.info("Não há registros no banco de dados. Enviando valores padrão com a data atual.")


    def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code: {close_code}")
        async_to_sync(self.channel_layer.group_discard)(
            "dashboard",
            self.channel_name
        )

    def sensor_update(self, event):
        logger.info(f"Sending sensor update: {event['data']}")
        self.send(text_data=json.dumps(event['data']))

class SensorConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        logger.info("Sensor WebSocket connection established")

    def disconnect(self, close_code):
        logger.info(f"Sensor WebSocket disconnected with code: {close_code}")

    def receive(self, text_data):
        logger.info(f"Received sensor data: {text_data}")
        text_data_json = json.loads(text_data)
        
        async_to_sync(self.channel_layer.group_send)(
            "dashboard",
            {
                'type': 'sensor_update',
                'data': text_data_json
            }
        )