from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user, get_db

router = APIRouter()


@router.get("/rooms", response_model=List[schemas.RoomOut])
def get_my_rooms(
    db: Session = Depends(get_db), current_user: models.Employee = Depends(get_current_user)
) -> Any:
    """
    Retrieve all rooms the current user is a member of.
    """
    if current_user.role == "owner":
        rooms = db.query(models.Room).filter(models.Room.is_active == True).all()
    else:
        user_rooms = [
            membership.room for membership in current_user.room_memberships if membership.room.is_active
        ]
        universal_rooms = db.query(models.Room).filter(
            models.Room.type == models.RoomType.universal, models.Room.is_active == True
        ).all()
        # Combine without duplicates
        rooms_dict = {r.id: r for r in user_rooms + universal_rooms}
        rooms = list(rooms_dict.values())
    return rooms


@router.get("", response_model=List[schemas.TicketOut])
def get_tickets(
    room_id: UUID = None,
    assignee_staff_id: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Retrieve tickets. Enforces Clinic Row-Level Security:
    - Owners: See all.
    - Manager/HR/IT: See created by them or assigned to them.
    - Staff: See ONLY assigned to them.
    """
    from sqlalchemy.orm import selectinload
    query = db.query(models.Ticket).filter(models.Ticket.is_active == True).options(
        selectinload(models.Ticket.creator).selectinload(models.Employee.room_memberships),
        selectinload(models.Ticket.creator).selectinload(models.Employee.assigned_tickets),
        selectinload(models.Ticket.assignee).selectinload(models.Employee.room_memberships),
        selectinload(models.Ticket.assignee).selectinload(models.Employee.assigned_tickets),
    )

    # Subquery to find tickets linked to universal rooms
    universal_room_tickets = (
        db.query(models.TicketRoom.ticket_id)
        .join(models.Room)
        .filter(models.Room.type == models.RoomType.universal)
    )

    if current_user.role in ["owner", "hr", "it_team", "executive"]:
        # See all active tickets
        pass
    else:
        user_room_ids = [m.room_id for m in current_user.room_memberships]
        user_room_tickets = (
            db.query(models.TicketRoom.ticket_id)
            .filter(models.TicketRoom.room_id.in_(user_room_ids))
        )
        if room_id:
            # When viewing a specific room, check room memberships
            query = query.filter(
                (models.Ticket.creator_id == current_user.id)
                | (models.Ticket.assigned_to_id == current_user.id)
                | models.Ticket.id.in_(universal_room_tickets)
                | models.Ticket.id.in_(user_room_tickets)
            )
        else:
            # "All Tickets" view (no room_id selected)
            if current_user.role == "manager":
                # Managers see all tickets in their rooms + created/assigned
                query = query.filter(
                    (models.Ticket.creator_id == current_user.id)
                    | (models.Ticket.assigned_to_id == current_user.id)
                    | models.Ticket.id.in_(universal_room_tickets)
                    | models.Ticket.id.in_(user_room_tickets)
                )
            else:
                # Standard staff see only tickets assigned to them (+ universal announcements)
                query = query.filter(
                    (models.Ticket.assigned_to_id == current_user.id)
                    | models.Ticket.id.in_(universal_room_tickets)
                )

    if room_id:
        query = query.join(models.TicketRoom).filter(models.TicketRoom.room_id == room_id)

    if assignee_staff_id:
        search_pattern = f"%{assignee_staff_id.strip()}%"
        # Join assignee to filter by their staff_id tag or their name
        query = query.join(
            models.Employee, models.Ticket.assigned_to_id == models.Employee.id
        ).filter(
            models.Employee.staff_id.ilike(search_pattern) |
            models.Employee.name.ilike(search_pattern)
        )

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
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Create new ticket. Only Managers, HR, IT, and Owners can create.
    """
    if current_user.role not in ["owner", "manager", "hr", "it_team"]:
        raise HTTPException(
            status_code=403,
            detail="Staff cannot create tickets. They can only resolve assigned tasks.",
        )

    approval_status = (
        models.ApprovalStatus.approved
        if current_user.role == "owner"
        else models.ApprovalStatus.pending
    )

    ticket = models.Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        priority=ticket_in.priority,
        creator_id=current_user.id,
        approval_status=approval_status,
        assigned_to_id=ticket_in.assigned_to_id,
        due_date=ticket_in.due_date,
    )
    db.add(ticket)
    db.flush()  # flush to get ticket ID

    # Link ticket to rooms
    for r_id in ticket_in.room_ids:
        ticket_room = models.TicketRoom(ticket_id=ticket.id, room_id=r_id)
        db.add(ticket_room)

    # Notify all Owners
    owners = db.query(models.Employee).filter(models.Employee.role == "owner").all()

    # Get assignee name if exists
    assignee_name = ""
    if ticket.assigned_to_id:
        assignee = db.query(models.Employee).filter(models.Employee.id == ticket.assigned_to_id).first()
        if assignee:
            assignee_name = assignee.name

    for owner in owners:
        if owner.id != current_user.id:
            if ticket.approval_status == models.ApprovalStatus.pending:
                msg = f"New ticket requires approval: {ticket.title}"
            elif assignee_name:
                msg = f"New ticket created (assigned to {assignee_name}): {ticket.title}"
            else:
                msg = f"New ticket created: {ticket.title}"

            db.add(models.Notification(
                user_id=owner.id,
                message=msg
            ))

    # Notify Assignee
    if ticket.assigned_to_id and ticket.assigned_to_id != current_user.id:
        db.add(models.Notification(
            user_id=ticket.assigned_to_id,
            message=f"You have been assigned to a new ticket: {ticket.title}"
        ))

    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=schemas.TicketDetailOut)
def get_ticket(
    *,
    db: Session = Depends(get_db),
    ticket_id: UUID,
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Get a specific ticket by ID with its messages thread.
    Enforces RLS.
    """
    from sqlalchemy.orm import selectinload

    ticket = (
        db.query(models.Ticket)
        .options(selectinload(models.Ticket.messages))
        .options(selectinload(models.Ticket.room_links).joinedload(models.TicketRoom.room))
        .filter(models.Ticket.id == ticket_id)
        .first()
    )
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security Check
    if current_user.role not in ["owner", "hr", "it_team", "executive"]:
        is_creator_or_assignee = (ticket.creator_id == current_user.id or ticket.assigned_to_id == current_user.id)
        ticket_room_ids = {link.room_id for link in ticket.room_links}
        user_room_ids = {m.room_id for m in current_user.room_memberships}
        has_room_access = bool(ticket_room_ids & user_room_ids)
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_creator_or_assignee and not has_room_access and not is_universal:
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
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Post a new message to a ticket thread with optional file attachment.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security check
    if current_user.role not in ["owner", "hr", "it_team", "executive"]:
        is_creator_or_assignee = (ticket.creator_id == current_user.id or ticket.assigned_to_id == current_user.id)
        ticket_room_ids = {link.room_id for link in ticket.room_links}
        user_room_ids = {m.room_id for m in current_user.room_memberships}
        has_room_access = bool(ticket_room_ids & user_room_ids)
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_creator_or_assignee and not has_room_access and not is_universal:
            raise HTTPException(
                status_code=403, detail="Not authorized to comment on this ticket"
            )

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
        attachment_type=attachment_type,
    )
    db.add(message)

    # Notifications logic
    users_to_notify = set()
    if ticket.creator_id and ticket.creator_id != current_user.id:
        users_to_notify.add(ticket.creator_id)
    if ticket.assigned_to_id and ticket.assigned_to_id != current_user.id:
        users_to_notify.add(ticket.assigned_to_id)

    # Notify all Owners as well
    owners = db.query(models.Employee).filter(models.Employee.role == "owner").all()
    for owner in owners:
        if owner.id != current_user.id:
            users_to_notify.add(owner.id)

    for user_id in users_to_notify:
        notification = models.Notification(
            user_id=user_id, message=f"New response by {current_user.name} on ticket: {ticket.title}"
        )
        db.add(notification)

    db.commit()
    db.refresh(message)
    return message


@router.get("/messages/{message_id}/attachment")
def get_message_attachment(
    message_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Download an attachment from a message.
    """
    message = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not message or not message.attachment_data:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Check access to ticket
    ticket = db.query(models.Ticket).filter(models.Ticket.id == message.ticket_id).first()
    if current_user.role not in ["owner", "hr", "it_team", "executive"]:
        # Check if user is creator or assignee
        is_creator_or_assignee = (ticket.creator_id == current_user.id or ticket.assigned_to_id == current_user.id)

        # Check if user belongs to any of the rooms the ticket is linked to
        ticket_room_ids = {link.room_id for link in ticket.room_links}
        user_room_ids = {m.room_id for m in current_user.room_memberships}
        has_room_access = bool(ticket_room_ids & user_room_ids)

        # Check if it's in a universal room
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_creator_or_assignee and not has_room_access and not is_universal:
            raise HTTPException(status_code=403, detail="Not authorized to access this attachment")

    return Response(
        content=message.attachment_data,
        media_type=message.attachment_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{message.attachment_name}"'},
    )


@router.patch("/{ticket_id}", response_model=schemas.TicketOut)
def update_ticket(
    *,
    db: Session = Depends(get_db),
    ticket_id: UUID,
    ticket_in: schemas.TicketUpdate,
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Update ticket status or priority. Also generates a system message.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security check
    if current_user.role not in ["owner", "hr", "it_team", "executive"]:
        is_creator_or_assignee = (ticket.creator_id == current_user.id or ticket.assigned_to_id == current_user.id)
        ticket_room_ids = {link.room_id for link in ticket.room_links}
        user_room_ids = {m.room_id for m in current_user.room_memberships}
        has_room_access = bool(ticket_room_ids & user_room_ids)
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_creator_or_assignee and not has_room_access and not is_universal:
            raise HTTPException(status_code=403, detail="Not authorized to modify this ticket")

    # Update logic and system message generation
    if ticket_in.status is not None and ticket_in.status != ticket.status:
        system_msg = models.Message(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=f"Status changed from {ticket.status.value} to {ticket_in.status.value}",
            type=models.MessageType.status_update,
        )
        db.add(system_msg)
        ticket.status = ticket_in.status

    if ticket_in.priority is not None and ticket_in.priority != ticket.priority:
        system_msg = models.Message(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=f"Priority changed from {ticket.priority.value} to {ticket_in.priority.value}",
            type=models.MessageType.status_update,
        )
        db.add(system_msg)
        ticket.priority = ticket_in.priority

    if "assigned_to_id" in ticket_in.model_fields_set:
        if ticket_in.assigned_to_id is None:
            if ticket.assigned_to_id is not None:
                system_msg = models.Message(
                    ticket_id=ticket.id,
                    author_id=current_user.id,
                    content="Unassigned ticket",
                    type=models.MessageType.status_update,
                )
                db.add(system_msg)
            ticket.assigned_to_id = None
        elif ticket_in.assigned_to_id != ticket.assigned_to_id:
            assignee = (
                db.query(models.Employee).filter(models.Employee.id == ticket_in.assigned_to_id).first()
            )
            if assignee:
                system_msg = models.Message(
                    ticket_id=ticket.id,
                    author_id=current_user.id,
                    content=f"Assigned ticket to {assignee.name}",
                    type=models.MessageType.status_update,
                )
                db.add(system_msg)
                ticket.assigned_to_id = assignee.id

                # Notify newly assigned employee
                if assignee.id != current_user.id:
                    db.add(models.Notification(
                        user_id=assignee.id,
                        message=f"You have been assigned to ticket: {ticket.title}"
                    ))

                # Notify all Owners
                owners = db.query(models.Employee).filter(models.Employee.role == "owner").all()
                for owner in owners:
                    if owner.id != current_user.id:
                        db.add(models.Notification(
                            user_id=owner.id,
                            message=f"Ticket '{ticket.title}' assigned to {assignee.name}"
                        ))

    if "due_date" in ticket_in.model_fields_set and ticket_in.due_date != ticket.due_date:
        ticket.due_date = ticket_in.due_date
        if ticket_in.due_date:
            due_str = ticket_in.due_date.strftime("%d %b %Y, %H:%M")
            content = f"Due date set to {due_str}"
        else:
            content = "Removed due date"
        system_msg = models.Message(
            ticket_id=ticket.id,
            author_id=current_user.id,
            content=content,
            type=models.MessageType.status_update,
        )
        db.add(system_msg)

    if ticket_in.add_room_id is not None:
        # Check if room is already linked
        existing_link = (
            db.query(models.TicketRoom)
            .filter_by(ticket_id=ticket.id, room_id=ticket_in.add_room_id)
            .first()
        )
        if not existing_link:
            room = db.query(models.Room).filter(models.Room.id == ticket_in.add_room_id).first()
            if room:
                new_link = models.TicketRoom(ticket_id=ticket.id, room_id=room.id)
                db.add(new_link)
                system_msg = models.Message(
                    ticket_id=ticket.id,
                    author_id=current_user.id,
                    content=f"Escalated ticket to room: {room.name}",
                    type=models.MessageType.status_update,
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
    current_user: models.Employee = Depends(get_current_user),
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
        type=models.MessageType.approval,
    )
    db.add(system_msg)

    # Notify creator
    if ticket.creator_id and ticket.creator_id != current_user.id:
        db.add(models.Notification(
            user_id=ticket.creator_id,
            message=f"Your ticket has been approved: {ticket.title}"
        ))

    # Notify assignee
    if ticket.assigned_to_id and ticket.assigned_to_id != current_user.id:
        db.add(models.Notification(
            user_id=ticket.assigned_to_id,
            message=f"Approved ticket assigned to you: {ticket.title}"
        ))

    db.commit()
    db.refresh(ticket)
    return ticket
