from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user, get_db

router = APIRouter()


@router.get("/all", response_model=List[schemas.RoomOut])
def get_all_rooms(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Get the active rooms available to the current user.

    Owners can manage every room. Other employees can only see rooms they
    belong to, plus the Universal room used for company-wide announcements.
    """
    if current_user.role == "owner":
        return db.query(models.Room).filter(models.Room.is_active == True).all()

    user_rooms = [
        membership.room
        for membership in current_user.room_memberships
        if membership.room.is_active
    ]
    universal_rooms = db.query(models.Room).filter(
        models.Room.type == models.RoomType.universal,
        models.Room.is_active == True,
    ).all()
    return list({room.id: room for room in user_rooms + universal_rooms}.values())


@router.post("", response_model=schemas.RoomOut)
def create_room(
    room_in: schemas.RoomCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Create a new room. Owner only.
    """
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create rooms")

    valid_types = [t.value for t in models.RoomType]
    if room_in.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid room type. Must be one of: {valid_types}",
        )

    room_type = models.RoomType[room_in.type]
    room = models.Room(name=room_in.name, type=room_type)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room
