import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import logging
from django.utils import timezone

logger = logging.getLogger('websocket_consumer')

class DashboardConsumer(WebsocketConsumer):
    def connect(self):
        logger.info("WebSocket connection attempt")
        try:
            async_to_sync(self.channel_layer.group_add)(
                "dashboard",
                self.channel_name
            )
            self.accept()
            logger.info("WebSocket connection established")
            
            from .models import DadoSensor
            
            ultimo_dado = DadoSensor.objects.order_by('-data').first()
            
            if ultimo_dado:
                dados = {
                    'temperatura': ultimo_dado.temperatura,
                    'umidade': ultimo_dado.umidade,
                    'luminosidade': ultimo_dado.luminosidade,
                    'gas_detectado': ultimo_dado.gas_detectado,
                    'chuva': bool(ultimo_dado.chuva),
                    'corrente': ultimo_dado.corrente,
                    'pm1_0': ultimo_dado.pm1_0,
                    'pm2_5': ultimo_dado.pm2_5,
                    'pm10': ultimo_dado.pm10,
                    'data_hora': timezone.localtime(ultimo_dado.data).isoformat(),
                    'latitude': ultimo_dado.latitude,
                    'longitude': ultimo_dado.longitude,
                    'localizacao': ultimo_dado.localizacao
                }
                logger.info(f"Enviando dados do último registro: {ultimo_dado.data}")
                self.send(text_data=json.dumps(dados))
                logger.info(f"Dados enviados com sucesso: {dados}")
            else:
                data_atual = timezone.now()
                logger.info("Não há registros no banco de dados. Enviando valores padrão.")
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
                    'data_hora': data_atual.isoformat(),
                    'latitude': -23.550520,
                    'longitude': -46.633308,
                    'localizacao': 'Sao Paulo, Brazil'
                }))
                logger.info("Valores padrão enviados com sucesso")
        except Exception as e:
            logger.error(f"Erro durante a conexão WebSocket: {e}")
            import traceback
            logger.error(traceback.format_exc())


    def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code: {close_code}")
        try:
            async_to_sync(self.channel_layer.group_discard)(
                "dashboard",
                self.channel_name
            )
        except Exception as e:
            logger.error(f"Erro ao desconectar WebSocket: {e}")

    def sensor_update(self, event):
        try:
            logger.info(f"Recebendo atualização de sensor para enviar ao cliente")
            if 'data' not in event:
                logger.error(f"Formato incorreto na mensagem de atualização: {event}")
                return
                
            data = event['data']
            logger.info(f"Enviando dados ao cliente: {data}")
            self.send(text_data=json.dumps(data))
            logger.info("Dados enviados com sucesso ao cliente")
        except Exception as e:
            logger.error(f"Erro ao processar atualização de sensor: {e}")
            import traceback
            logger.error(traceback.format_exc())


class SensorConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        logger.info("Sensor WebSocket connection established")

    def disconnect(self, close_code):
        logger.info(f"Sensor WebSocket disconnected with code: {close_code}")

    def receive(self, text_data):
        try:
            logger.info(f"Received sensor data: {text_data}")
            text_data_json = json.loads(text_data)
            
            async_to_sync(self.channel_layer.group_send)(
                "dashboard",
                {
                    'type': 'sensor_update',
                    'data': text_data_json
                }
            )
            logger.info("Dados encaminhados com sucesso para o grupo dashboard")
        except Exception as e:
            logger.error(f"Erro ao processar dados recebidos: {e}")
            import traceback
            logger.error(traceback.format_exc())