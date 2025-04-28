import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import logging

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
            'data_hora': '2023-01-01T12:00:00'
        }))

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