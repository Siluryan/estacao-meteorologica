### Comandos necessários

```bash
docker-compose up --build -d
```

### Configuração do arquivo .env

```sh
POSTGRES_DB=sensores
POSTGRES_USER=sensores
POSTGRES_PASSWORD=senhasegura123

MQTT_BROKER=rabbitmq
MQTT_PORT=1883
MQTT_TOPIC=estacao.meteorologica
MQTT_USERNAME=mqtt_username
MQTT_PASSWORD=mqttsenha123

DEBUG=1
SECRET_KEY=chavemuitosegura123
DATABASE_URL=postgres://sensores:senhasegura123@db:5432/sensores

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@gmail.com
DJANGO_SUPERUSER_PASSWORD=adminsenha123
```

### Execução do simulation.py

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python _simulation.py
```