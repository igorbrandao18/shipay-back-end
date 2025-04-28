import pytest
import requests
import httpx
from unittest.mock import patch
from app.services.validation import ValidationService
from app.core.config import settings

@pytest.fixture
def validation_service():
    """Cria uma instância do serviço de validação."""
    return ValidationService()

@pytest.mark.asyncio
async def test_cnpj_validation_success(validation_service):
    """Testa a validação de CNPJ com sucesso."""
    cnpj = "12.345.678/0001-90"

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "status": "active",
            "name": "Test Company"
        }

        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is True
        assert info.name == "Test Company"
        assert error is None

@pytest.mark.asyncio
async def test_cnpj_validation_failure(validation_service):
    """Testa a validação de CNPJ com falha."""
    cnpj = "12.345.678/0001-90"

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.status_code = 404
        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is False
        assert info is None
        assert error == "CNPJ inválido"

@pytest.mark.asyncio
async def test_cnpj_validation_retry(validation_service):
    """Testa o mecanismo de retry na validação de CNPJ."""
    cnpj = "12.345.678/0001-90"
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = [
            httpx.ConnectError(),
            httpx.TimeoutException(),
            httpx.Response(200, json={
                "status": "active",
                "name": "Test Company"
            })
        ]
        
        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is True
        assert info.name == "Test Company"
        assert error is None

@pytest.mark.asyncio
async def test_cep_validation_success(validation_service):
    """Testa a validação de CEP com sucesso."""
    cep = "12345-678"

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "cep": "12345-678",
            "logradouro": "Test Street",
            "bairro": "Test Neighborhood",
            "localidade": "Test City",
            "uf": "TS"
        }

        valid, info, error = await validation_service.validate_cep(cep)
        assert valid is True
        assert info.cep == "12345-678"
        assert error is None

@pytest.mark.asyncio
async def test_cep_validation_failure(validation_service):
    """Testa a validação de CEP com falha."""
    cep = "00000-000"

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.status_code = 404
        valid, info, error = await validation_service.validate_cep(cep)
        assert valid is False
        assert info is None
        assert error == "CEP inválido"

@pytest.mark.asyncio
async def test_cep_validation_retry(validation_service):
    """Testa o mecanismo de retry na validação de CEP."""
    cep = "12345-678"
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = [
            httpx.ConnectError(),
            httpx.TimeoutException(),
            httpx.Response(200, json={
                "cep": "12345-678",
                "logradouro": "Test Street",
                "bairro": "Test Neighborhood",
                "localidade": "Test City",
                "uf": "TS"
            })
        ]
        
        valid, info, error = await validation_service.validate_cep(cep)
        assert valid is True
        assert info.cep == "12345-678"
        assert error is None

@pytest.mark.asyncio
async def test_api_fallback(validation_service):
    """Testa o fallback para APIs alternativas."""
    cnpj = "12.345.678/0001-90"
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json={
                "status": "active",
                "name": "Test Company"
            })
        ]
        
        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is True
        assert info.name == "Test Company"
        assert error is None

@pytest.mark.asyncio
async def test_rate_limiting(validation_service):
    """Testa o rate limiting nas chamadas à API."""
    cnpj = "12.345.678/0001-90"
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = httpx.Response(429, headers={"Retry-After": "1"})
        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is False
        assert info is None
        assert error is not None

@pytest.mark.asyncio
async def test_timeout_handling(validation_service):
    """Testa o tratamento de timeouts nas chamadas à API."""
    cnpj = "12.345.678/0001-90"
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.side_effect = httpx.TimeoutException()
        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is False
        assert info is None
        assert error is not None

@pytest.mark.asyncio
async def test_invalid_response(validation_service):
    """Testa o tratamento de respostas inválidas da API."""
    cnpj = "12.345.678/0001-90"
    
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = httpx.Response(200, json={"invalid": "data"})
        valid, info, error = await validation_service.validate_cnpj(cnpj)
        assert valid is False
        assert info is None
        assert error is not None

@pytest.mark.asyncio
async def test_validate_both_success(validation_service):
    """Testa a validação de CNPJ e CEP com sucesso."""
    cnpj = "12.345.678/0001-90"
    cep = "12345-678"

    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [
            {
                "status": "active",
                "name": "Test Company"
            },
            {
                "cep": "12345-678",
                "logradouro": "Test Street",
                "bairro": "Test Neighborhood",
                "localidade": "Test City",
                "uf": "TS"
            }
        ]

        result = await validation_service.validate_both(cnpj, cep)
        assert result["cnpj_valid"] is True
        assert result["cep_valid"] is True
        assert result["cnpj_details"].name == "Test Company"
        assert result["cep_details"].cep == "12345-678"
        assert result["error"] is None 