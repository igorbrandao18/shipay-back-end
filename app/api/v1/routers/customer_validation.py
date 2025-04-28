from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import CustomerValidationRequest, CustomerValidationResponse
from app.services.customer_validation import CustomerValidationService

router = APIRouter()

@router.post(
    "/validate",
    response_model=CustomerValidationResponse,
    summary="Valida cadastro de cliente",
    description="Valida o cadastro de um cliente comparando o endereço do CNPJ com o CEP informado",
    responses={
        200: {"description": "Validação realizada com sucesso"},
        404: {"description": "Endereço não corresponde"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def validate_customer(
    request: CustomerValidationRequest,
    service: CustomerValidationService = Depends()
) -> CustomerValidationResponse:
    try:
        response = await service.validate_customer(
            cnpj=request.cnpj,
            cep=request.cep
        )
        
        if not response.address_match:
            raise HTTPException(
                status_code=404,
                detail="Endereço não corresponde ao cadastro da empresa"
            )
            
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao validar cliente: {str(e)}"
        ) 