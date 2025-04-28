from fastapi import APIRouter
from app.api.v1.routers import user, validation, report, scheduler

api_router = APIRouter()

api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(validation.router, prefix="/validation", tags=["Validation"])
api_router.include_router(report.router, prefix="/reports", tags=["Reports"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"]) 