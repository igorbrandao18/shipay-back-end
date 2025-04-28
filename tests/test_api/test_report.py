from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.models.schemas import LaunchReportRequest, LaunchReport, RocketLaunch

client = TestClient(app)

@pytest.fixture
def mock_launch_data():
    return [
        {
            "customer_id": "123",
            "launch_date": datetime.now(),
            "status": "success",
            "pre_flight_status": "ok",
            "countdown_status": "completed",
            "trace_id": "abc123",
            "created_at": datetime.now() - timedelta(minutes=5)
        },
        {
            "customer_id": "123",
            "launch_date": datetime.now() - timedelta(days=1),
            "status": "failed",
            "pre_flight_status": "error",
            "countdown_status": "aborted",
            "trace_id": "def456",
            "created_at": datetime.now() - timedelta(days=1, minutes=5)
        }
    ]

def test_generate_report_success(mock_launch_data):
    with patch('app.services.report.ReportService._get_launches_for_period') as mock_get_launches:
        mock_get_launches.return_value = mock_launch_data
        
        request_data = {
            "customer_id": "123",
            "period_start": datetime.now() - timedelta(days=30),
            "period_end": datetime.now()
        }
        
        response = client.post("/api/v1/report/launches", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["customer_id"] == request_data["customer_id"]
        assert data["total_launches"] == 2
        assert data["successful_launches"] == 1
        assert data["failed_launches"] == 1
        assert len(data["launches"]) == 2
        assert data["launches"][0]["trace_id"] == mock_launch_data[0]["trace_id"]
        assert data["launches"][1]["trace_id"] == mock_launch_data[1]["trace_id"]

def test_generate_report_period_too_long():
    request_data = {
        "customer_id": "123",
        "period_start": datetime.now() - timedelta(days=31),
        "period_end": datetime.now()
    }
    
    response = client.post("/api/v1/report/launches", json=request_data)
    assert response.status_code == 400
    assert "O período máximo para o relatório é de 30 dias" in response.json()["detail"]

def test_generate_report_no_launches():
    with patch('app.services.report.ReportService._get_launches_for_period') as mock_get_launches:
        mock_get_launches.return_value = []
        
        request_data = {
            "customer_id": "123",
            "period_start": datetime.now() - timedelta(days=30),
            "period_end": datetime.now()
        }
        
        response = client.post("/api/v1/report/launches", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_launches"] == 0
        assert data["successful_launches"] == 0
        assert data["failed_launches"] == 0
        assert len(data["launches"]) == 0

def test_generate_report_database_error():
    with patch('app.services.report.ReportService._get_launches_for_period') as mock_get_launches:
        mock_get_launches.side_effect = Exception("Database error")
        
        request_data = {
            "customer_id": "123",
            "period_start": datetime.now() - timedelta(days=30),
            "period_end": datetime.now()
        }
        
        response = client.post("/api/v1/report/launches", json=request_data)
        assert response.status_code == 500
        assert "Erro ao gerar relatório" in response.json()["detail"] 