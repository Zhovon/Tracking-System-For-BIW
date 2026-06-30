import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, LargeBinary, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TicketStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    approved = "approved"
    resolved = "resolved"


class TicketPriority(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ApprovalStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class MessageType(enum.Enum):
    comment = "comment"
    approval = "approval"
    status_update = "status_update"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String)
    description = Column(Text)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    assigned_to_id = Column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True
    )
    approved_by_id = Column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True
    )
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.open)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.medium)
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.pending)
    is_active = Column(Boolean, default=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("Employee", foreign_keys=[creator_id], back_populates="created_tickets")
    assignee = relationship(
        "Employee", foreign_keys=[assigned_to_id], back_populates="assigned_tickets"
    )
    approver = relationship(
        "Employee", foreign_keys=[approved_by_id], back_populates="approved_tickets"
    )
    room_links = relationship("TicketRoom", back_populates="ticket")
    participants = relationship("TicketParticipant", back_populates="ticket")
    messages = relationship("Message", back_populates="ticket", order_by="Message.created_at")


class TicketRoom(Base):
    __tablename__ = "ticket_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="CASCADE"), index=True)

    ticket = relationship("Ticket", back_populates="room_links")
    room = relationship("Room", back_populates="ticket_links")


class TicketParticipant(Base):
    __tablename__ = "ticket_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), index=True)

    ticket = relationship("Ticket", back_populates="participants")
    employee = relationship("Employee", back_populates="participated_tickets")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    content = Column(Text)
    type = Column(SQLEnum(MessageType), default=MessageType.comment)

    attachment_name = Column(String, nullable=True)
    attachment_type = Column(String, nullable=True)
    attachment_data = Column(LargeBinary, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")
    author = relationship("Employee", back_populates="messages")
