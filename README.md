### Comandos necessários

```bash
docker-compose up --build -d
```

### Configuração do arquivo .env

```sh
ACME_EMAIL=example@gmail.com
DOMAIN=www.example.com
TRAEFIK_DASHBOARD_AUTH=admin:senhaadmin

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

### Criar um service para permitir reinicialização do servidor

#### Crie um arquivo em /etc/systemd/system/docker-compose-app.service

```bash
[Unit]
Description=Docker Compose Application Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
User=seu-usuario-linux 
Group=seu-grupo-linux
WorkingDirectory=/home/usuario/caminho-para-o-seu-docker-compose

Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/docker-compose up --build -d
ExecStop=/usr/local/bin/docker-compose down
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

#### Execute os seguintes comandos
```bash
sudo systemctl daemon-reload
sudo systemctl enable docker-compose-app    
sudo systemctl start docker-compose-app 
```