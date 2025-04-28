from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.schemas import CustomerValidationRequest, CustomerValidationResponse
from app.services.validation import ValidationService

router = APIRouter()

@router.post("/validate", response_model=CustomerValidationResponse)
async def validate_customer(request: CustomerValidationRequest, db: Session = Depends(get_db)):
    """Validate customer data."""
    service = ValidationService()  # Removed db parameter as it's not used in the service
    try:
        return await service.validate_customer(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{validation_id}", response_model=CustomerValidationResponse)
async def get_validation(validation_id: int, db: Session = Depends(get_db)):
    """Get validation result by ID."""
    service = ValidationService()
    validation = await service.get_validation_by_id(validation_id)
    if not validation:
        raise HTTPException(status_code=404, detail="Validation not found")
    return validation 