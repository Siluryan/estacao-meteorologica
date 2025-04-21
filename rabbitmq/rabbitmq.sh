#!/bin/bash
set -e

until rabbitmqctl status; do
  echo "RabbitMQ ainda não está pronto - aguardando..."
  sleep 2
done

rabbitmq-plugins enable rabbitmq_management rabbitmq_mqtt rabbitmq_web_mqtt

rabbitmqctl add_user "$MQTT_USERNAME" "$MQTT_PASSWORD" || echo "Usuário já existe"
rabbitmqctl set_user_tags "$MQTT_USERNAME" administrator
rabbitmqctl set_permissions -p / "$MQTT_USERNAME" ".*" ".*" ".*"
rabbitmqctl set_topic_permissions -p / "$MQTT_USERNAME" "amq.topic" ".*" ".*"

echo "Configuração do RabbitMQ concluída!"

tail -f /dev/null