from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from .models import RoomType, TicketStatus, TicketPriority, MessageType, ApprovalStatus

# --- Auth / User Schemas ---
class UserOut(BaseModel):
    id: UUID
    staff_id: Optional[str] = None
    name: str
    email: str
    role: str
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

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    room_ids: Optional[List[UUID]] = None

# --- Room Schemas ---
class RoomOut(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# --- Message Schemas ---
class MessageCreate(BaseModel):
    content: str
    type: MessageType = MessageType.comment

class MessageOut(BaseModel):
    id: UUID
    content: str
    type: MessageType
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None
    created_at: datetime
    author: UserOut
    
    model_config = ConfigDict(from_attributes=True)

# --- Ticket Schemas ---
class TicketCreate(BaseModel):
    title: str
    description: str
    room_ids: List[UUID]
    priority: TicketPriority = TicketPriority.medium
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[UUID] = None

class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to_id: Optional[UUID] = None
    add_room_id: Optional[UUID] = None

class TicketOut(BaseModel):
    id: UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    approval_status: ApprovalStatus
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    creator: UserOut
    assignee: Optional[UserOut] = None
    rooms: List[RoomOut] = []
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True

class TicketDetailOut(TicketOut):
    messages: List[MessageOut]
    rooms: List[RoomOut]

# --- Notification Schemas ---
class NotificationOut(BaseModel):
    id: UUID
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
