import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.core.config import get_settings
from app.models.schemas import Address, CompanyInfo, CustomerValidationResponse

settings = get_settings()

class CustomerValidationService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.max_retries = 3
        self.retry_delay = 1  # segundos

    async def _make_request_with_retry(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                if attempt == self.max_retries - 1:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao consultar {url}: {str(e)}"
                    )
                await asyncio.sleep(self.retry_delay)

    async def get_company_info(self, cnpj: str) -> CompanyInfo:
        try:
            # Consulta à API de CNPJ
            data = await self._make_request_with_retry(
                f"{settings.CNPJ_API_URL}/cnpj/{cnpj}"
            )
            
            return CompanyInfo(
                cnpj=cnpj,
                razao_social=data["razao_social"],
                nome_fantasia=data.get("nome_fantasia"),
                endereco=Address(
                    cep=data["endereco"]["cep"],
                    logradouro=data["endereco"]["logradouro"],
                    complemento=data["endereco"].get("complemento"),
                    bairro=data["endereco"]["bairro"],
                    cidade=data["endereco"]["cidade"],
                    uf=data["endereco"]["uf"]
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao consultar informações do CNPJ: {str(e)}"
            )

    async def get_address_by_cep(self, cep: str) -> Address:
        try:
            # Primeira tentativa com o provedor principal
            data = await self._make_request_with_retry(
                f"{settings.CEP_API_URL}/{cep}/json"
            )
            
            if data.get("erro"):
                # Se falhar, tenta o provedor alternativo
                data = await self._make_request_with_retry(
                    f"{settings.CEP_API_FALLBACK_URL}/{cep}"
                )
            
            return Address(
                cep=cep,
                logradouro=data["logradouro"],
                complemento=data.get("complemento"),
                bairro=data["bairro"],
                cidade=data["cidade"],
                uf=data["uf"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao consultar endereço pelo CEP: {str(e)}"
            )

    async def validate_customer(
        self,
        cnpj: str,
        cep: str
    ) -> CustomerValidationResponse:
        try:
            # Obtém informações da empresa
            company_info = await self.get_company_info(cnpj)
            
            # Obtém endereço pelo CEP
            address = await self.get_address_by_cep(cep)
            
            # Compara os endereços
            address_match = (
                company_info.endereco.uf.lower() == address.uf.lower() and
                company_info.endereco.cidade.lower() == address.cidade.lower() and
                company_info.endereco.logradouro.lower() == address.logradouro.lower()
            )
            
            return CustomerValidationResponse(
                is_valid=address_match,
                company_info=company_info,
                address_match=address_match,
                details="Endereço validado com sucesso" if address_match else "Endereço não corresponde"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao validar cliente: {str(e)}"
            ) 