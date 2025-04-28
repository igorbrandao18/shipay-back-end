import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.core.database import Base, engine, get_db
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock do Redis para os testes."""
    with patch('app.core.redis.RedisManager') as mock:
        mock.get_client = AsyncMock()
        mock.initialize = AsyncMock()
        mock.close = AsyncMock()
        mock.health_check = AsyncMock(return_value=True)
        yield mock

@pytest.fixture(autouse=True)
def setup_database():
    """Configura o banco de dados para os testes."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """Fornece uma sessão do banco de dados para os testes."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_token():
    """Cria um token de autenticação para os testes."""
    access_token = create_access_token({"sub": "test@example.com"})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def client(auth_token, db):
    """Cria um cliente de teste para a API com autenticação."""
    with TestClient(app) as client:
        client.headers.update(auth_token)
        yield client

def test_concurrent_user_creation(client):
    """Testa a criação concorrente de usuários."""
    num_requests = 100
    latencies = []
    
    def create_user():
        start_time = time.time()
        response = client.post(
            "/api/v1/users",
            json={
                "name": "Test User",
                "email": f"test{time.time()}@example.com",
                "role_id": 1
            }
        )
        end_time = time.time()
        latencies.append(end_time - start_time)
        return response.status_code == 201
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: create_user(), range(num_requests)))
    
    success_rate = sum(1 for r in results if r) / num_requests
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95  # 95% de sucesso
    assert avg_latency < 1.0  # Latência média < 1s
    assert p95_latency < 2.0  # P95 < 2s

def test_concurrent_validation(client):
    """Testa a validação concorrente de CNPJ."""
    num_requests = 200
    latencies = []
    
    def validate_cnpj():
        start_time = time.time()
        response = client.post(
            "/api/v1/validate/cnpj",
            json={"cnpj": "12.345.678/0001-90"}
        )
        end_time = time.time()
        latencies.append(end_time - start_time)
        return response.status_code == 200
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _: validate_cnpj(), range(num_requests)))
    
    success_rate = sum(1 for r in results if r) / num_requests
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95
    assert avg_latency < 0.5  # Latência média < 500ms
    assert p95_latency < 1.0  # P95 < 1s

def test_concurrent_scheduling(client):
    """Testa o agendamento concorrente de eventos."""
    num_requests = 50
    latencies = []
    
    def schedule_event():
        start_time = time.time()
        scheduled_time = (time.time() + 3600)  # 1 hora no futuro
        response = client.post(
            "/api/v1/scheduler/schedule",
            json={
                "event_type": "video_render",
                "scheduled_time": scheduled_time,
                "metadata": {
                    "video_id": str(time.time()),
                    "resolution": "1080p"
                }
            }
        )
        end_time = time.time()
        latencies.append(end_time - start_time)
        return response.status_code == 200
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: schedule_event(), range(num_requests)))
    
    success_rate = sum(1 for r in results if r) / num_requests
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95
    assert avg_latency < 0.5
    assert p95_latency < 1.0

def test_mixed_workload(client):
    """Testa uma carga mista de diferentes operações."""
    num_requests = 100  # Reduzindo o número de requisições
    latencies = []
    
    def mixed_operation(i):
        start_time = time.time()
        # Usando o índice para alternar entre operações de forma previsível
        if i % 3 == 0:
            response = client.post(
                "/api/v1/users",
                json={
                    "name": "Test User",
                    "email": f"test{i}@example.com",
                    "role_id": 1
                }
            )
        elif i % 3 == 1:
            response = client.post(
                "/api/v1/validate/cnpj",
                json={"cnpj": "12.345.678/0001-90"}
            )
        else:
            scheduled_time = (time.time() + 3600)
            response = client.post(
                "/api/v1/scheduler/schedule",
                json={
                    "event_type": "video_render",
                    "scheduled_time": scheduled_time,
                    "metadata": {
                        "video_id": str(i),
                        "resolution": "1080p"
                    }
                }
            )
        end_time = time.time()
        latencies.append(end_time - start_time)
        return response.status_code in [200, 201]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(mixed_operation, range(num_requests)))
    
    success_rate = sum(1 for r in results if r) / num_requests
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95
    assert avg_latency < 0.75  # Latência média < 750ms
    assert p95_latency < 1.5  # P95 < 1.5s

def test_sustained_load(client):
    """Testa uma carga sustentada por um período mais curto."""
    duration = 30  # 30 segundos ao invés de 5 minutos
    start_time = time.time()
    latencies = []
    success_count = 0
    total_requests = 0
    
    while time.time() - start_time < duration:
        operation_start = time.time()
        response = client.post(
            "/api/v1/users",
            json={
                "name": "Load Test User",
                "email": f"load{total_requests}@example.com",
                "role_id": 1
            }
        )
        operation_end = time.time()
        
        latencies.append(operation_end - operation_start)
        if response.status_code in [200, 201]:
            success_count += 1
        total_requests += 1
        
        # Pequena pausa para não sobrecarregar o sistema
        time.sleep(0.1)
    
    success_rate = success_count / total_requests
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95
    assert avg_latency < 0.5  # Latência média < 500ms
    assert p95_latency < 1.0  # P95 < 1s

def test_database_connection_pool(client):
    """Testa o pool de conexões do banco de dados sob carga."""
    num_connections = 50
    latencies = []
    
    def test_connection():
        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()
        latencies.append(end_time - start_time)
        return response.status_code == 200
    
    with ThreadPoolExecutor(max_workers=num_connections) as executor:
        results = list(executor.map(lambda _: test_connection(), range(num_connections)))
    
    success_rate = sum(1 for r in results if r) / num_connections
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95
    assert avg_latency < 0.2  # Latência média < 200ms
    assert p95_latency < 0.5  # P95 < 500ms

def test_cache_performance(client):
    """Testa o desempenho do cache sob carga."""
    num_requests = 1000
    latencies = []
    
    def test_cache():
        start_time = time.time()
        response = client.post(
            "/api/v1/validate/cnpj",
            json={"cnpj": "12.345.678/0001-90"}
        )
        end_time = time.time()
        latencies.append(end_time - start_time)
        return response.status_code == 200
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda _: test_cache(), range(num_requests)))
    
    success_rate = sum(1 for r in results if r) / num_requests
    avg_latency = statistics.mean(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]
    
    assert success_rate >= 0.95
    assert avg_latency < 0.1  # Latência média < 100ms
    assert p95_latency < 0.2  # P95 < 200ms 