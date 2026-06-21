import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


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
    created_tickets = relationship(
        "Ticket", foreign_keys="Ticket.creator_id", back_populates="creator"
    )
    assigned_tickets = relationship(
        "Ticket", foreign_keys="Ticket.assigned_to_id", back_populates="assignee"
    )
    approved_tickets = relationship(
        "Ticket", foreign_keys="Ticket.approved_by_id", back_populates="approver"
    )
    messages = relationship("Message", back_populates="author")
    notifications = relationship("Notification", back_populates="user")

    @property
    def room_ids(self):
        return [m.room_id for m in self.room_memberships]

    @property
    def penalty_reasons(self):
        reasons = []
        active_tickets = [t for t in self.assigned_tickets if t.status.name != "resolved"]
        if len(active_tickets) > 5:
            reasons.append(f"Overloaded: {len(active_tickets)} active tickets (Max 5)")

        overdue_tickets = [
            t for t in active_tickets if t.due_date and t.due_date < datetime.utcnow()
        ]
        if len(overdue_tickets) > 0:
            reasons.append(f"Deadline Missed: {len(overdue_tickets)} overdue tickets")

        return reasons

    @property
    def has_penalty(self):
        return len(self.penalty_reasons) > 0
