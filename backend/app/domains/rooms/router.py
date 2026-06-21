from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_db

router = APIRouter()


@router.get("/all", response_model=List[schemas.RoomOut])
def get_all_rooms(db: Session = Depends(get_db)) -> Any:
    """
    Get all active rooms for escalation dropdowns.
    """
    return db.query(models.Room).filter(models.Room.is_active == True).all()
