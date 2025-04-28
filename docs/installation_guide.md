# Guia de Instalação

## 1. Pré-requisitos

### 1.1 Sistema Operacional
- Linux (Ubuntu 20.04 LTS ou superior)
- macOS (10.15 ou superior)
- Windows 10/11 (com WSL2)

### 1.2 Dependências do Sistema
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    build-essential \
    libpq-dev \
    redis-server \
    docker.io \
    docker-compose

# macOS (usando Homebrew)
brew install \
    python@3.10 \
    postgresql \
    redis \
    docker \
    docker-compose
```

### 1.3 Ferramentas de Desenvolvimento
- Git
- Docker
- Docker Compose
- Python 3.10+
- pip
- virtualenv

## 2. Configuração do Ambiente

### 2.1 Clonar o Repositório
```bash
git clone https://github.com/shipay/backend.git
cd backend
```

### 2.2 Criar Ambiente Virtual
```bash
python3.10 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
.\venv\Scripts\activate  # Windows
```

### 2.3 Instalar Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configuração do Banco de Dados

### 3.1 PostgreSQL
```bash
# Criar banco de dados
createdb shipay_db

# Configurar variáveis de ambiente
export DATABASE_URL=postgresql://user:password@localhost:5432/shipay_db
```

### 3.2 Redis
```bash
# Iniciar servidor Redis
redis-server

# Verificar conexão
redis-cli ping
```

### 3.3 MongoDB
```bash
# Usando Docker
docker run -d \
    --name mongodb \
    -p 27017:27017 \
    -v mongodb_data:/data/db \
    mongo:latest
```

## 4. Configuração do Kafka

### 4.1 Usando Docker Compose
```yaml
# docker-compose.yml
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - 9092:9092
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

## 5. Configuração do Ambiente de Desenvolvimento

### 5.1 Variáveis de Ambiente
```bash
# Criar arquivo .env
cp .env.example .env

# Editar .env com suas configurações
nano .env
```

### 5.2 Configurações Recomendadas
```env
# Banco de Dados
DATABASE_URL=postgresql://user:password@localhost:5432/shipay_db

# Redis
REDIS_URL=redis://localhost:6379/0

# MongoDB
MONGODB_URL=mongodb://localhost:27017/shipay_db

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
API_V1_STR=/api/v1
PROJECT_NAME=Shipay Backend
```

## 6. Inicialização do Sistema

### 6.1 Migrações do Banco de Dados
```bash
# Criar migrações
alembic revision --autogenerate -m "Initial migration"

# Aplicar migrações
alembic upgrade head
```

### 6.2 Iniciar Serviços
```bash
# Iniciar Redis
redis-server

# Iniciar Kafka (usando Docker Compose)
docker-compose up -d

# Iniciar a aplicação
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 7. Verificação da Instalação

### 7.1 Testar Conexões
```bash
# Testar PostgreSQL
psql -U user -d shipay_db -c "SELECT 1"

# Testar Redis
redis-cli ping

# Testar MongoDB
mongosh --eval "db.version()"

# Testar Kafka
kafka-topics --list --bootstrap-server localhost:9092
```

### 7.2 Testar API
```bash
# Health Check
curl http://localhost:8000/health

# Documentação Swagger
curl http://localhost:8000/docs
```

## 8. Problemas Comuns

### 8.1 Erro de Conexão com PostgreSQL
```bash
# Verificar se o serviço está rodando
sudo service postgresql status

# Verificar permissões
sudo -u postgres psql -c "ALTER USER user WITH PASSWORD 'password';"
```

### 8.2 Erro de Conexão com Redis
```bash
# Verificar se o serviço está rodando
redis-cli ping

# Reiniciar serviço
sudo service redis-server restart
```

### 8.3 Erro de Conexão com Kafka
```bash
# Verificar logs do Docker
docker-compose logs kafka

# Verificar status dos containers
docker-compose ps
```

## 9. Próximos Passos

1. Configurar monitoramento (Prometheus + Grafana)
2. Configurar logs (ELK Stack)
3. Configurar CI/CD
4. Configurar ambiente de produção

## 10. Suporte

Para suporte técnico ou dúvidas sobre a instalação:

- Email: suporte@shipay.com
- Slack: #backend-support
- Documentação: https://docs.shipay.com 