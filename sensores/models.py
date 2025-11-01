from django.db import models


class DadoSensor(models.Model):
    data = models.DateTimeField(auto_now_add=True)
    temperatura = models.FloatField()
    umidade = models.FloatField()
    luminosidade = models.FloatField()
    gas_detectado = models.BooleanField(default=False)
    chuva = models.FloatField(default=0)
    corrente = models.FloatField(default=0)
    qualidade_ar = models.FloatField(default=0)
    pm1_0 = models.FloatField(default=0)
    pm2_5 = models.FloatField(default=0)
    pm10 = models.FloatField(default=0)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    localizacao = models.CharField(max_length=255, null=True, blank=True)
    vento_kmh = models.FloatField(default=0, null=True, blank=True)
    vento_ms = models.FloatField(default=0, null=True, blank=True)
    umidade_solo_pct = models.FloatField(default=0, null=True, blank=True)
    pressao_hpa = models.FloatField(default=0, null=True, blank=True)
    altitude_m = models.FloatField(default=0, null=True, blank=True)
    temperatura_bmp = models.FloatField(default=0, null=True, blank=True)
