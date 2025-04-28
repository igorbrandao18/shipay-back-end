import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import CustomerValidationRequest

client = TestClient(app)

def test_validate_customer_success():
    # Dados de teste
    request_data = {
        "cnpj": "12345678000190",
        "cep": "01311000"
    }
    
    response = client.post("/api/v1/customer/validate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["address_match"] is True
    assert "company_info" in data
    assert "details" in data

def test_validate_customer_invalid_cnpj():
    request_data = {
        "cnpj": "123",  # CNPJ inválido
        "cep": "01311000"
    }
    
    response = client.post("/api/v1/customer/validate", json=request_data)
    
    assert response.status_code == 422  # Erro de validação

def test_validate_customer_invalid_cep():
    request_data = {
        "cnpj": "12345678000190",
        "cep": "123"  # CEP inválido
    }
    
    response = client.post("/api/v1/customer/validate", json=request_data)
    
    assert response.status_code == 422  # Erro de validação

def test_validate_customer_address_mismatch():
    # Dados de teste com endereços que não correspondem
    request_data = {
        "cnpj": "12345678000190",
        "cep": "20040000"  # CEP diferente do cadastro da empresa
    }
    
    response = client.post("/api/v1/customer/validate", json=request_data)
    
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Endereço não corresponde" in data["detail"] 