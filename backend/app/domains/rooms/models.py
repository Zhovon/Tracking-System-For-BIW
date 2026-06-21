import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RoomType(enum.Enum):
    branch = "branch"
    department = "department"
    founder = "founder"
    universal = "universal"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, index=True)
    type = Column(SQLEnum(RoomType))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("RoomMember", back_populates="room")
    ticket_links = relationship("TicketRoom", back_populates="room")


class RoomMember(Base):
    __tablename__ = "room_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id"), index=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), index=True)

    employee = relationship("Employee", back_populates="room_memberships")
    room = relationship("Room", back_populates="members")
