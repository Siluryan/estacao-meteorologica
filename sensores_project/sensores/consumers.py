import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import DadoSensor

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "dashboard",
            self.channel_name
        )
        await self.accept()
        
        latest_data = await self.get_latest_data()
        if latest_data:
            await self.send(text_data=json.dumps({
                "temperatura": latest_data.temperatura,
                "umidade": latest_data.umidade,
                "luminosidade": latest_data.luminosidade,
                "qualidade_ar": latest_data.qualidade_ar,
                "chuva": latest_data.chuva,
                "data_hora": latest_data.data.isoformat()
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "dashboard",
            self.channel_name
        )

    async def receive(self, text_data):
        pass

    async def new_data(self, event):
        data = event['data']
        await self.send(text_data=json.dumps(data))

    @database_sync_to_async
    def get_latest_data(self):
        try:
            return DadoSensor.objects.latest('data')
        except DadoSensor.DoesNotExist:
            return None