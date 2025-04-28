from typing import Dict, Optional, Any
import httpx
from fastapi import HTTPException
from app.core.config import get_settings
import asyncio
from datetime import datetime
from app.core.metrics import metrics
from app.models.schemas import CustomerValidationRequest, CustomerValidationResponse, CompanyInfo, Address
import time
from tenacity import retry, stop_after_attempt, wait_exponential

settings = get_settings()

class ValidationService:
    def __init__(self):
        self.max_retries = settings.MAX_RETRIES
        self.retry_delay = settings.RETRY_DELAY
        self.cnpj_api_url = settings.CNPJ_API_URL
        self.cep_api_url = settings.CEP_API_URL
        self.timeout = 10.0
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _make_request(self, url: str, params: Dict) -> Dict:
        """Faz uma requisição HTTP com retentativas"""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao consultar API: {str(e)}"
                    )
                await asyncio.sleep(self.retry_delay)

    async def _get_cnpj_info(self, cnpj: str) -> Dict:
        """Consulta informações do CNPJ"""
        try:
            start_time = time.time()
            data = await self._make_request(
                self.cnpj_api_url,
                {"cnpj": cnpj}
            )
            duration = time.time() - start_time
            metrics.observe_request_latency("cnpj_validation", duration)
            metrics.inc_validation_attempt("cnpj")
            return data
        except Exception as e:
            metrics.inc_validation_error("cnpj", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao consultar CNPJ: {str(e)}"
            )

    async def _get_cep_info(self, cep: str) -> Dict:
        """Consulta informações do CEP com fallback para provedor secundário"""
        for api_url in [self.cep_api_url]:
            try:
                start_time = time.time()
                data = await self._make_request(
                    api_url,
                    {"cep": cep}
                )
                duration = time.time() - start_time
                metrics.observe_request_latency("cep_validation", duration)
                metrics.inc_validation_attempt("cep")
                return data
            except Exception as e:
                if api_url == self.cep_api_url:
                    metrics.inc_validation_error("cep", type(e).__name__)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao consultar CEP: {str(e)}"
                    )
                continue

    def _normalize_address(self, address: str) -> str:
        """Normaliza o endereço para comparação"""
        return (
            address.lower()
            .replace(" ", "")
            .replace(".", "")
            .replace(",", "")
            .replace("-", "")
        )

    def _compare_addresses(self, cnpj_address: Dict, cep_address: Dict) -> bool:
        """Compara os endereços obtidos do CNPJ e CEP"""
        cnpj_normalized = self._normalize_address(
            f"{cnpj_address.get('logradouro', '')} "
            f"{cnpj_address.get('cidade', '')} "
            f"{cnpj_address.get('uf', '')}"
        )
        
        cep_normalized = self._normalize_address(
            f"{cep_address.get('logradouro', '')} "
            f"{cep_address.get('cidade', '')} "
            f"{cep_address.get('uf', '')}"
        )
        
        return cnpj_normalized == cep_normalized

    async def validate_address(self, cnpj: str, cep: str) -> bool:
        """Valida se o endereço do CNPJ corresponde ao CEP informado"""
        try:
            cnpj_info = await self._get_cnpj_info(cnpj)
            cep_info = await self._get_cep_info(cep)
            
            return self._compare_addresses(cnpj_info, cep_info)
        except Exception as e:
            metrics.inc_api_error("validation", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Erro na validação: {str(e)}"
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_company_info(self, cnpj: str) -> Dict[str, Any]:
        """Busca informações da empresa pelo CNPJ com retentativas"""
        try:
            response = await self.client.get(f"{self.cnpj_api_url}/{cnpj}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Erro ao consultar CNPJ: {str(e)}")

    async def _try_cep_providers(self, cep: str) -> Dict[str, Any]:
        """Tenta buscar o endereço em ambos os provedores de CEP"""
        try:
            response = await self.client.get(f"{self.cep_api_url}/{cep}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Erro ao consultar CEP: {str(e)}")

    def _compare_addresses(self, company_address: Dict[str, Any], cep_address: Dict[str, Any]) -> bool:
        """Compara os endereços retornados pelas APIs"""
        return (
            company_address.get("uf", "").lower() == cep_address.get("uf", "").lower() and
            company_address.get("cidade", "").lower() == cep_address.get("cidade", "").lower() and
            company_address.get("logradouro", "").lower() in cep_address.get("logradouro", "").lower()
        )

    async def validate_customer(self, request: CustomerValidationRequest) -> CustomerValidationResponse:
        """Valida o cadastro do cliente comparando CNPJ e CEP"""
        try:
            start_time = time.time()
            
            # Busca informações da empresa
            company_data = await self._fetch_company_info(request.cnpj)
            
            # Busca endereço pelo CEP
            cep_data = await self._try_cep_providers(request.cep)
            
            # Compara os endereços
            address_match = self._compare_addresses(
                company_data.get("endereco", {}),
                cep_data
            )
            
            duration = time.time() - start_time
            metrics.observe_request_latency("customer_validation", duration)
            
            # Constrói a resposta
            company_info = CompanyInfo(
                cnpj=company_data.get("cnpj"),
                razao_social=company_data.get("razao_social"),
                nome_fantasia=company_data.get("nome_fantasia"),
                endereco=Address(
                    cep=company_data.get("endereco", {}).get("cep"),
                    logradouro=company_data.get("endereco", {}).get("logradouro"),
                    complemento=company_data.get("endereco", {}).get("complemento"),
                    bairro=company_data.get("endereco", {}).get("bairro"),
                    cidade=company_data.get("endereco", {}).get("cidade"),
                    uf=company_data.get("endereco", {}).get("uf")
                )
            )
            
            return CustomerValidationResponse(
                is_valid=address_match,
                company_info=company_info,
                address_match=address_match,
                details="Endereço validado com sucesso" if address_match else "Endereço não corresponde"
            )
                
        except HTTPException:
            raise
        except Exception as e:
            metrics.inc_api_error("validation", type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    async def get_validation_by_id(self, validation_id: int) -> Optional[CustomerValidationResponse]:
        """Busca uma validação pelo ID"""
        # This is a placeholder. In a real implementation, this would fetch from a database
        raise HTTPException(status_code=501, detail="Not implemented")

    async def validate_cnpj(self, cnpj: str) -> tuple[bool, Optional[CompanyInfo], Optional[str]]:
        """Validates a CNPJ and returns company information if valid."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = time.time()
                response = await client.get(f"{self.cnpj_api_url}/{cnpj}")
                duration = time.time() - start_time
                metrics.observe_request_latency("cnpj_validation", duration)
                
                if response.status_code == 200:
                    data = response.json()
                    metrics.inc_validation_attempt("cnpj")
                    return True, CompanyInfo(**data), None
                metrics.inc_validation_error("cnpj", f"http_{response.status_code}")
                return False, None, "CNPJ inválido"
        except Exception as e:
            metrics.inc_validation_error("cnpj", type(e).__name__)
            return False, None, str(e)

    async def validate_cep(self, cep: str) -> tuple[bool, Optional[Address], Optional[str]]:
        """Validates a CEP and returns address information if valid."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = time.time()
                response = await client.get(f"{self.cep_api_url}/{cep}")
                duration = time.time() - start_time
                metrics.observe_request_latency("cep_validation", duration)
                
                if response.status_code == 200:
                    data = response.json()
                    metrics.inc_validation_attempt("cep")
                    return True, Address(**data), None
                metrics.inc_validation_error("cep", f"http_{response.status_code}")
                return False, None, "CEP inválido"
        except Exception as e:
            metrics.inc_validation_error("cep", type(e).__name__)
            return False, None, str(e)

    async def validate_both(self, cnpj: str, cep: str) -> Dict[str, Any]:
        """Validates both CNPJ and CEP."""
        cnpj_valid, cnpj_info, cnpj_error = await self.validate_cnpj(cnpj)
        cep_valid, cep_info, cep_error = await self.validate_cep(cep)

        return {
            "cnpj_valid": cnpj_valid,
            "cep_valid": cep_valid,
            "cnpj_details": cnpj_info,
            "cep_details": cep_info,
            "error": cnpj_error or cep_error
        } 