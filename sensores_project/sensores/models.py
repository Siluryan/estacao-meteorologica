from django.db import models

class DadoSensor(models.Model):
    data = models.DateTimeField(auto_now_add=True)
    temperatura = models.FloatField()
    umidade = models.FloatField()
    luminosidade = models.FloatField()
    qualidade_ar = models.FloatField()
    chuva = models.FloatField()