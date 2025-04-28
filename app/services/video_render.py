import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException
from redis import Redis
from kafka import KafkaProducer
from app.models.schemas import RenderEvent, ScheduleEventRequest, ScheduleEventResponse
from app.core.config import get_settings

settings = get_settings()

class VideoRenderService:
    def __init__(self):
        # Conexão com Redis para armazenamento dos eventos
        self.redis = Redis.from_url(settings.REDIS_URL)
        
        # Conexão com Kafka para publicação dos eventos
        self.kafka_producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Inicia o processo de verificação de eventos
        self._start_event_checker()

    def _start_event_checker(self):
        """Inicia o processo de verificação de eventos agendados"""
        asyncio.create_task(self._check_scheduled_events())

    async def _check_scheduled_events(self):
        """Verifica periodicamente eventos agendados"""
        while True:
            try:
                await self._process_due_events()
            except Exception as e:
                print(f"Erro ao verificar eventos: {str(e)}")
            await asyncio.sleep(1)  # Verifica a cada segundo

    async def _process_due_events(self):
        """Processa eventos que estão vencidos"""
        now = datetime.now()
        
        # Busca todos os eventos agendados
        events = self.redis.keys("event:*")
        
        for event_key in events:
            event_data = self.redis.get(event_key)
            if not event_data:
                continue
                
            event = RenderEvent(**json.loads(event_data))
            
            # Se o evento está vencido e pendente
            if event.scheduled_time <= now and event.status == "pending":
                try:
                    # Atualiza status para processando
                    event.status = "processing"
                    self.redis.set(event_key, event.json())
                    
                    # Publica no Kafka
                    self.kafka_producer.send(
                        settings.KAFKA_TOPIC,
                        value={
                            "event_id": event.event_id,
                            "content": event.content,
                            "scheduled_time": event.scheduled_time.isoformat()
                        }
                    )
                    
                    # Atualiza status para concluído
                    event.status = "completed"
                    event.processed_at = datetime.now()
                    self.redis.set(event_key, event.json())
                    
                except Exception as e:
                    # Em caso de erro, marca como falha
                    event.status = "failed"
                    self.redis.set(event_key, event.json())
                    print(f"Erro ao processar evento {event.event_id}: {str(e)}")

    async def schedule_event(
        self,
        request: ScheduleEventRequest
    ) -> ScheduleEventResponse:
        """Agenda um novo evento de renderização"""
        try:
            # Cria o evento
            event = RenderEvent(
                event_id=str(uuid.uuid4()),
                content=request.content,
                scheduled_time=request.scheduled_time
            )
            
            # Armazena no Redis
            self.redis.set(
                f"event:{event.event_id}",
                event.json(),
                ex=int((request.scheduled_time - datetime.now()).total_seconds()) + 3600  # Expira 1 hora após o agendamento
            )
            
            return ScheduleEventResponse(
                event_id=event.event_id,
                scheduled_time=event.scheduled_time,
                status=event.status
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao agendar evento: {str(e)}"
            )

    async def get_event_status(self, event_id: str) -> RenderEvent:
        """Obtém o status de um evento"""
        try:
            event_data = self.redis.get(f"event:{event_id}")
            if not event_data:
                raise HTTPException(
                    status_code=404,
                    detail="Evento não encontrado"
                )
            return RenderEvent(**json.loads(event_data))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao obter status do evento: {str(e)}"
            ) 