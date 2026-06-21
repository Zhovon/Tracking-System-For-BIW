from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoomOut(BaseModel):
    id: UUID
    name: str
    type: str

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    name: str
    type: str


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None


class RoomMemberCreate(BaseModel):
    employee_id: UUID
    room_id: UUID
