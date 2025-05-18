# AgroStation: Sistema de Monitoramento Ambiental

## Visão Geral

AgroStation é um sistema completo de monitoramento ambiental baseado em IoT, projetado para aplicações agrícolas. Fornece dados em tempo real e análises históricas para auxiliar no gerenciamento e tomada de decisões no campo.

## Tecnologias Principais

- **Backend**:
  - Django (Framework Python)
  - Channels (WebSockets)
  - PostgreSQL (Banco de dados relacional)

- **Mensageria e Comunicação**:
  - RabbitMQ com protocolo MQTT para comunicação com sensores
  - Redis para cache e comunicação entre serviços

- **Infraestrutura**:
  - Docker e Docker Compose para containerização
  - Traefik como proxy reverso e balanceador de carga
  - Let's Encrypt para certificados SSL

- **Frontend**:
  - JavaScript para interatividade
  - Chart.js para visualização de dados em gráficos
  - Leaflet para mapas e geolocalização

## Funcionalidades Destacadas

### Dashboard em Tempo Real
- Monitoramento de temperatura, umidade e luminosidade
- Sensores de qualidade do ar (PM1.0, PM2.5, PM10)
- Detecção de gás e monitoramento de corrente elétrica
- Indicação de chuva e localização geográfica

### Análise de Dados
- Estatísticas diárias, semanais e mensais
- Visualização gráfica de tendências
- Registro histórico completo para análises de longo prazo

### Segurança e Usabilidade
- Sistema de login para acesso protegido
- Alertas visuais para valores críticos
- Interface responsiva e intuitiva para desktop e dispositivos móveis

### Comunicação IoT
- WebSockets para atualizações instantâneas na interface
- Compatibilidade com protocolos MQTT para dispositivos IoT
- Arquitetura escalável para suportar múltiplos sensores

## Arquitetura do Sistema

O sistema é composto por diversos serviços containerizados:
- **web**: Aplicação Django principal
- **consumer**: Processador de mensagens assíncronas
- **db**: Banco de dados PostgreSQL
- **rabbitmq**: Broker de mensagens MQTT
- **redis**: Armazenamento em cache e PubSub
- **traefik**: Proxy reverso e SSL

## Instalação e Execução

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

### Configuração do arquivo .env.local
```sh
POSTGRES_DB=sensores_local
POSTGRES_USER=sensores_local
POSTGRES_PASSWORD=localpassword

MQTT_BROKER=rabbitmq
MQTT_PORT=1883
MQTT_TOPIC=estacao.meteorologica.local
MQTT_USERNAME=mqtt_local_user
MQTT_PASSWORD=mqttlocalpassword

DEBUG=1
SECRET_KEY=local_secret_key_for_development_only
DATABASE_URL=postgres://sensores_local:localpassword@db:5432/sensores_local

DJANGO_SUPERUSER_EMAIL=admin_local@example.com
DJANGO_SUPERUSER_PASSWORD=adminlocalpass
DJANGO_SUPERUSER_USERNAME=admin

RABBITMQ_DEFAULT_USER=guest 
RABBITMQ_DEFAULT_PASS=guest
```

## Simulação de Sensores

### Execução do simulation.py

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
python _simulation.py
```

## Configuração para Produção

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