import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import ScheduleEventRequest

client = TestClient(app)

def test_schedule_event_success():
    # Dados de teste
    request_data = {
        "content": {"video_id": "123", "format": "mp4"},
        "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat()
    }
    
    response = client.post("/api/v1/render/schedule", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert "scheduled_time" in data
    assert "status" in data
    assert data["status"] == "pending"

def test_schedule_event_past_date():
    # Data no passado
    request_data = {
        "content": {"video_id": "123", "format": "mp4"},
        "scheduled_time": (datetime.now() - timedelta(hours=1)).isoformat()
    }
    
    response = client.post("/api/v1/render/schedule", json=request_data)
    
    assert response.status_code == 422
    assert "A data agendada deve ser futura" in response.json()["detail"]

def test_get_event_status_success():
    # Primeiro agenda um evento
    request_data = {
        "content": {"video_id": "123", "format": "mp4"},
        "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat()
    }
    
    schedule_response = client.post("/api/v1/render/schedule", json=request_data)
    event_id = schedule_response.json()["event_id"]
    
    # Depois consulta o status
    response = client.get(f"/api/v1/render/status/{event_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == event_id
    assert data["status"] == "pending"

def test_get_event_status_not_found():
    # Tenta consultar um evento que não existe
    response = client.get("/api/v1/render/status/non_existent_event")
    
    assert response.status_code == 404
    assert "Evento não encontrado" in response.json()["detail"] 