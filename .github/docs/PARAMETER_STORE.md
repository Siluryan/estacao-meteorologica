# Configuração do Parameter Store

Este documento descreve como configurar o AWS Systems Manager Parameter Store para fornecer credenciais e configurações para o deploy do AgroStation.

## Visão Geral

O deploy usa o Parameter Store para armazenar credenciais e configurações sensíveis, evitando hardcoding e melhorando a segurança. O arquivo `.env` é criado automaticamente na EC2 durante o deploy usando os valores do Parameter Store.

## Estrutura de Parâmetros

Todos os parâmetros são armazenados com o prefixo `/agrostation/prod`:

```
/agrostation/prod/
├── database/
│   ├── name          (String)
│   ├── user          (String)
│   ├── password      (SecureString)
│   └── url           (SecureString, opcional)
├── mqtt/
│   ├── broker        (String)
│   ├── port          (String)
│   ├── topic         (String)
│   ├── username      (String)
│   └── password      (SecureString)
├── rabbitmq/
│   ├── user          (String)
│   └── password      (SecureString)
├── django/
│   ├── secret_key    (SecureString)
│   ├── debug         (String)
│   └── superuser/
│       ├── email      (String)
│       ├── username   (String)
│       └── password   (SecureString)
```

## Configuração Inicial

### 1. Criar Parâmetros

Execute o script interativo para criar todos os parâmetros:

```bash
./.github/scripts/setup-parameter-store.sh
```

O script irá solicitar todos os valores necessários e criar os parâmetros no Parameter Store.

### 2. Criar Parâmetros Manualmente

Você também pode criar os parâmetros manualmente usando AWS CLI:

```bash
# Exemplo: Criar parâmetro seguro
aws ssm put-parameter \
  --name "/agrostation/prod/database/password" \
  --value "sua_senha_aqui" \
  --type "SecureString" \
  --region us-east-1 \
  --description "Senha do banco de dados PostgreSQL"

# Exemplo: Criar parâmetro simples
aws ssm put-parameter \
  --name "/agrostation/prod/mqtt/broker" \
  --value "rabbitmq" \
  --type "String" \
  --region us-east-1 \
  --description "Hostname do broker MQTT"
```

### 3. Atualizar Parâmetros

Para atualizar um parâmetro existente, use o mesmo comando com `--overwrite`:

```bash
aws ssm put-parameter \
  --name "/agrostation/prod/database/password" \
  --value "nova_senha" \
  --type "SecureString" \
  --overwrite \
  --region us-east-1
```

## Permissões IAM Necessárias

A role do GitHub Actions (`Agrostation`) precisa das seguintes permissões:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:us-east-1:914256152987:parameter/agrostation/prod/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "ssm.us-east-1.amazonaws.com"
        }
      }
    }
  ]
}
```

A role da EC2 também precisa dessas permissões se o `.env` for criado na EC2 diretamente (via SSM).

## Como Funciona no Deploy

1. O workflow `deploy.yml` executa o job `setup-ec2`
2. A action `setup-env-from-params` é executada
3. A action faz chamadas SSM para buscar todos os parâmetros
4. Um arquivo `.env` é criado na EC2 com todos os valores
5. O Docker Compose usa o arquivo `.env` via `env_file`

## Valores Padrão

Alguns parâmetros têm valores padrão caso não sejam encontrados:

- `POSTGRES_DB`: `sensores_prod`
- `POSTGRES_USER`: `sensores_prod`
- `MQTT_BROKER`: `rabbitmq`
- `MQTT_PORT`: `1883`
- `MQTT_TOPIC`: `estacao/meteorologica`
- `RABBITMQ_DEFAULT_USER`: `mqtt_user`
- `DJANGO_DEBUG`: `0`

## Segurança

- Parâmetros sensíveis (senhas, chaves) são armazenados como `SecureString`
- O Parameter Store usa KMS para criptografia
- A role do GitHub Actions tem acesso apenas aos parâmetros do prefixo `/agrostation/prod`
- Parâmetros não são expostos nos logs do GitHub Actions

## Listar Parâmetros

Para listar todos os parâmetros criados:

```bash
aws ssm describe-parameters \
  --filters "Key=Name,Values=/agrostation/prod" \
  --region us-east-1 \
  --query 'Parameters[*].[Name,Type]' \
  --output table
```

## Excluir Parâmetros

Para excluir um parâmetro:

```bash
aws ssm delete-parameter \
  --name "/agrostation/prod/database/password" \
  --region us-east-1
```

## Troubleshooting

### Parâmetro não encontrado

Se um parâmetro não for encontrado, a action `setup-env-from-params` irá:
- Emitir um aviso
- Usar valores padrão quando disponíveis
- Continuar o deploy (mas pode falhar se parâmetros críticos estiverem faltando)

### Erro de permissão

Verifique se:
1. A role tem permissões `ssm:GetParameter`
2. O prefixo do parâmetro está correto
3. A região está correta (us-east-1)

### KMS Decrypt error

Se houver erro de descriptografia:
1. Verifique se a role tem permissão `kms:Decrypt`
2. Verifique se o parâmetro é do tipo `SecureString`
3. Verifique se a chave KMS está acessível

