from fastapi.testclient import TestClient
from app.main import app
import pytest
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.schemas import UserCreate, UserRole
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
def mock_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "test123",
        "role": UserRole.USER
    }

def test_create_user_success(db, mock_user_data):
    response = client.post("/api/v1/users/", json=mock_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == mock_user_data["name"]
    assert data["email"] == mock_user_data["email"]
    assert data["role"] == mock_user_data["role"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_user_duplicate_email(db, mock_user_data):
    # Cria primeiro usuário
    client.post("/api/v1/users/", json=mock_user_data)
    
    # Tenta criar segundo usuário com mesmo email
    response = client.post("/api/v1/users/", json=mock_user_data)
    assert response.status_code == 400
    assert "Email já registrado" in response.json()["detail"]

def test_get_user_success(db, mock_user_data):
    # Cria usuário
    create_response = client.post("/api/v1/users/", json=mock_user_data)
    user_id = create_response.json()["id"]
    
    # Busca usuário
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == mock_user_data["name"]
    assert data["email"] == mock_user_data["email"]

def test_get_user_not_found():
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404
    assert "Usuário não encontrado" in response.json()["detail"]

def test_update_user_success(db, mock_user_data):
    # Cria usuário
    create_response = client.post("/api/v1/users/", json=mock_user_data)
    user_id = create_response.json()["id"]
    
    # Atualiza usuário
    update_data = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "password": "newpassword",
        "role": UserRole.ADMIN
    }
    response = client.put(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["email"] == update_data["email"]
    assert data["role"] == update_data["role"]

def test_delete_user_success(db, mock_user_data):
    # Cria usuário
    create_response = client.post("/api/v1/users/", json=mock_user_data)
    user_id = create_response.json()["id"]
    
    # Remove usuário
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204
    
    # Verifica se foi removido
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404

def test_user_metrics(db, mock_user_data):
    # Cria vários usuários
    for i in range(5):
        user_data = mock_user_data.copy()
        user_data["email"] = f"test{i}@example.com"
        client.post("/api/v1/users/", json=user_data)
    
    # Verifica métricas
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.text
    assert "users_created_total 5" in metrics 