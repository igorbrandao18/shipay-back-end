import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.core.database import SessionLocal
from app.services.validation import ValidationService
from app.services.scheduler import SchedulerService
from datetime import datetime, timedelta

@pytest.fixture
def client():
    """Cria um cliente de teste para a API."""
    return TestClient(app)

@pytest.fixture
def db_session():
    """Cria uma sessão do banco de dados para testes."""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def validation_service():
    """Cria uma instância do serviço de validação."""
    return ValidationService()

@pytest.fixture
def scheduler_service():
    """Cria uma instância do serviço de agendamento."""
    return SchedulerService()

def test_user_creation_flow(client, db_session):
    """Testa o fluxo completo de criação de usuário."""
    # Criar usuário
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "role_id": 1
        }
    )
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # Verificar usuário criado
    user = db_session.query(User).filter_by(id=user_id).first()
    assert user is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"

def test_validation_flow(client, validation_service):
    """Testa o fluxo completo de validação de CNPJ e CEP."""
    # Validar CNPJ
    cnpj_response = client.post(
        "/api/v1/validate/cnpj",
        json={"cnpj": "12.345.678/0001-90"}
    )
    assert cnpj_response.status_code == 200
    
    # Validar CEP
    cep_response = client.post(
        "/api/v1/validate/cep",
        json={"cep": "12345-678"}
    )
    assert cep_response.status_code == 200

def test_scheduler_flow(client, scheduler_service):
    """Testa o fluxo completo de agendamento de eventos."""
    # Agendar evento
    scheduled_time = (datetime.now() + timedelta(hours=1)).isoformat()
    schedule_response = client.post(
        "/api/v1/scheduler/schedule",
        json={
            "event_type": "video_render",
            "scheduled_time": scheduled_time,
            "metadata": {
                "video_id": "123",
                "resolution": "1080p"
            }
        }
    )
    assert schedule_response.status_code == 200
    event_id = schedule_response.json()["event_id"]
    
    # Verificar status do evento
    status_response = client.get(f"/api/v1/scheduler/status/{event_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "scheduled"

def test_report_flow(client, db_session):
    """Testa o fluxo completo de geração de relatórios."""
    # Criar dados de teste
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    end_date = datetime.now().isoformat()
    
    # Gerar relatório
    report_response = client.get(
        "/api/v1/reports/launches",
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )
    assert report_response.status_code == 200
    assert "data" in report_response.json()
    assert "statistics" in report_response.json()

def test_error_handling_flow(client):
    """Testa o fluxo de tratamento de erros."""
    # Tentar criar usuário com email inválido
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Test User",
            "email": "invalid_email",
            "role_id": 1
        }
    )
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()
    
    # Tentar validar CNPJ inválido
    response = client.post(
        "/api/v1/validate/cnpj",
        json={"cnpj": "invalid_cnpj"}
    )
    assert response.status_code == 400
    assert "cnpj" in response.json()["detail"].lower()
    
    # Tentar agendar evento no passado
    past_time = (datetime.now() - timedelta(hours=1)).isoformat()
    response = client.post(
        "/api/v1/scheduler/schedule",
        json={
            "event_type": "video_render",
            "scheduled_time": past_time,
            "metadata": {}
        }
    )
    assert response.status_code == 400
    assert "past" in response.json()["detail"].lower()

def test_authentication_flow(client):
    """Testa o fluxo completo de autenticação."""
    # Criar usuário
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "role_id": 1
        }
    )
    assert response.status_code == 201
    
    # Obter token
    auth_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "generated_password"
        }
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]
    
    # Acessar recurso protegido
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_rate_limiting_flow(client):
    """Testa o fluxo de rate limiting."""
    # Fazer múltiplas requisições em sequência
    for _ in range(100):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    # A próxima requisição deve ser bloqueada
    response = client.get("/api/v1/health")
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()

def test_cache_flow(client, validation_service):
    """Testa o fluxo de cache."""
    cnpj = "12.345.678/0001-90"
    
    # Primeira chamada (sem cache)
    response1 = client.post(
        "/api/v1/validate/cnpj",
        json={"cnpj": cnpj}
    )
    assert response1.status_code == 200
    
    # Segunda chamada (com cache)
    response2 = client.post(
        "/api/v1/validate/cnpj",
        json={"cnpj": cnpj}
    )
    assert response2.status_code == 200
    
    # Verificar se o cache foi usado
    assert response1.json() == response2.json()

def test_metrics_flow(client):
    """Testa o fluxo de métricas."""
    # Acessar endpoint de métricas
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Verificar se as métricas estão presentes
    metrics = response.text
    assert "http_requests_total" in metrics
    assert "http_request_duration_seconds" in metrics
    assert "validation_requests_total" in metrics 