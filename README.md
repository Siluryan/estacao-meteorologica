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
  - HTML5, CSS3 e JavaScript ES6+
  - Chart.js para visualização de dados em gráficos
  - Leaflet para mapas e geolocalização
  - Font Awesome para ícones
  - Design responsivo com tema verde moderno

## Sensores Integrados

O sistema monitora os seguintes sensores:

### Sensores Básicos
- **Temperatura** (DHT22 e BMP280)
- **Umidade do Ar** (DHT22)
- **Luminosidade** (TEMT6000)
- **Detecção de Chuva**
- **Detecção de Gás** (MQ-2)
- **Corrente Elétrica** (ACS712)

### Sensores de Qualidade do Ar
- **PM1.0** (Partículas ultrafinas)
- **PM2.5** (Partículas finas respiráveis)
- **PM10** (Partículas inaláveis)

### Sensores Meteorológicos Avançados
- **Velocidade do Vento** (Anemômetro - km/h e m/s)
- **Umidade do Solo**
- **Pressão Atmosférica** (BMP280 - hPa)
- **Altitude** (BMP280 - metros)
- **Temperatura BMP280**

### Geolocalização
- **GPS** (Latitude e Longitude)
- **Localização** (Reverse geocoding)

## Funcionalidades Destacadas

### Dashboard em Tempo Real
- Monitoramento completo de todos os sensores
- Visualização gráfica em tempo real (Chart.js)
- Mapa interativo com localização GPS (Leaflet)
- Indicadores visuais de status e alertas
- Atualização automática via WebSocket

### Páginas do Sistema
- **Dashboard**: Visualização principal com dados em tempo real
- **Estatísticas**: Análise histórica com tabelas e gráficos
- **Sobre**: Informações sobre o projeto e tecnologias
- **Ajuda**: Guia completo de uso e resolução de problemas

### Análise de Dados
- Estatísticas diárias, semanais e mensais
- Visualização gráfica de tendências
- Registro histórico completo para análises de longo prazo
- Filtros por período para análise temporal

### Segurança e Usabilidade
- Sistema de login para acesso protegido
- Alertas visuais para valores críticos
- Interface responsiva e intuitiva para desktop e dispositivos móveis
- Design moderno com tema verde focado em aplicações agrícolas

### Comunicação IoT
- WebSockets para atualizações instantâneas na interface
- Compatibilidade com protocolos MQTT para dispositivos IoT
- Arquitetura escalável para suportar múltiplos sensores
- Validação e tratamento robusto de dados recebidos

## Arquitetura do Sistema

O sistema é composto por diversos serviços containerizados:
- **web**: Aplicação Django principal (Daphne/ASGI)
- **consumer**: Processador de mensagens MQTT assíncronas
- **db**: Banco de dados PostgreSQL
- **rabbitmq**: Broker de mensagens MQTT
- **redis**: Armazenamento em cache e PubSub

## Estrutura do Projeto

```
estacao-meteorologica/
├── scripts/                 # Scripts auxiliares
│   ├── create_superuser.py  # Criação de superusuário
│   ├── mqtt_consumer.py     # Consumidor MQTT
│   └── mqtt_simulator.py    # Simulador de sensores
├── sensores/                # Aplicação Django principal
│   ├── models.py            # Modelos de dados
│   ├── views.py             # Views e lógica de negócio
│   ├── consumers.py         # WebSocket consumers
│   ├── static/              # Arquivos estáticos
│   │   └── sensores/
│   │       ├── css/         # Estilos CSS modulares
│   │       └── js/          # JavaScript modular
│   └── templates/           # Templates HTML
├── sensores_project/        # Configurações do projeto Django
└── docker-compose.yaml      # Configuração Docker Compose
```

## Instalação e Execução

### Requisitos
- Docker e Docker Compose instalados
- Python 3.8+ (para executar scripts localmente)

### Execução Local

Para desenvolvimento local, use o arquivo `docker-compose.yaml.local`:

```bash
docker-compose -f docker-compose.yaml.local up --build -d
```

A aplicação estará disponível em `http://localhost:8000`.

### Execução em Produção

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
MQTT_TOPIC=estacao/meteorologica
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
MQTT_TOPIC=estacao/meteorologica
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

### Execução do simulador MQTT

O simulador permite testar o sistema localmente enviando dados simulados via MQTT.

**Pré-requisitos:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Execução:**
```bash
python scripts/mqtt_simulator.py
```

O simulador:
- Gera dados aleatórios para todos os sensores
- Publica no tópico MQTT configurado
- Valida payload antes de enviar
- Fornece estatísticas de envio
- Carrega credenciais do `.env.local` automaticamente

**Configuração:**
Certifique-se de que o RabbitMQ está rodando antes de executar o simulador. As credenciais MQTT devem estar configuradas no `.env.local` ou serão usados valores padrão para desenvolvimento.

## Organização do Código

### Estrutura de Arquivos

O projeto segue boas práticas de organização:

- **Scripts auxiliares**: Movidos para a pasta `scripts/`
- **Estáticos**: CSS e JavaScript modularizados em arquivos separados
- **Templates**: Separação clara entre base, páginas e componentes
- **Modelos**: Um modelo principal (`DadoSensor`) para todos os dados

### Frontend Modular

- **CSS**: Arquivos separados por funcionalidade (base, dashboard, estatisticas)
- **JavaScript**: Módulos organizados (charts, indicators, map, websocket, utils)
- **Reutilização**: Componentes e funções compartilhadas

## Formatação de Código

Este projeto utiliza o [Black](https://github.com/psf/black) para formatação automática de código Python.

### Instalação

```bash
pip install -r requirements.txt
```

Ou apenas o Black:

```bash
make install-black
```

### Uso

Para formatar todo o código:

```bash
black .
```

Ou usando o Makefile:

```bash
make format
```

Para verificar se o código está formatado (sem fazer alterações):

```bash
black --check .
```

Ou:

```bash
make format-check
```

### Configuração

As configurações do Black estão em `pyproject.toml`:
- **Line length**: 88 caracteres (padrão PEP 8)
- **Target versions**: Python 3.8, 3.9, 3.10, 3.11
- **Exclui**: migrations, arquivos de build, ambientes virtuais

### Integração com Editores

#### VS Code
Adicione ao `.vscode/settings.json`:
```json
{
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

#### PyCharm
1. Settings → Tools → Black
2. Habilitar "Use Black"
3. Configurar o caminho do executável

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

## Desenvolvimento

### Estrutura de Scripts

- `scripts/create_superuser.py`: Cria ou atualiza o superusuário Django
- `scripts/mqtt_consumer.py`: Consumidor MQTT que processa mensagens dos sensores
- `scripts/mqtt_simulator.py`: Simulador para testar envio de dados MQTT

### Páginas Disponíveis

- `/`: Dashboard principal
- `/estatisticas/`: Página de estatísticas históricas
- `/sobre/`: Informações sobre o projeto
- `/ajuda/`: Guia de ajuda e documentação
- `/login/`: Página de autenticação

### Acesso ao Sistema

Após iniciar os containers, acesse:
- **Aplicação**: `http://localhost:8000` (local) ou conforme DOMAIN configurado
- **Credenciais padrão (local)**: Usuário `admin`, senha conforme `.env.local`
