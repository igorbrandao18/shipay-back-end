# Guia de Configuração

## 1. Configuração do Ambiente

### 1.1 Variáveis de Ambiente

O sistema utiliza variáveis de ambiente para configuração. Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações Gerais
ENVIRONMENT=development  # development, staging, production
DEBUG=true
LOG_LEVEL=INFO

# API
API_V1_STR=/api/v1
PROJECT_NAME=Shipay Backend
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Banco de Dados
DATABASE_URL=postgresql://user:password@localhost:5432/shipay_db
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10
REDIS_TIMEOUT=5

# MongoDB
MONGODB_URL=mongodb://localhost:27017/shipay_db
MONGODB_MAX_POOL_SIZE=10
MONGODB_TIMEOUT_MS=5000

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=shipay-backend
KAFKA_AUTO_OFFSET_RESET=latest
KAFKA_ENABLE_AUTO_COMMIT=true

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Cache
CACHE_TTL=300
CACHE_MAX_SIZE=1000

# Validação
CNPJ_VALIDATION_TIMEOUT=5
CEP_VALIDATION_TIMEOUT=5
VALIDATION_MAX_RETRIES=3

# Agendamento
SCHEDULER_MAX_CONCURRENT_JOBS=10
SCHEDULER_JOB_TIMEOUT=300
SCHEDULER_RETRY_DELAY=60

# Monitoramento
PROMETHEUS_METRICS_PORT=9090
ELASTICSEARCH_URL=http://localhost:9200
```

### 1.2 Configuração por Ambiente

#### Desenvolvimento
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### Staging
```env
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
```

#### Produção
```env
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

## 2. Configuração do Banco de Dados

### 2.1 PostgreSQL

#### Configuração de Pool
```python
# app/core/database.py
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", 5)),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", 10)),
    pool_timeout=30,
    pool_recycle=1800
)
```

#### Configuração de Migrações
```python
# alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

### 2.2 Redis

#### Configuração de Pool
```python
# app/core/cache.py
redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    max_connections=int(os.getenv("REDIS_POOL_SIZE", 10)),
    socket_timeout=int(os.getenv("REDIS_TIMEOUT", 5))
)
```

#### Configuração de Cache
```python
# app/core/cache.py
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL"),
    "CACHE_DEFAULT_TIMEOUT": int(os.getenv("CACHE_TTL", 300)),
    "CACHE_OPTIONS": {
        "max_entries": int(os.getenv("CACHE_MAX_SIZE", 1000))
    }
}
```

### 2.3 MongoDB

#### Configuração de Conexão
```python
# app/core/mongodb.py
client = MongoClient(
    os.getenv("MONGODB_URL"),
    maxPoolSize=int(os.getenv("MONGODB_MAX_POOL_SIZE", 10)),
    serverSelectionTimeoutMS=int(os.getenv("MONGODB_TIMEOUT_MS", 5000))
)
```

## 3. Configuração de Segurança

### 3.1 JWT

#### Configuração de Tokens
```python
# app/core/security.py
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
```

#### Configuração de CORS
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv("BACKEND_CORS_ORIGINS", "[]")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.2 Rate Limiting

#### Configuração Global
```python
# app/core/rate_limit.py
rate_limit = RateLimitMiddleware(
    app,
    key_func=lambda: "global",
    rate_limit=int(os.getenv("RATE_LIMIT_REQUESTS", 100)),
    period=int(os.getenv("RATE_LIMIT_PERIOD", 60))
)
```

## 4. Configuração de Monitoramento

### 4.1 Prometheus

#### Configuração de Métricas
```python
# app/core/metrics.py
prometheus_client.start_http_server(
    int(os.getenv("PROMETHEUS_METRICS_PORT", 9090))
)
```

### 4.2 ELK Stack

#### Configuração de Logs
```python
# app/core/logging.py
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "elasticsearch": {
            "class": "app.core.logging.ElasticsearchHandler",
            "hosts": [os.getenv("ELASTICSEARCH_URL")],
            "formatter": "json"
        }
    },
    "root": {
        "level": os.getenv("LOG_LEVEL", "INFO"),
        "handlers": ["elasticsearch"]
    }
})
```

## 5. Configuração de Serviços

### 5.1 Validação

#### Configuração de Timeouts
```python
# app/services/validation.py
VALIDATION_CONFIG = {
    "timeout": int(os.getenv("CNPJ_VALIDATION_TIMEOUT", 5)),
    "max_retries": int(os.getenv("VALIDATION_MAX_RETRIES", 3))
}
```

### 5.2 Agendamento

#### Configuração de Jobs
```python
# app/services/scheduler.py
SCHEDULER_CONFIG = {
    "max_concurrent_jobs": int(os.getenv("SCHEDULER_MAX_CONCURRENT_JOBS", 10)),
    "job_timeout": int(os.getenv("SCHEDULER_JOB_TIMEOUT", 300)),
    "retry_delay": int(os.getenv("SCHEDULER_RETRY_DELAY", 60))
}
```

## 6. Verificação de Configuração

### 6.1 Script de Verificação
```bash
# scripts/check_config.py
import os
from app.core.config import settings

def check_config():
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET_KEY",
        "KAFKA_BOOTSTRAP_SERVERS"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    print("Configuration check passed successfully!")

if __name__ == "__main__":
    check_config()
```

### 6.2 Comando para Verificar
```bash
python scripts/check_config.py
```

## 7. Atualização de Configuração

### 7.1 Script de Atualização
```bash
# scripts/update_config.py
import os
import json
from app.core.config import settings

def update_config():
    # Atualizar configurações do banco de dados
    settings.DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Atualizar configurações de cache
    settings.REDIS_URL = os.getenv("REDIS_URL")
    
    # Atualizar configurações de segurança
    settings.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    
    print("Configuration updated successfully!")

if __name__ == "__main__":
    update_config()
```

### 7.2 Comando para Atualizar
```bash
python scripts/update_config.py
```

## 8. Suporte

Para suporte técnico ou dúvidas sobre configuração:

- Email: suporte@shipay.com
- Slack: #backend-config
- Documentação: https://docs.shipay.com 