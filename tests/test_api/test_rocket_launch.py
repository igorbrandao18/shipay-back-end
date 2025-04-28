import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import LaunchReportRequest
from sqlalchemy.orm import Session
from app.models.rocket_launch import RocketLaunch
from app.models.user import User
from app.models.schemas import RocketLaunchCreate
from app.db.session import get_db
from app.db.base_class import Base
from app.db.session import engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Cria todas as tabelas
    Base.metadata.create_all(bind=engine)
    yield
    # Limpa o banco após os testes
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def mock_user(db):
    user = User(
        name="Test User",
        email="test@example.com",
        password="hashed_password",
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def mock_launch_data(mock_user):
    return {
        "launch_id": "test-launch-1",
        "name": "Test Launch",
        "status": "success",
        "launch_date": datetime.utcnow().isoformat(),
        "rocket_name": "Falcon 9",
        "rocket_type": "Falcon",
        "launch_site": "Cape Canaveral",
        "mission_name": "Test Mission",
        "mission_details": {"test": "details"},
        "payload_mass": 1000.0,
        "orbit": "LEO",
        "user_id": mock_user.id
    }

def test_generate_report_success():
    # Dados de teste
    request_data = {
        "customer_id": "customer123",
        "period_start": (datetime.now() - timedelta(days=7)).isoformat(),
        "period_end": datetime.now().isoformat()
    }
    
    response = client.post("/api/v1/rocket/report", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "customer_id" in data
    assert "period_start" in data
    assert "period_end" in data
    assert "total_launches" in data
    assert "successful_launches" in data
    assert "failed_launches" in data
    assert "launches" in data

def test_generate_report_invalid_period():
    # Período inválido (data final anterior à data inicial)
    request_data = {
        "customer_id": "customer123",
        "period_start": datetime.now().isoformat(),
        "period_end": (datetime.now() - timedelta(days=1)).isoformat()
    }
    
    response = client.post("/api/v1/rocket/report", json=request_data)
    
    assert response.status_code == 400
    assert "A data final deve ser posterior à data inicial" in response.json()["detail"]

def test_generate_report_period_too_long():
    # Período maior que 30 dias
    request_data = {
        "customer_id": "customer123",
        "period_start": (datetime.now() - timedelta(days=31)).isoformat(),
        "period_end": datetime.now().isoformat()
    }
    
    response = client.post("/api/v1/rocket/report", json=request_data)
    
    assert response.status_code == 400
    assert "O período máximo permitido é de 30 dias" in response.json()["detail"]

def test_generate_report_missing_customer():
    # Cliente não encontrado
    request_data = {
        "customer_id": "non_existent_customer",
        "period_start": (datetime.now() - timedelta(days=7)).isoformat(),
        "period_end": datetime.now().isoformat()
    }
    
    response = client.post("/api/v1/rocket/report", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_launches"] == 0
    assert data["successful_launches"] == 0
    assert data["failed_launches"] == 0
    assert len(data["launches"]) == 0

def test_create_launch_success(db, mock_launch_data):
    response = client.post("/api/v1/rocket-launches/", json=mock_launch_data)
    assert response.status_code == 201
    data = response.json()
    assert data["launch_id"] == mock_launch_data["launch_id"]
    assert data["name"] == mock_launch_data["name"]
    assert data["status"] == mock_launch_data["status"]

def test_create_launch_duplicate(db, mock_launch_data):
    # Cria primeiro lançamento
    client.post("/api/v1/rocket-launches/", json=mock_launch_data)
    
    # Tenta criar segundo lançamento com mesmo ID
    response = client.post("/api/v1/rocket-launches/", json=mock_launch_data)
    assert response.status_code == 400
    assert "Lançamento já registrado" in response.json()["detail"]

def test_get_launch_success(db, mock_launch_data):
    # Cria lançamento
    create_response = client.post("/api/v1/rocket-launches/", json=mock_launch_data)
    launch_id = create_response.json()["launch_id"]
    
    # Busca lançamento
    response = client.get(f"/api/v1/rocket-launches/{launch_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["launch_id"] == launch_id
    assert data["name"] == mock_launch_data["name"]

def test_get_launch_not_found():
    response = client.get("/api/v1/rocket-launches/non-existent")
    assert response.status_code == 404
    assert "Lançamento não encontrado" in response.json()["detail"]

def test_get_launches_by_period(db, mock_launch_data, mock_user):
    # Cria alguns lançamentos
    for i in range(3):
        launch_data = mock_launch_data.copy()
        launch_data["launch_id"] = f"test-launch-{i}"
        launch_data["launch_date"] = (datetime.utcnow() - timedelta(days=i)).isoformat()
        client.post("/api/v1/rocket-launches/", json=launch_data)
    
    # Busca lançamentos do último mês
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    response = client.get(
        "/api/v1/rocket-launches/period/",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "user_id": mock_user.id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_get_launch_statistics(db, mock_launch_data, mock_user):
    # Cria lançamentos com diferentes status
    launch_data = mock_launch_data.copy()
    launch_data["status"] = "success"
    client.post("/api/v1/rocket-launches/", json=launch_data)
    
    launch_data["launch_id"] = "test-launch-2"
    launch_data["status"] = "failure"
    client.post("/api/v1/rocket-launches/", json=launch_data)
    
    # Busca estatísticas
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    response = client.get(
        "/api/v1/rocket-launches/statistics/",
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "user_id": mock_user.id
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_launches"] == 2
    assert data["successful_launches"] == 1
    assert data["failed_launches"] == 1
    assert data["success_rate"] == 50.0
    assert "Falcon" in data["rocket_types"] 