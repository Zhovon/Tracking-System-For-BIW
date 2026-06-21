from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user
from app.database import get_db

router = APIRouter()


@router.get("", response_model=List[schemas.NotificationOut])
def get_notifications(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Retrieve notifications for the current user.
    """
    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notifications


@router.patch("/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_notification_read(
    *,
    db: Session = Depends(get_db),
    notification_id: UUID,
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Mark a notification as read.
    """
    notification = (
        db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
