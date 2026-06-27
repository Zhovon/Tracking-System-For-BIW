from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    id: UUID
    staff_id: Optional[str] = None
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    nid: Optional[str] = None
    joining_date: Optional[str] = None
    room_ids: List[UUID] = []
    has_penalty: bool = False
    penalty_reasons: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    room_ids: List[UUID]
    phone: Optional[str] = None
    nid: Optional[str] = None
    joining_date: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    room_ids: Optional[List[UUID]] = None
    phone: Optional[str] = None
    nid: Optional[str] = None
    joining_date: Optional[str] = None
