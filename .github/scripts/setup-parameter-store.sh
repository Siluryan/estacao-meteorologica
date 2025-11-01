#!/bin/bash

set -e

AWS_REGION=${AWS_REGION:-us-east-1}
PARAM_PREFIX=${PARAM_PREFIX:-/agrostation/prod}

echo "Criando parâmetros no Parameter Store com prefixo: $PARAM_PREFIX"
echo "Região: $AWS_REGION"
echo ""

create_param() {
  local name=$1
  local value=$2
  local type=${3:-String}
  local secure=${4:-false}
  
  if [ "$secure" = "true" ]; then
    aws ssm put-parameter \
      --name "$PARAM_PREFIX$name" \
      --value "$value" \
      --type "SecureString" \
      --region "$AWS_REGION" \
      --overwrite \
      --description "AgroStation Production Parameter: $name" || echo "Erro ao criar $name"
  else
    aws ssm put-parameter \
      --name "$PARAM_PREFIX$name" \
      --value "$value" \
      --type "$type" \
      --region "$AWS_REGION" \
      --overwrite \
      --description "AgroStation Production Parameter: $name" || echo "Erro ao criar $name"
  fi
  
  echo "OK $name"
}

echo "Database Parameters"
read -sp "POSTGRES_DB [sensores_prod]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-sensores_prod}
create_param "/database/name" "$POSTGRES_DB"

read -sp "POSTGRES_USER [sensores_prod]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-sensores_prod}
create_param "/database/user" "$POSTGRES_USER"

read -sp "POSTGRES_PASSWORD: " POSTGRES_PASSWORD
echo ""
create_param "/database/password" "$POSTGRES_PASSWORD" "String" "true"

read -sp "DATABASE_URL [opcional]: " DATABASE_URL
if [ -n "$DATABASE_URL" ]; then
  create_param "/database/url" "$DATABASE_URL" "String" "true"
fi

echo ""
echo "MQTT Parameters"
read -sp "MQTT_BROKER [rabbitmq]: " MQTT_BROKER
MQTT_BROKER=${MQTT_BROKER:-rabbitmq}
create_param "/mqtt/broker" "$MQTT_BROKER"

read -sp "MQTT_PORT [1883]: " MQTT_PORT
MQTT_PORT=${MQTT_PORT:-1883}
create_param "/mqtt/port" "$MQTT_PORT"

read -sp "MQTT_TOPIC [estacao/meteorologica]: " MQTT_TOPIC
MQTT_TOPIC=${MQTT_TOPIC:-estacao/meteorologica}
create_param "/mqtt/topic" "$MQTT_TOPIC"

read -sp "MQTT_USERNAME: " MQTT_USERNAME
create_param "/mqtt/username" "$MQTT_USERNAME"

read -sp "MQTT_PASSWORD: " MQTT_PASSWORD
echo ""
create_param "/mqtt/password" "$MQTT_PASSWORD" "String" "true"

echo ""
echo "RabbitMQ Parameters"
read -sp "RABBITMQ_DEFAULT_USER [mqtt_user]: " RABBITMQ_USER
RABBITMQ_USER=${RABBITMQ_USER:-mqtt_user}
create_param "/rabbitmq/user" "$RABBITMQ_USER"

read -sp "RABBITMQ_DEFAULT_PASS: " RABBITMQ_PASS
echo ""
create_param "/rabbitmq/password" "$RABBITMQ_PASS" "String" "true"

echo ""
echo "Django Parameters"
read -sp "DJANGO_SECRET_KEY: " DJANGO_SECRET_KEY
echo ""
create_param "/django/secret_key" "$DJANGO_SECRET_KEY" "String" "true"

read -sp "DJANGO_DEBUG [0]: " DJANGO_DEBUG
DJANGO_DEBUG=${DJANGO_DEBUG:-0}
create_param "/django/debug" "$DJANGO_DEBUG"

echo ""
echo "Django Superuser Parameters"
read -sp "DJANGO_SUPERUSER_EMAIL: " DJANGO_EMAIL
create_param "/django/superuser/email" "$DJANGO_EMAIL"

read -sp "DJANGO_SUPERUSER_USERNAME [admin]: " DJANGO_USERNAME
DJANGO_USERNAME=${DJANGO_USERNAME:-admin}
create_param "/django/superuser/username" "$DJANGO_USERNAME"

read -sp "DJANGO_SUPERUSER_PASSWORD: " DJANGO_PASSWORD
echo ""
create_param "/django/superuser/password" "$DJANGO_PASSWORD" "String" "true"

echo ""
echo "Todos os parâmetros criados com sucesso!"
echo ""
echo "Para listar os parâmetros criados:"
echo "  aws ssm describe-parameters --filters \"Key=Name,Values=$PARAM_PREFIX\" --region $AWS_REGION"

