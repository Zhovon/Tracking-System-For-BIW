import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base
import enum

# Enums
class RoomType(enum.Enum):
    branch = "branch"
    department = "department"
    founder = "founder"
    universal = "universal"

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

# Models
class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    type = Column(SQLEnum(RoomType))
    is_active = Column(Boolean, default=True) # Soft delete
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("RoomMember", back_populates="room")
    ticket_links = relationship("TicketRoom", back_populates="room")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    staff_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    room_memberships = relationship("RoomMember", back_populates="employee")
    created_tickets = relationship("Ticket", foreign_keys="Ticket.creator_id", back_populates="creator")
    assigned_tickets = relationship("Ticket", foreign_keys="Ticket.assigned_to_id", back_populates="assignee")
    approved_tickets = relationship("Ticket", foreign_keys="Ticket.approved_by_id", back_populates="approver")
    messages = relationship("Message", back_populates="author")
    notifications = relationship("Notification", back_populates="user")

    @property
    def room_ids(self):
        return [m.room_id for m in self.room_memberships]

    @property
    def penalty_reasons(self):
        reasons = []
        # Filter active tickets directly using the relationship
        active_tickets = [t for t in self.assigned_tickets if t.status.name != "resolved"]
        if len(active_tickets) > 5:
            reasons.append(f"Overloaded: {len(active_tickets)} active tickets (Max 5)")
            
        overdue_tickets = [t for t in active_tickets if t.due_date and t.due_date < datetime.utcnow()]
        if len(overdue_tickets) > 0:
            reasons.append(f"Deadline Missed: {len(overdue_tickets)} overdue tickets")
            
        return reasons

    @property
    def has_penalty(self):
        return len(self.penalty_reasons) > 0

class RoomMember(Base):
    __tablename__ = "room_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), index=True)

    employee = relationship("Employee", back_populates="room_memberships")
    room = relationship("Room", back_populates="members")

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String)
    description = Column(Text)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True)
    approved_by_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), nullable=True, index=True)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.open)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.medium)
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.pending)
    is_active = Column(Boolean, default=True) # Soft delete
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("Employee", foreign_keys=[creator_id], back_populates="created_tickets")
    assignee = relationship("Employee", foreign_keys=[assigned_to_id], back_populates="assigned_tickets")
    approver = relationship("Employee", foreign_keys=[approved_by_id], back_populates="approved_tickets")
    room_links = relationship("TicketRoom", back_populates="ticket")
    messages = relationship("Message", back_populates="ticket", order_by="Message.created_at")

class TicketRoom(Base):
    __tablename__ = "ticket_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), index=True)

    ticket = relationship("Ticket", back_populates="room_links")
    room = relationship("Room", back_populates="ticket_links")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    content = Column(Text)
    type = Column(SQLEnum(MessageType), default=MessageType.comment)
    
    # Attachment fields
    attachment_name = Column(String, nullable=True)
    attachment_type = Column(String, nullable=True)
    attachment_data = Column(LargeBinary, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="messages")
    author = relationship("Employee", back_populates="messages")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Employee", back_populates="notifications")
