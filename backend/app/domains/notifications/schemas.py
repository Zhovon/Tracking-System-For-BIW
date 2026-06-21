from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    id: UUID
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
