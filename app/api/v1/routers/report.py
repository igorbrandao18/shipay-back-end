from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import LaunchReport, LaunchReportRequest
from app.services.report import ReportService

router = APIRouter()

@router.post(
    "/launches",
    response_model=LaunchReport,
    summary="Gera relatório de lançamentos",
    description="Gera um relatório de lançamentos de foguetes para um cliente em um período específico",
    responses={
        200: {"description": "Relatório gerado com sucesso"},
        400: {"description": "Dados inválidos"},
        500: {"description": "Erro ao gerar relatório"}
    }
)
async def generate_launch_report(
    request: LaunchReportRequest,
    service: ReportService = Depends()
) -> LaunchReport:
    try:
        # Valida o período (máximo 30 dias)
        period_days = (request.period_end - request.period_start).days
        if period_days > 30:
            raise HTTPException(
                status_code=400,
                detail="O período máximo para o relatório é de 30 dias"
            )
        
        return await service.generate_report(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar relatório: {str(e)}"
        ) 