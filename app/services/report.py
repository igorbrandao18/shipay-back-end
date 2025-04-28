from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.schemas import LaunchReport, LaunchReportRequest, RocketLaunch
from app.core.config import get_settings

settings = get_settings()

class ReportService:
    def __init__(self):
        # Conexão com o banco de dados de relatórios
        self.report_engine = create_engine(settings.REPORT_DATABASE_URL)
        self.ReportSession = sessionmaker(bind=self.report_engine)
        
        # Conexão com o banco de dados principal (somente leitura)
        self.main_engine = create_engine(settings.DATABASE_URL)
        self.MainSession = sessionmaker(bind=self.main_engine)

    async def _store_launch_data(self, launch_data: dict):
        """Armazena os dados do lançamento no banco de relatórios"""
        try:
            session = self.ReportSession()
            query = text("""
                INSERT INTO rocket_launches (
                    customer_id, launch_date, status, pre_flight_status,
                    countdown_status, trace_id, created_at
                ) VALUES (
                    :customer_id, :launch_date, :status, :pre_flight_status,
                    :countdown_status, :trace_id, :created_at
                )
            """)
            
            session.execute(query, {
                "customer_id": launch_data["customer_id"],
                "launch_date": launch_data["launch_date"],
                "status": launch_data["status"],
                "pre_flight_status": launch_data["pre_flight_status"],
                "countdown_status": launch_data["countdown_status"],
                "trace_id": launch_data["trace_id"],
                "created_at": datetime.now()
            })
            session.commit()
        except Exception as e:
            session.rollback()
            # Não levanta exceção para não impactar o fluxo principal
            print(f"Erro ao armazenar dados do relatório: {str(e)}")
        finally:
            session.close()

    async def _get_launches_for_period(
        self,
        customer_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> List[dict]:
        """Busca lançamentos do período no banco de relatórios"""
        try:
            session = self.ReportSession()
            query = text("""
                SELECT * FROM rocket_launches
                WHERE customer_id = :customer_id
                AND launch_date BETWEEN :period_start AND :period_end
                ORDER BY launch_date DESC
            """)
            
            result = session.execute(query, {
                "customer_id": customer_id,
                "period_start": period_start,
                "period_end": period_end
            })
            
            return [dict(row) for row in result]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar lançamentos: {str(e)}"
            )
        finally:
            session.close()

    async def generate_report(self, request: LaunchReportRequest) -> LaunchReport:
        """Gera o relatório de lançamentos para um cliente"""
        try:
            # Busca os lançamentos do período
            launches = await self._get_launches_for_period(
                request.customer_id,
                request.period_start,
                request.period_end
            )
            
            # Calcula estatísticas
            total_launches = len(launches)
            successful_launches = sum(1 for l in launches if l["status"] == "success")
            failed_launches = total_launches - successful_launches
            
            # Calcula tempo médio de verificação pré-lançamento
            pre_flight_times = [
                (l["launch_date"] - l["created_at"]).total_seconds()
                for l in launches
            ]
            avg_pre_flight_time = sum(pre_flight_times) / len(pre_flight_times) if pre_flight_times else 0
            
            # Constrói a resposta
            return LaunchReport(
                customer_id=request.customer_id,
                period_start=request.period_start,
                period_end=request.period_end,
                total_launches=total_launches,
                successful_launches=successful_launches,
                failed_launches=failed_launches,
                average_pre_flight_time=avg_pre_flight_time,
                launches=[
                    RocketLaunch(
                        customer_id=l["customer_id"],
                        launch_date=l["launch_date"],
                        status=l["status"],
                        pre_flight_status=l["pre_flight_status"],
                        countdown_status=l["countdown_status"],
                        trace_id=l["trace_id"]
                    )
                    for l in launches
                ]
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar relatório: {str(e)}"
            ) 