from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.services.rocket_launch import RocketLaunchService
from app.models.schemas import (
    RocketLaunchCreate,
    RocketLaunchResponse,
    LaunchStatistics
)

router = APIRouter()

@router.post(
    "/",
    response_model=RocketLaunchResponse,
    summary="Registra um novo lançamento",
    description="Registra um novo lançamento de foguete no sistema",
    responses={
        201: {"description": "Lançamento registrado com sucesso"},
        400: {"description": "Lançamento já registrado"},
        500: {"description": "Erro ao registrar lançamento"}
    }
)
def create_launch(
    launch_data: RocketLaunchCreate,
    db: Session = Depends(get_db)
) -> RocketLaunchResponse:
    service = RocketLaunchService(db)
    launch = service.create_launch(launch_data)
    return RocketLaunchResponse.from_orm(launch)

@router.get(
    "/{launch_id}",
    response_model=RocketLaunchResponse,
    summary="Busca um lançamento",
    description="Retorna os dados de um lançamento pelo ID",
    responses={
        200: {"description": "Lançamento encontrado"},
        404: {"description": "Lançamento não encontrado"},
        500: {"description": "Erro ao buscar lançamento"}
    }
)
def get_launch(
    launch_id: str,
    db: Session = Depends(get_db)
) -> RocketLaunchResponse:
    service = RocketLaunchService(db)
    launch = service.get_launch(launch_id)
    return RocketLaunchResponse.from_orm(launch)

@router.get(
    "/period/",
    response_model=List[RocketLaunchResponse],
    summary="Busca lançamentos por período",
    description="Retorna todos os lançamentos dentro de um período específico",
    responses={
        200: {"description": "Lista de lançamentos"},
        500: {"description": "Erro ao buscar lançamentos"}
    }
)
def get_launches_by_period(
    start_date: datetime = Query(..., description="Data inicial do período"),
    end_date: datetime = Query(..., description="Data final do período"),
    user_id: Optional[int] = Query(None, description="ID do usuário para filtrar"),
    db: Session = Depends(get_db)
) -> List[RocketLaunchResponse]:
    service = RocketLaunchService(db)
    launches = service.get_launches_by_period(start_date, end_date, user_id)
    return [RocketLaunchResponse.from_orm(launch) for launch in launches]

@router.get(
    "/statistics/",
    response_model=LaunchStatistics,
    summary="Estatísticas de lançamentos",
    description="Retorna estatísticas dos lançamentos em um período",
    responses={
        200: {"description": "Estatísticas dos lançamentos"},
        500: {"description": "Erro ao calcular estatísticas"}
    }
)
def get_launch_statistics(
    start_date: datetime = Query(..., description="Data inicial do período"),
    end_date: datetime = Query(..., description="Data final do período"),
    user_id: Optional[int] = Query(None, description="ID do usuário para filtrar"),
    db: Session = Depends(get_db)
) -> LaunchStatistics:
    service = RocketLaunchService(db)
    return service.get_launch_statistics(start_date, end_date, user_id) 