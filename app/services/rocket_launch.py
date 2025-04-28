from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.models.schemas import RocketLaunch, LaunchReport, RocketLaunchCreate, RocketLaunchResponse
from app.core.config import get_settings
from prometheus_client import Counter, Histogram

settings = get_settings()

# Métricas Prometheus
LAUNCHES_COLLECTED = Counter('rocket_launches_collected_total', 'Total de lançamentos coletados')
LAUNCH_ERRORS = Counter('rocket_launch_errors_total', 'Total de erros em operações de lançamento')
LAUNCH_LATENCY = Histogram('rocket_launch_operations_latency_seconds', 'Latência das operações de lançamento')

class RocketLaunchService:
    def __init__(self, db: Session):
        self.db = db
        # Conexão com o banco de dados principal
        self.main_engine = create_engine(settings.DATABASE_URL)
        self.main_session = sessionmaker(bind=self.main_engine)
        
        # Conexão com o banco de dados de relatórios
        self.report_engine = create_engine(settings.REPORT_DATABASE_URL)
        self.report_session = sessionmaker(bind=self.report_engine)

    async def _store_launch_data(self, launch_data: RocketLaunch):
        """Armazena os dados do lançamento no banco de relatórios"""
        try:
            session = self.report_session()
            # Aqui você implementaria a lógica de inserção no banco de relatórios
            # Por exemplo:
            # session.add(launch_data)
            # session.commit()
            session.close()
        except Exception as e:
            # Log do erro, mas não interrompe o fluxo principal
            print(f"Erro ao armazenar dados do relatório: {str(e)}")

    async def process_launch(self, launch_data: RocketLaunch):
        """Processa um lançamento e armazena os dados para relatório"""
        try:
            # Armazena os dados para relatório de forma assíncrona
            await self._store_launch_data(launch_data)
        except Exception as e:
            # Log do erro, mas não interrompe o fluxo principal
            print(f"Erro ao processar dados do lançamento: {str(e)}")

    async def generate_report(
        self,
        customer_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> LaunchReport:
        """Gera um relatório de lançamentos para um cliente em um período"""
        try:
            session = self.report_session()
            
            # Consulta os lançamentos do período
            query = text("""
                SELECT * FROM rocket_launches 
                WHERE customer_id = :customer_id 
                AND launch_date BETWEEN :start_date AND :end_date
            """)
            
            result = session.execute(
                query,
                {
                    "customer_id": customer_id,
                    "start_date": period_start,
                    "end_date": period_end
                }
            )
            
            launches = [RocketLaunch(**row) for row in result]
            
            # Calcula estatísticas
            total_launches = len(launches)
            successful_launches = sum(1 for l in launches if l.status == "success")
            failed_launches = total_launches - successful_launches
            
            return LaunchReport(
                customer_id=customer_id,
                period_start=period_start,
                period_end=period_end,
                total_launches=total_launches,
                successful_launches=successful_launches,
                failed_launches=failed_launches,
                average_pre_flight_time=0.0,  # Implementar cálculo real
                launches=launches
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar relatório: {str(e)}"
            )
        finally:
            session.close()

    @LAUNCH_LATENCY.time()
    def create_launch(self, launch_data: RocketLaunchCreate) -> RocketLaunch:
        """Cria um novo registro de lançamento"""
        try:
            # Verifica se o lançamento já existe
            if self.db.query(RocketLaunch).filter(RocketLaunch.launch_id == launch_data.launch_id).first():
                raise HTTPException(
                    status_code=400,
                    detail="Lançamento já registrado"
                )

            db_launch = RocketLaunch(
                launch_id=launch_data.launch_id,
                name=launch_data.name,
                status=launch_data.status,
                launch_date=launch_data.launch_date,
                rocket_name=launch_data.rocket_name,
                rocket_type=launch_data.rocket_type,
                launch_site=launch_data.launch_site,
                mission_name=launch_data.mission_name,
                mission_details=launch_data.mission_details,
                payload_mass=launch_data.payload_mass,
                orbit=launch_data.orbit,
                user_id=launch_data.user_id
            )

            self.db.add(db_launch)
            self.db.commit()
            self.db.refresh(db_launch)

            LAUNCHES_COLLECTED.inc()
            return db_launch

        except HTTPException:
            raise
        except Exception as e:
            LAUNCH_ERRORS.inc()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao criar lançamento: {str(e)}"
            )

    @LAUNCH_LATENCY.time()
    def get_launch(self, launch_id: str) -> RocketLaunch:
        """Busca um lançamento pelo ID"""
        try:
            launch = self.db.query(RocketLaunch).filter(RocketLaunch.launch_id == launch_id).first()
            if not launch:
                raise HTTPException(
                    status_code=404,
                    detail="Lançamento não encontrado"
                )
            return launch
        except HTTPException:
            raise
        except Exception as e:
            LAUNCH_ERRORS.inc()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar lançamento: {str(e)}"
            )

    @LAUNCH_LATENCY.time()
    def get_launches_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> List[RocketLaunch]:
        """Busca lançamentos por período"""
        try:
            query = self.db.query(RocketLaunch).filter(
                RocketLaunch.launch_date >= start_date,
                RocketLaunch.launch_date <= end_date
            )

            if user_id:
                query = query.filter(RocketLaunch.user_id == user_id)

            return query.all()
        except Exception as e:
            LAUNCH_ERRORS.inc()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar lançamentos: {str(e)}"
            )

    @LAUNCH_LATENCY.time()
    def get_launch_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> dict:
        """Retorna estatísticas dos lançamentos no período"""
        try:
            launches = self.get_launches_by_period(start_date, end_date, user_id)
            
            total_launches = len(launches)
            successful_launches = sum(1 for l in launches if l.status.lower() == "success")
            failed_launches = total_launches - successful_launches
            
            rocket_types = {}
            for launch in launches:
                rocket_types[launch.rocket_type] = rocket_types.get(launch.rocket_type, 0) + 1
            
            return {
                "total_launches": total_launches,
                "successful_launches": successful_launches,
                "failed_launches": failed_launches,
                "success_rate": (successful_launches / total_launches * 100) if total_launches > 0 else 0,
                "rocket_types": rocket_types
            }
        except Exception as e:
            LAUNCH_ERRORS.inc()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao calcular estatísticas: {str(e)}"
            ) 