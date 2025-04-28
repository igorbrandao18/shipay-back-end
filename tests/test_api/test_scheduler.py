from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.models.schemas import ScheduleEventRequest, ScheduleEventResponse, RenderEvent

client = TestClient(app)

@pytest.fixture
def mock_event_data():
    return {
        "event_id": "123",
        "content": {"video_id": "abc", "format": "mp4"},
        "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat(),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "processed_at": None
    }

def test_schedule_event_success(mock_event_data):
    with patch('app.services.scheduler.SchedulerService._store_event') as mock_store, \
         patch('app.services.scheduler.SchedulerService._process_pending_events') as mock_process:
        
        mock_store.return_value = mock_event_data
        mock_process.return_value = None
        
        request_data = {
            "content": {"video_id": "abc", "format": "mp4"},
            "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        
        response = client.post("/api/v1/scheduler/schedule", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scheduled"
        assert "event_id" in data

def test_schedule_event_past_date():
    request_data = {
        "content": {"video_id": "abc", "format": "mp4"},
        "scheduled_time": (datetime.now() - timedelta(hours=1)).isoformat()
    }
    
    response = client.post("/api/v1/scheduler/schedule", json=request_data)
    assert response.status_code == 400
    assert "A data agendada deve ser futura" in response.json()["detail"]

def test_get_event_status_success(mock_event_data):
    with patch('app.services.scheduler.SchedulerService.get_event_status') as mock_get_status:
        mock_get_status.return_value = RenderEvent(
            event_id=mock_event_data["event_id"],
            content=mock_event_data["content"],
            scheduled_time=datetime.fromisoformat(mock_event_data["scheduled_time"]),
            status=mock_event_data["status"],
            created_at=datetime.fromisoformat(mock_event_data["created_at"]),
            processed_at=None
        )
        
        response = client.get(f"/api/v1/scheduler/status/{mock_event_data['event_id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == mock_event_data["event_id"]
        assert data["status"] == mock_event_data["status"]

def test_get_event_status_not_found():
    with patch('app.services.scheduler.SchedulerService.get_event_status') as mock_get_status:
        mock_get_status.side_effect = HTTPException(status_code=404, detail="Evento não encontrado")
        
        response = client.get("/api/v1/scheduler/status/nonexistent")
        assert response.status_code == 404
        assert "Evento não encontrado" in response.json()["detail"]

def test_process_pending_events(mock_event_data):
    with patch('app.services.scheduler.SchedulerService._process_pending_events') as mock_process:
        mock_process.return_value = None
        
        # Simula eventos pendentes
        events = [
            {**mock_event_data, "status": "pending"},
            {**mock_event_data, "status": "completed"}
        ]
        
        # Processa os eventos
        for event in events:
            if event["status"] == "pending":
                response = client.post("/api/v1/scheduler/process")
                assert response.status_code == 200
                assert response.json()["message"] == "Eventos processados com sucesso"

def test_event_metrics():
    with patch('app.services.scheduler.SchedulerService._store_event') as mock_store, \
         patch('app.services.scheduler.SchedulerService._process_pending_events') as mock_process:
        
        mock_store.return_value = mock_event_data
        mock_process.return_value = None
        
        # Agenda vários eventos
        for _ in range(10):
            request_data = {
                "content": {"video_id": "abc", "format": "mp4"},
                "scheduled_time": (datetime.now() + timedelta(hours=1)).isoformat()
            }
            response = client.post("/api/v1/scheduler/schedule", json=request_data)
            assert response.status_code == 200
        
        # Verifica métricas
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text
        assert "scheduled_events_total 10" in metrics 