from typing import Any, List
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from sqlalchemy.orm import Session

from app import models, schemas
from app.api.deps import get_current_user, get_db
from app.database import SessionLocal
from app.domains.notifications.push import send_web_push

router = APIRouter()


def dispatch_notification(db: Session, background_tasks: BackgroundTasks, user_id: UUID, ticket_id: UUID, message: str):
    notif = models.Notification(user_id=user_id, ticket_id=ticket_id, message=message)
    db.add(notif)

    def _send():
        bg_db = SessionLocal()
        try:
            subs = bg_db.query(models.PushSubscription).filter(models.PushSubscription.user_id == user_id).all()
            for sub in subs:
                send_web_push(
                    {"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                    {"title": "New Update", "body": message, "url": f"/dashboard?ticket_id={ticket_id}"}
                )
        finally:
            bg_db.close()

    if background_tasks:
        background_tasks.add_task(_send)



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

    if current_user.role == "owner":
        # Owners see all active tickets
        pass
    else:
        # Non-owners see ONLY tickets they participated in (created or assigned to), or in universal rooms
        user_participated_tickets = (
            db.query(models.TicketParticipant.ticket_id)
            .filter(models.TicketParticipant.employee_id == current_user.id)
        )
        query = query.filter(
            models.Ticket.id.in_(user_participated_tickets)
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
    background_tasks: BackgroundTasks) -> Any:
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

    # Add initial participants (creator and assignee)
    db.add(models.TicketParticipant(ticket_id=ticket.id, employee_id=current_user.id))
    if ticket.assigned_to_id and ticket.assigned_to_id != current_user.id:
        db.add(models.TicketParticipant(ticket_id=ticket.id, employee_id=ticket.assigned_to_id))

    # Track who we have notified to avoid duplicates
    notified_user_ids = {current_user.id}

    # Check if this is a universal ticket
    is_universal = db.query(models.Room).filter(
        models.Room.id.in_(ticket_in.room_ids),
        models.Room.type == models.RoomType.universal
    ).first() is not None

    if is_universal:
        # Notify ALL active staff
        all_staff = db.query(models.Employee).filter(models.Employee.is_active == True).all()
        for staff in all_staff:
            if staff.id not in notified_user_ids:
                dispatch_notification(db, background_tasks, staff.id, ticket.id, f"📢 New Universal Announcement: {ticket.title}")
                notified_user_ids.add(staff.id)
    else:
        # Notify all Owners
        owners = db.query(models.Employee).filter(models.Employee.role == "owner").all()
        
        assignee_name = ""
        if ticket.assigned_to_id:
            assignee = db.query(models.Employee).filter(models.Employee.id == ticket.assigned_to_id).first()
            if assignee:
                assignee_name = assignee.name

        for owner in owners:
            if owner.id not in notified_user_ids:
                if ticket.approval_status == models.ApprovalStatus.pending:
                    msg = f"New ticket requires approval: {ticket.title}"
                elif assignee_name:
                    msg = f"New ticket created (assigned to {assignee_name}): {ticket.title}"
                else:
                    msg = f"New ticket created: {ticket.title}"

                dispatch_notification(db, background_tasks, owner.id, ticket.id, msg)
                notified_user_ids.add(owner.id)

    # Notify Assignee
    if ticket.assigned_to_id and ticket.assigned_to_id not in notified_user_ids:
        dispatch_notification(db, background_tasks, ticket.assigned_to_id, ticket.id, f"You have been assigned to a new ticket: {ticket.title}")
        notified_user_ids.add(ticket.assigned_to_id)

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
    if current_user.role != "owner":
        is_participant = db.query(models.TicketParticipant).filter(
            models.TicketParticipant.ticket_id == ticket.id,
            models.TicketParticipant.employee_id == current_user.id
        ).first() is not None
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_participant and not is_universal:
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
    background_tasks: BackgroundTasks) -> Any:
    """
    Post a new message to a ticket thread with optional file attachment.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security check
    if current_user.role != "owner":
        is_participant = db.query(models.TicketParticipant).filter(
            models.TicketParticipant.ticket_id == ticket.id,
            models.TicketParticipant.employee_id == current_user.id
        ).first() is not None
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_participant and not is_universal:
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
        dispatch_notification(db, background_tasks, user_id, ticket.id, f"New response by {current_user.name} on ticket: {ticket.title}")

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
    if current_user.role != "owner":
        is_participant = db.query(models.TicketParticipant).filter(
            models.TicketParticipant.ticket_id == ticket.id,
            models.TicketParticipant.employee_id == current_user.id
        ).first() is not None

        # Check if it's in a universal room
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_participant and not is_universal:
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
    background_tasks: BackgroundTasks) -> Any:
    """
    Update ticket status or priority. Also generates a system message.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket or not ticket.is_active:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Security check
    if current_user.role != "owner":
        is_participant = db.query(models.TicketParticipant).filter(
            models.TicketParticipant.ticket_id == ticket.id,
            models.TicketParticipant.employee_id == current_user.id
        ).first() is not None
        is_universal = any(link.room.type == models.RoomType.universal for link in ticket.room_links)

        if not is_participant and not is_universal:
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

                # Add new assignee to ticket participants if not already
                is_existing_participant = db.query(models.TicketParticipant).filter(
                    models.TicketParticipant.ticket_id == ticket.id,
                    models.TicketParticipant.employee_id == assignee.id
                ).first() is not None

                if not is_existing_participant:
                    db.add(models.TicketParticipant(ticket_id=ticket.id, employee_id=assignee.id))

                # Notify newly assigned employee
                if assignee.id != current_user.id:
                    dispatch_notification(db, background_tasks, assignee.id, ticket.id, f"You have been assigned to ticket: {ticket.title}")

                # Notify all Owners
                owners = db.query(models.Employee).filter(models.Employee.role == "owner").all()
                for owner in owners:
                    if owner.id != current_user.id:
                        dispatch_notification(db, background_tasks, owner.id, ticket.id, f"Ticket '{ticket.title}' assigned to {assignee.name}")

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
    background_tasks: BackgroundTasks
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
        dispatch_notification(db, background_tasks, ticket.creator_id, ticket.id, f"Your ticket has been approved: {ticket.title}")

    # Notify assignee
    if ticket.assigned_to_id and ticket.assigned_to_id != current_user.id:
        dispatch_notification(db, background_tasks, ticket.assigned_to_id, ticket.id, f"Approved ticket assigned to you: {ticket.title}")

    db.commit()
    db.refresh(ticket)
    return ticket
