from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ScheduleEventRequest, ScheduleEventResponse, RenderEvent
from app.services.video_render import VideoRenderService

router = APIRouter()

@router.post(
    "/schedule",
    response_model=ScheduleEventResponse,
    summary="Agenda um evento de renderização",
    description="Agenda um novo evento de renderização de vídeo para execução futura",
    responses={
        200: {"description": "Evento agendado com sucesso"},
        400: {"description": "Data de agendamento inválida"},
        500: {"description": "Erro ao agendar evento"}
    }
)
async def schedule_event(
    request: ScheduleEventRequest,
    service: VideoRenderService = Depends()
) -> ScheduleEventResponse:
    try:
        return await service.schedule_event(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao agendar evento: {str(e)}"
        )

@router.get(
    "/status/{event_id}",
    response_model=RenderEvent,
    summary="Obtém status de um evento",
    description="Retorna o status atual de um evento de renderização",
    responses={
        200: {"description": "Status do evento obtido com sucesso"},
        404: {"description": "Evento não encontrado"},
        500: {"description": "Erro ao obter status do evento"}
    }
)
async def get_event_status(
    event_id: str,
    service: VideoRenderService = Depends()
) -> RenderEvent:
    try:
        return await service.get_event_status(event_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter status do evento: {str(e)}"
        ) 