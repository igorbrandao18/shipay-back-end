from typing import Optional, Dict, Any
from datetime import datetime
import json
from app.core.redis import RedisManager
from app.models.schemas import EventStatus, ScheduleEventRequest, ScheduleEventResponse
from app.core.metrics import metrics
import uuid

class SchedulerService:
    def __init__(self):
        self.redis = None
        self.job_prefix = "scheduler:job:"
        self.queue_key = "scheduler:queue"

    async def _get_redis(self):
        if self.redis is None:
            self.redis = await RedisManager.get_client()
        return self.redis

    async def schedule_event(self, request: ScheduleEventRequest) -> ScheduleEventResponse:
        """Schedule a new event."""
        redis = await self._get_redis()
        event_id = str(uuid.uuid4())
        
        event_data = {
            "event_id": event_id,
            "event_type": request.event_type,
            "content": request.content,
            "scheduled_time": request.scheduled_time.isoformat(),
            "status": EventStatus.SCHEDULED.value,
            "metadata": request.metadata,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Store event data
        await redis.hset(f"{self.job_prefix}{event_id}", mapping=event_data)
        
        # Add to scheduled queue
        await redis.zadd(
            self.queue_key,
            {event_id: request.scheduled_time.timestamp()}
        )
        
        metrics.inc_api_request("POST", "/scheduler", 201)
        return ScheduleEventResponse(
            event_id=event_id,
            status=EventStatus.SCHEDULED,
            scheduled_time=request.scheduled_time
        )

    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event details by ID."""
        redis = await self._get_redis()
        event_data = await redis.hgetall(f"{self.job_prefix}{event_id}")
        
        if not event_data:
            return None
            
        metrics.inc_api_request("GET", f"/scheduler/{event_id}", 200)
        return event_data

    async def update_event_status(self, event_id: str, status: EventStatus) -> bool:
        """Update event status."""
        redis = await self._get_redis()
        exists = await redis.exists(f"{self.job_prefix}{event_id}")
        
        if not exists:
            return False
            
        await redis.hset(
            f"{self.job_prefix}{event_id}",
            "status",
            status.value,
            "updated_at",
            datetime.utcnow().isoformat()
        )
        
        metrics.inc_api_request("PUT", f"/scheduler/{event_id}", 200)
        return True

    async def get_pending_events(self, limit: int = 100) -> list[Dict[str, Any]]:
        """Get pending events that are due for execution."""
        redis = await self._get_redis()
        now = datetime.utcnow().timestamp()
        
        # Get events due for execution
        event_ids = await redis.zrangebyscore(
            self.queue_key,
            0,
            now,
            start=0,
            num=limit
        )
        
        if not event_ids:
            return []
            
        # Get event details
        events = []
        for event_id in event_ids:
            event_data = await redis.hgetall(f"{self.job_prefix}{event_id}")
            if event_data:
                events.append(event_data)
                
        metrics.inc_api_request("GET", "/scheduler/pending", 200)
        return events

    async def remove_completed_events(self, event_ids: list[str]) -> None:
        """Remove completed events from the queue."""
        redis = await self._get_redis()
        
        # Remove from queue
        if event_ids:
            await redis.zrem(self.queue_key, *event_ids)
            
        # Remove event data
        for event_id in event_ids:
            await redis.delete(f"{self.job_prefix}{event_id}")
            
        metrics.inc_api_request("DELETE", "/scheduler/cleanup", 200) 