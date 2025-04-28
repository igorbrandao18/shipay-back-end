from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import (
    ScheduleEventRequest,
    ScheduleEventResponse,
    EventStatus
)
from app.services.scheduler import SchedulerService
from typing import List, Dict, Any

router = APIRouter()

@router.post("/events", response_model=ScheduleEventResponse)
async def schedule_event(request: ScheduleEventRequest):
    """Schedule a new event."""
    service = SchedulerService()
    try:
        return await service.schedule_event(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{event_id}", response_model=Dict[str, Any])
async def get_event(event_id: str):
    """Get event details by ID."""
    service = SchedulerService()
    event = await service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/events/{event_id}/status/{status}")
async def update_event_status(event_id: str, status: EventStatus):
    """Update event status."""
    service = SchedulerService()
    success = await service.update_event_status(event_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event status updated successfully"}

@router.get("/events/pending", response_model=List[Dict[str, Any]])
async def get_pending_events(limit: int = 100):
    """Get pending events that are due for execution."""
    service = SchedulerService()
    return await service.get_pending_events(limit)

@router.delete("/events/cleanup")
async def cleanup_completed_events(event_ids: List[str]):
    """Remove completed events from the queue."""
    service = SchedulerService()
    await service.remove_completed_events(event_ids)
    return {"message": "Events cleaned up successfully"} 