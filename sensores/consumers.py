import json
from channels.generic.websocket import WebsocketConsumer
from datetime import datetime
from asgiref.sync import async_to_sync

class DashboardConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("dashboard", self.channel_name)
        self.accept()
        self.send_initial_data()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("dashboard", self.channel_name)

    def send_initial_data(self):
        from .models import DadoSensor
        latest_data = DadoSensor.objects.last()
        
        if latest_data:
            self.send(text_data=json.dumps({
                'temperatura': latest_data.temperatura,
                'umidade': latest_data.umidade,
                'luminosidade': latest_data.luminosidade,
                'qualidade_ar': latest_data.qualidade_ar,
                'chuva': latest_data.chuva,
                'data_hora': latest_data.data.strftime('%Y-%m-%d %H:%M:%S')
            }))

    def receive(self, text_data):
        self.send_initial_data()

    def sensor_update(self, event):
        self.send(text_data=json.dumps(event['data']))

class SensorConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        from .models import DadoSensor
        
        data = json.loads(text_data)
        sensor_data = DadoSensor.objects.create(
            temperatura=data.get('temperatura'),
            umidade=data.get('umidade'),
            luminosidade=data.get('luminosidade'),
            qualidade_ar=data.get('qualidade_ar'),
            chuva=data.get('chuva')
        )

        async_to_sync(self.channel_layer.group_send)(
            "dashboard",
            {
                "type": "sensor_update",
                "data": {
                    'temperatura': sensor_data.temperatura,
                    'umidade': sensor_data.umidade,
                    'luminosidade': sensor_data.luminosidade,
                    'qualidade_ar': sensor_data.qualidade_ar,
                    'chuva': sensor_data.chuva,
                    'data_hora': sensor_data.data.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
        )