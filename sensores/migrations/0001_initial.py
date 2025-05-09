# Generated by Django 4.2 on 2025-04-28 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DadoSensor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateTimeField(auto_now_add=True)),
                ('temperatura', models.FloatField()),
                ('umidade', models.FloatField()),
                ('luminosidade', models.FloatField()),
                ('gas_detectado', models.BooleanField(default=False)),
                ('chuva', models.FloatField(default=0)),
                ('corrente', models.FloatField(default=0)),
                ('qualidade_ar', models.FloatField(default=0)),
                ('pm1_0', models.FloatField(default=0)),
                ('pm2_5', models.FloatField(default=0)),
                ('pm10', models.FloatField(default=0)),
            ],
        ),
    ]
