from fastapi.testclient import TestClient
from app.main import app
import pytest
from unittest.mock import patch, MagicMock
from app.models.schemas import CustomerValidationRequest, CustomerValidationResponse, CompanyInfo, Address, ValidationRequest, ValidationResponse

client = TestClient(app)

@pytest.fixture
def mock_company_data():
    return {
        "cnpj": "12345678000190",
        "razao_social": "Empresa Teste LTDA",
        "nome_fantasia": "Empresa Teste",
        "endereco": {
            "cep": "12345678",
            "logradouro": "Rua Teste",
            "complemento": "Sala 1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP"
        }
    }

@pytest.fixture
def mock_cep_data():
    return {
        "cep": "12345678",
        "logradouro": "Rua Teste",
        "complemento": "Sala 1",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "uf": "SP"
    }

@pytest.fixture
def mock_cnpj_data():
    return {
        "logradouro": "Rua Teste",
        "cidade": "São Paulo",
        "uf": "SP"
    }

def test_validate_customer_success(mock_company_data, mock_cep_data):
    with patch('app.services.validation.ValidationService._fetch_company_info') as mock_fetch_company, \
         patch('app.services.validation.ValidationService._try_cep_providers') as mock_fetch_cep:
        
        mock_fetch_company.return_value = mock_company_data
        mock_fetch_cep.return_value = mock_cep_data
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["address_match"] is True
        assert data["company_info"]["cnpj"] == mock_company_data["cnpj"]
        assert data["company_info"]["razao_social"] == mock_company_data["razao_social"]

def test_validate_customer_address_mismatch(mock_company_data, mock_cep_data):
    with patch('app.services.validation.ValidationService._fetch_company_info') as mock_fetch_company, \
         patch('app.services.validation.ValidationService._try_cep_providers') as mock_fetch_cep:
        
        mock_company_data["endereco"]["cidade"] = "Rio de Janeiro"
        mock_fetch_company.return_value = mock_company_data
        mock_fetch_cep.return_value = mock_cep_data
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert data["address_match"] is False

def test_validate_customer_primary_cep_failure(mock_company_data, mock_cep_data):
    with patch('app.services.validation.ValidationService._fetch_company_info') as mock_fetch_company, \
         patch('app.services.validation.ValidationService._fetch_address_by_cep') as mock_fetch_cep:
        
        mock_fetch_company.return_value = mock_company_data
        # Simula falha no provedor primário
        mock_fetch_cep.side_effect = [
            Exception("Primary provider failed"),
            mock_cep_data  # Sucesso no provedor secundário
        ]
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["address_match"] is True

def test_validate_customer_all_cep_providers_fail(mock_company_data):
    with patch('app.services.validation.ValidationService._fetch_company_info') as mock_fetch_company, \
         patch('app.services.validation.ValidationService._fetch_address_by_cep') as mock_fetch_cep:
        
        mock_fetch_company.return_value = mock_company_data
        # Simula falha em ambos os provedores
        mock_fetch_cep.side_effect = Exception("All providers failed")
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 500
        assert "Todos os provedores de CEP falharam" in response.json()["detail"]

def test_validate_customer_invalid_cnpj():
    request_data = {
        "cnpj": "123",  # CNPJ inválido
        "cep": "12345678"
    }
    
    response = client.post("/api/v1/validation/validate", json=request_data)
    assert response.status_code == 422  # Erro de validação do Pydantic

def test_validate_customer_invalid_cep():
    request_data = {
        "cnpj": "12345678000190",
        "cep": "123"  # CEP inválido
    }
    
    response = client.post("/api/v1/validation/validate", json=request_data)
    assert response.status_code == 422  # Erro de validação do Pydantic

def test_validate_address_success(mock_cnpj_data, mock_cep_data):
    with patch('app.services.validation.ValidationService._get_cnpj_info') as mock_cnpj, \
         patch('app.services.validation.ValidationService._get_cep_info') as mock_cep:
        
        mock_cnpj.return_value = mock_cnpj_data
        mock_cep.return_value = mock_cep_data
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert "validado com sucesso" in data["message"]

def test_validate_address_mismatch(mock_cnpj_data, mock_cep_data):
    with patch('app.services.validation.ValidationService._get_cnpj_info') as mock_cnpj, \
         patch('app.services.validation.ValidationService._get_cep_info') as mock_cep:
        
        mock_cnpj.return_value = mock_cnpj_data
        mock_cep.return_value = {
            "logradouro": "Rua Diferente",
            "cidade": "Rio de Janeiro",
            "uf": "RJ"
        }
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 404
        assert "não corresponde" in response.json()["detail"]

def test_validate_address_api_error():
    with patch('app.services.validation.ValidationService._get_cnpj_info') as mock_cnpj:
        mock_cnpj.side_effect = Exception("API Error")
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 500
        assert "Erro na validação" in response.json()["detail"]

def test_validation_metrics(mock_cnpj_data, mock_cep_data):
    with patch('app.services.validation.ValidationService._get_cnpj_info') as mock_cnpj, \
         patch('app.services.validation.ValidationService._get_cep_info') as mock_cep:
        
        mock_cnpj.return_value = mock_cnpj_data
        mock_cep.return_value = mock_cep_data
        
        # Faz várias requisições
        for _ in range(10):
            request_data = {
                "cnpj": "12345678000190",
                "cep": "12345678"
            }
            response = client.post("/api/v1/validation/validate", json=request_data)
            assert response.status_code == 200
        
        # Verifica métricas
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text
        assert "validation_requests_total 10" in metrics 

def test_validate_customer_api_error():
    with patch('app.services.validation.ValidationService._fetch_company_info') as mock_fetch_company:
        mock_fetch_company.side_effect = Exception("API Error")
        
        request_data = {
            "cnpj": "12345678000190",
            "cep": "12345678"
        }
        
        response = client.post("/api/v1/validation/validate", json=request_data)
        assert response.status_code == 500
        assert "API Error" in response.json()["detail"]

def test_validation_metrics():
    with patch('app.services.validation.ValidationService._fetch_company_info') as mock_fetch_company, \
         patch('app.services.validation.ValidationService._try_cep_providers') as mock_fetch_cep:
        
        mock_company_data = {
            "cnpj": "12345678000190",
            "razao_social": "Empresa Teste LTDA",
            "nome_fantasia": "Empresa Teste",
            "endereco": {
                "cep": "12345678",
                "logradouro": "Rua Teste",
                "complemento": "Sala 1",
                "bairro": "Centro",
                "cidade": "São Paulo",
                "uf": "SP"
            }
        }
        
        mock_cep_data = {
            "cep": "12345678",
            "logradouro": "Rua Teste",
            "complemento": "Sala 1",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP"
        }
        
        mock_fetch_company.return_value = mock_company_data
        mock_fetch_cep.return_value = mock_cep_data
        
        # Make multiple requests
        for _ in range(5):
            response = client.post("/api/v1/validation/validate", json={
                "cnpj": "12345678000190",
                "cep": "12345678"
            })
            assert response.status_code == 200
            
        # Check metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.text
        assert "validation_requests_total 5.0" in metrics 