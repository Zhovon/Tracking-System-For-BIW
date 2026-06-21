from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Response
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app import models, schemas

router = APIRouter()

@router.get("/rooms", response_model=List[schemas.RoomOut])
def get_my_rooms(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Retrieve all rooms the current user is a member of.
    """
    rooms = [membership.room for membership in current_user.room_memberships if membership.room.is_active]
    return rooms

@router.get("", response_model=List[schemas.TicketOut])
def get_tickets(
    room_id: UUID = None,
    assignee_staff_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Retrieve tickets. Enforces Clinic Row-Level Security:
    - Owners: See all.
    - Manager/HR/IT: See created by them or assigned to them.
    - Staff: See ONLY assigned to them.
    """
    query = db.query(models.Ticket).filter(models.Ticket.is_active == True)

    if current_user.role == "owner":
        # Owners see everything
        pass
    elif current_user.role in ["manager", "hr", "it_team"]:
        # Creators/Managers see what they made or what is assigned to them
        query = query.filter(
            (models.Ticket.creator_id == current_user.id) | 
            (models.Ticket.assigned_to_id == current_user.id)
        )
    else:
        # Staff ONLY see what is assigned to them
        query = query.filter(models.Ticket.assigned_to_id == current_user.id)

    if room_id:
        query = query.join(models.TicketRoom).filter(models.TicketRoom.room_id == room_id)

    if assignee_staff_id:
        # Join assignee to filter by their staff_id tag
        query = query.join(models.Employee, models.Ticket.assigned_to_id == models.Employee.id).filter(models.Employee.staff_id == assignee_staff_id)
        
    if status:
        try:
            status_enum = models.TicketStatus[status]
            query = query.filter(models.Ticket.status == status_enum)
        except KeyError:
            pass

    tickets = query.offset(skip).limit(limit).all()
    return tickets

@router.post("", response_model=schemas.TicketOut)
def create_ticket(
    *,
    db: Session = Depends(get_db),
    ticket_in: schemas.TicketCreate,
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Create new ticket. Only Managers, HR, IT, and Owners can create.
    """
    if current_user.role not in ["owner", "manager", "hr", "it_team"]:
        raise HTTPException(status_code=403, detail="Staff cannot create tickets. They can only resolve assigned tasks.")

    approval_status = models.ApprovalStatus.approved if current_user.role == "owner" else models.ApprovalStatus.pending

    ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        priority=ticket_in.priority,
        creator_id=current_user.id,
        approval_status=approval_status,
        assigned_to_id=ticket_in.assigned_to_id
    )
    db.add(ticket)
    db.flush() # flush to get ticket ID

    # Link ticket to rooms
    for r_id in ticket_in.room_ids:
        ticket_room = models.TicketRoom(ticket_id=ticket.id, room_id=r_id)
        db.add(ticket_room)

    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/{ticket_id}", response_model=schemas.TicketDetailOut)
def get_ticket(
    *,
    db: Session = Depends(get_db),
    ticket_id: UUID,
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Get a specific ticket by ID with its messages thread.
    Enforces RLS.
    """
    from sqlalchemy.orm import selectinload
    ticket = db.query(models.Ticket)\
        .options(selectinload(models.Ticket.messages))\
        .options(selectinload(models.Ticket.room_links).joinedload(models.TicketRoom.room))\
        .filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security Check
    if current_user.role != "owner":
        if current_user.role in ["manager", "hr", "it_team"]:
            if ticket.creator_id != current_user.id and ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
        else:
            if ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this ticket")

    ticket.rooms = [link.room for link in ticket.room_links]
    return ticket

@router.post("/{ticket_id}/messages", response_model=schemas.MessageOut)
async def post_message(
    *,
    db: Session = Depends(get_db),
    ticket_id: UUID,
    content: str = Form(...),
    type: models.MessageType = Form(models.MessageType.comment),
    file: UploadFile = File(None),
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Post a new message to a ticket thread with optional file attachment.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security check
    if current_user.role != "owner":
        if current_user.role in ["manager", "hr", "it_team"]:
            if ticket.creator_id != current_user.id and ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to comment on this ticket")
        else:
            if ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to comment on this ticket")

    attachment_data = None
    attachment_name = None
    attachment_type = None
    
    if file:
        attachment_data = await file.read()
        attachment_name = file.filename
        attachment_type = file.content_type

    message = models.Message(
        ticket_id=ticket_id,
        author_id=current_user.id,
        content=content,
        type=type,
        attachment_data=attachment_data,
        attachment_name=attachment_name,
        attachment_type=attachment_type
    )
    db.add(message)
    
    # Notifications logic
    users_to_notify = set()
    if ticket.creator_id and ticket.creator_id != current_user.id:
        users_to_notify.add(ticket.creator_id)
    if ticket.assigned_to_id and ticket.assigned_to_id != current_user.id:
        users_to_notify.add(ticket.assigned_to_id)
        
    for user_id in users_to_notify:
        notification = models.Notification(
            user_id=user_id,
            message=f"New message on ticket: {ticket.title}"
        )
        db.add(notification)

    db.commit()
    db.refresh(message)
    return message

@router.get("/messages/{message_id}/attachment")
def get_message_attachment(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Download an attachment from a message.
    """
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message or not message.attachment_data:
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    # Check access to ticket
    ticket = db.query(models.Ticket).filter(models.Ticket.id == message.ticket_id).first()
    if current_user.role != "owner":
        if current_user.role in ["manager", "hr", "it_team"]:
            if ticket.creator_id != current_user.id and ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
        else:
            if ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to view this ticket")

    return Response(
        content=message.attachment_data, 
        media_type=message.attachment_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=\"{message.attachment_name}\""}
    )

@router.patch("/{ticket_id}", response_model=schemas.TicketOut)
def update_ticket(
    *,
    db: Session = Depends(get_db),
    ticket_id: UUID,
    ticket_in: schemas.TicketUpdate,
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Update ticket status or priority. Also generates a system message.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security check
    if current_user.role != "owner":
        if current_user.role in ["manager", "hr", "it_team"]:
            if ticket.creator_id != current_user.id and ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to modify this ticket")
        else:
            if ticket.assigned_to_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized to modify this ticket")

    # Update logic and system message generation
    if ticket_in.status is not None and ticket_in.status != ticket.status:
        system_msg = models.Message(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=f"Status changed from {ticket.status.value} to {ticket_in.status.value}",
            type=models.MessageType.status_update
        )
        db.add(system_msg)
        ticket.status = ticket_in.status

    if ticket_in.priority is not None and ticket_in.priority != ticket.priority:
        system_msg = models.Message(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=f"Priority changed from {ticket.priority.value} to {ticket_in.priority.value}",
            type=models.MessageType.status_update
        )
        db.add(system_msg)
        ticket.priority = ticket_in.priority

    if ticket_in.assigned_to_id is not None and ticket_in.assigned_to_id != ticket.assigned_to_id:
        assignee = db.query(models.Employee).filter(models.Employee.id == ticket_in.assigned_to_id).first()
        if assignee:
            system_msg = models.Message(
                ticket_id=ticket.id,
                author_id=current_user.id,
                content=f"Assigned ticket to {assignee.name}",
                type=models.MessageType.status_update
            )
            db.add(system_msg)
            ticket.assigned_to_id = assignee.id
            
    if ticket_in.add_room_id is not None:
        # Check if room is already linked
        existing_link = db.query(models.TicketRoom).filter_by(ticket_id=ticket.id, room_id=ticket_in.add_room_id).first()
        if not existing_link:
            room = db.query(models.Room).filter(models.Room.id == ticket_in.add_room_id).first()
            if room:
                new_link = models.TicketRoom(ticket_id=ticket.id, room_id=room.id)
                db.add(new_link)
                system_msg = models.Message(
                    ticket_id=ticket.id,
                    author_id=current_user.id,
                    content=f"Escalated ticket to room: {room.name}",
                    type=models.MessageType.status_update
                )
                db.add(system_msg)

    db.commit()
    db.refresh(ticket)
    return ticket

@router.patch("/{ticket_id}/approve", response_model=schemas.TicketOut)
def approve_ticket(
    *,
    db: Session = Depends(get_db),
    ticket_id: UUID,
    current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Approve a pending ticket. Only Owners can do this.
    """
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can approve tickets")

    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.approval_status == models.ApprovalStatus.approved:
        raise HTTPException(status_code=400, detail="Ticket is already approved")

    ticket.approval_status = models.ApprovalStatus.approved
    ticket.approved_by_id = current_user.id
    
    system_msg = models.Message(
        ticket_id=ticket.id,
        author_id=current_user.id,
        content="Approved the ticket.",
        type=models.MessageType.approval
    )
    db.add(system_msg)

    db.commit()
    db.refresh(ticket)
    return ticket
