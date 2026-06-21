from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domains.rooms.schemas import RoomOut
from app.domains.tickets.models import ApprovalStatus, MessageType, TicketPriority, TicketStatus
from app.domains.users.schemas import UserOut


class MessageCreate(BaseModel):
    content: str
    type: MessageType = MessageType.comment


class MessageOut(BaseModel):
    id: UUID
    ticket_id: UUID
    author_id: UUID
    content: str
    type: MessageType
    attachment_name: Optional[str] = None
    attachment_type: Optional[str] = None
    created_at: datetime
    author: UserOut

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class TicketDetailOut(TicketOut):
    messages: List[MessageOut]
    rooms: List[RoomOut]
