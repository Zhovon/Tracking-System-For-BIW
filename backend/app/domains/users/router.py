import os
import uuid
from typing import Any, List

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from supabase import Client, create_client

from app import models, schemas
from app.api.deps import get_current_user, get_db
from app.config import settings

router = APIRouter()


def sync_user_to_google_sheet(action: str, email: str, name: str = "", role: str = "", password: str = "", uid: str = "", phn_num: str = "", joining_date: str = ""):
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    if not webhook_url:
        return
    try:
        payload = {
            "action": action,
            "email": email,
            "name": name,
            "role": role,
            "password": password,
            "uid": uid,
            "phn_num": phn_num,
            "joining_date": joining_date
        }
        # Send post request to Apps Script Web App
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        print(f"Google Sheet Sync ({action} for {email}): Status {response.status_code}")
    except Exception as e:
        print(f"Failed to sync user to Google Sheet: {e}")


@router.get("/me", response_model=schemas.UserOut)
def get_current_user_profile(current_user: models.Employee = Depends(get_current_user)) -> Any:
    """
    Get current logged in user profile.
    """
    return current_user


@router.get("", response_model=List[schemas.UserOut])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Get all employees. Scoped by role:
    - Owners, HR, IT Support, Executives see all.
    - Managers see only employees sharing branch rooms they manage.
    """
    if current_user.role in ["owner", "hr", "it_team", "executive"]:
        return db.query(models.Employee).filter(models.Employee.is_active == True).all()
    elif current_user.role == "manager":
        # Find all branch rooms this manager is a member of
        manager_branch_ids = [
            m.room_id for m in current_user.room_memberships
            if m.room.type == models.RoomType.branch
        ]
        if not manager_branch_ids:
            return []

        # Query employees belonging to these branch rooms
        return (
            db.query(models.Employee)
            .join(models.RoomMember, models.Employee.id == models.RoomMember.employee_id)
            .filter(
                models.Employee.is_active == True,
                models.RoomMember.room_id.in_(manager_branch_ids),
            )
            .distinct()
            .all()
        )
    else:
        return db.query(models.Employee).filter(models.Employee.is_active == True).all()





@router.post("", response_model=schemas.UserOut)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Create new staff user. Only Owners can create accounts.
    """
    import uuid

    from fastapi import HTTPException
    from supabase import Client, create_client
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Only owners and managers can create new staff accounts")

    if current_user.role == "manager":
        # Managers can only create standard non-admin staff roles (therapist, cleaner, it_team)
        if user_in.role in ["owner", "manager", "hr", "executive"]:
            raise HTTPException(
                status_code=403,
                detail="Managers can only create standard staff (therapist, cleaner, or IT Support)"
            )

        # Managers must assign staff to branches they are members of
        manager_branch_ids = [
            m.room_id for m in current_user.room_memberships
            if m.room.type == models.RoomType.branch
        ]
        if not user_in.room_ids:
            raise HTTPException(status_code=400, detail="Managers must assign new staff to at least one branch")

        for r_id in user_in.room_ids:
            if r_id not in manager_branch_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Managers can only assign staff to branches they manage"
                )

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase admin keys not configured")

    supabase_admin: Client = create_client(supabase_url, supabase_key)

    # Pre-flight: check if email already exists in local DB
    existing = db.query(models.Employee).filter(
        models.Employee.email == user_in.email.lower().strip()
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"An account with the email '{user_in.email}' already exists in the system."
        )

    try:
        # Create user in Supabase Auth
        # Admin API bypasses signup restrictions and email confirmation
        res = supabase_admin.auth.admin.create_user(
            {
                "email": user_in.email,
                "password": user_in.password,
                "email_confirm": True,
                "user_metadata": {"name": user_in.name, "role": user_in.role},
            }
        )

        new_uuid = res.user.id

        # Generate staff_id
        from sqlalchemy import text

        seq_val = db.execute(text("SELECT nextval('staff_id_seq')")).scalar()
        staff_id_str = str(seq_val).zfill(4)

        # Create Employee in local DB with exactly the same UUID
        employee = models.Employee(
            id=uuid.UUID(new_uuid),
            staff_id=staff_id_str,
            email=user_in.email,
            name=user_in.name,
            role=user_in.role,
            phone=user_in.phone,
            nid=user_in.nid,
            joining_date=user_in.joining_date,
        )
        db.add(employee)

        # Link to the selected rooms
        if user_in.room_ids:
            for r_id in user_in.room_ids:
                room_membership = models.RoomMember(employee_id=employee.id, room_id=r_id)
                db.add(room_membership)

        db.commit()
        db.refresh(employee)

        # Trigger Google Sheet sync in background
        background_tasks.add_task(
            sync_user_to_google_sheet,
            action="create",
            email=employee.email,
            name=employee.name,
            role=employee.role,
            password=user_in.password,
            uid=employee.staff_id,
            phn_num=employee.phone if employee.phone else "",
            joining_date=employee.joining_date if employee.joining_date else ""
        )

        return employee

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        err_str = str(e).lower()
        # Supabase Auth already has this email (ghost/orphaned account from testing/imports)
        # but our local DB has no record — recover by reusing the existing Auth UUID
        if "already been registered" in err_str or "already registered" in err_str or "email address" in err_str:
            try:
                # Find the existing auth user by email
                all_users = supabase_admin.auth.admin.list_users()
                user_list = all_users if isinstance(all_users, list) else getattr(all_users, "users", [])
                existing_auth = next((u for u in user_list if u.email == user_in.email), None)

                if not existing_auth:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Email '{user_in.email}' is blocked in the auth system. Please contact IT support to resolve."
                    )

                # Update the auth user's password and metadata to match what was requested
                supabase_admin.auth.admin.update_user_by_id(
                    str(existing_auth.id),
                    {
                        "password": user_in.password,
                        "email_confirm": True,
                        "user_metadata": {"name": user_in.name, "role": user_in.role}
                    }
                )

                # Generate a new staff_id for the recovered account
                from sqlalchemy import text
                seq_val = db.execute(text("SELECT nextval('staff_id_seq')")).scalar()
                staff_id_str = str(seq_val).zfill(4)

                # Create a fresh local DB record using the existing Auth UUID
                employee = models.Employee(
                    id=uuid.UUID(str(existing_auth.id)),
                    staff_id=staff_id_str,
                    email=user_in.email,
                    name=user_in.name,
                    role=user_in.role,
                    phone=user_in.phone,
                    nid=user_in.nid,
                    joining_date=user_in.joining_date,
                )
                db.add(employee)

                if user_in.room_ids:
                    for r_id in user_in.room_ids:
                        db.add(models.RoomMember(employee_id=employee.id, room_id=r_id))

                db.commit()
                db.refresh(employee)

                background_tasks.add_task(
                    sync_user_to_google_sheet,
                    action="create",
                    email=employee.email,
                    name=employee.name,
                    role=employee.role,
                    password=user_in.password,
                    uid=employee.staff_id,
                    phn_num=employee.phone if employee.phone else "",
                    joining_date=employee.joining_date if employee.joining_date else ""
                )

                return employee

            except HTTPException:
                raise
            except Exception as recovery_err:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not recover orphaned account for '{user_in.email}': {recovery_err}"
                )

        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_id}", response_model=schemas.UserOut)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    user_in: schemas.UserUpdate,
    background_tasks: BackgroundTasks,
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Update a staff user. Only Owners can update accounts.
    """
    employee = db.query(models.Employee).filter(models.Employee.id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role != "owner":
        if current_user.role == "manager":
            # Managers can edit standard staff in branches they manage
            manager_branch_ids = [
                m.room_id for m in current_user.room_memberships
                if m.room.type == models.RoomType.branch
            ]

            # Check if target employee shares a branch with the manager
            has_common_branch = db.query(models.RoomMember).filter(
                models.RoomMember.employee_id == employee.id,
                models.RoomMember.room_id.in_(manager_branch_ids)
            ).first() is not None

            if not has_common_branch:
                raise HTTPException(status_code=403, detail="Not authorized to edit staff outside your branch")

            # Managers cannot edit other managers or owners
            if employee.role in ["owner", "manager"] and current_user.id != user_id:
                raise HTTPException(status_code=403, detail="Managers cannot edit owner or other manager accounts")

            # If changing role, manager can only assign standard staff roles
            if user_in.role is not None and user_in.role in ["owner", "manager", "hr", "executive"]:
                raise HTTPException(status_code=403, detail="Managers cannot assign administrative or manager roles")

            # If changing branches, manager can only assign rooms they manage
            if user_in.room_ids is not None:
                for r_id in user_in.room_ids:
                    if r_id not in manager_branch_ids:
                        raise HTTPException(status_code=403, detail="Managers can only assign staff to branches they manage")
        else:
            # Standard employees editing their own accounts
            if current_user.id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized to edit this account")
            if user_in.role is not None and user_in.role != employee.role:
                raise HTTPException(status_code=403, detail="Not authorized to change your own role")
            if user_in.room_ids is not None:
                raise HTTPException(status_code=403, detail="Not authorized to change your own branch assignments")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase_admin: Client = create_client(supabase_url, supabase_key)

    try:
        # Update user in Supabase Auth
        update_data = {}
        if user_in.email is not None:
            update_data["email"] = user_in.email
            update_data["email_confirm"] = True
        if user_in.password is not None and len(user_in.password) > 0:
            update_data["password"] = user_in.password

        user_metadata = {}
        if user_in.name is not None:
            user_metadata["name"] = user_in.name
            employee.name = user_in.name
        if user_in.role is not None:
            user_metadata["role"] = user_in.role
            employee.role = user_in.role
        if user_in.phone is not None:
            employee.phone = user_in.phone
        if user_in.nid is not None:
            employee.nid = user_in.nid
        if user_in.joining_date is not None:
            employee.joining_date = user_in.joining_date

        if user_metadata:
            update_data["user_metadata"] = user_metadata

        if update_data:
            supabase_admin.auth.admin.update_user_by_id(str(user_id), update_data)

        if user_in.email is not None:
            employee.email = user_in.email

        if user_in.room_ids is not None:
            if current_user.role == "manager":
                manager_branch_ids = [
                    m.room_id for m in current_user.room_memberships
                    if m.room.type == models.RoomType.branch
                ]
                # Non-managed room IDs: keep them!
                existing_non_managed = db.query(models.RoomMember).filter(
                    models.RoomMember.employee_id == employee.id,
                    ~models.RoomMember.room_id.in_(manager_branch_ids)
                ).all()
                non_managed_ids = [m.room_id for m in existing_non_managed]

                # Full merged list
                final_room_ids = list(set(non_managed_ids + user_in.room_ids))
            else:
                final_room_ids = user_in.room_ids

            db.query(models.RoomMember).filter(
                models.RoomMember.employee_id == employee.id
            ).delete()
            for r_id in final_room_ids:
                new_membership = models.RoomMember(employee_id=employee.id, room_id=r_id)
                db.add(new_membership)

        db.commit()
        db.refresh(employee)

        # Trigger Google Sheet sync in background
        background_tasks.add_task(
            sync_user_to_google_sheet,
            action="update",
            email=employee.email,
            name=employee.name,
            role=employee.role,
            password=user_in.password if user_in.password else "",
            uid=employee.staff_id,
            phn_num=employee.phone if employee.phone else "",
            joining_date=employee.joining_date if employee.joining_date else ""
        )

        return employee

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: models.Employee = Depends(get_current_user),
) -> Any:
    """
    Delete a staff user. Soft deletes local record, hard deletes Supabase auth record.
    """
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Only owners and managers can delete staff accounts")

    employee = db.query(models.Employee).filter(models.Employee.id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role == "manager":
        # Managers cannot delete owners or other managers
        if employee.role in ["owner", "manager"]:
            raise HTTPException(status_code=403, detail="Managers cannot delete owner or manager accounts")

        # Verify the target employee shares a branch with the manager
        manager_branch_ids = [
            m.room_id for m in current_user.room_memberships
            if m.room.type == models.RoomType.branch
        ]
        has_common_branch = db.query(models.RoomMember).filter(
            models.RoomMember.employee_id == employee.id,
            models.RoomMember.room_id.in_(manager_branch_ids)
        ).first() is not None

        if not has_common_branch:
            raise HTTPException(status_code=403, detail="Not authorized to delete staff outside your branch")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase_admin: Client = create_client(supabase_url, supabase_key)

    try:
        supabase_admin.auth.admin.delete_user(str(user_id))

        employee.is_active = False
        db.commit()

        # Trigger Google Sheet sync in background
        background_tasks.add_task(
            sync_user_to_google_sheet,
            action="delete",
            email=employee.email
        )

        return {"success": True}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
