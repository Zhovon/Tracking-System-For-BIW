from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: UUID
    ticket_id: Optional[UUID] = None
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PushSubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
