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
def get_users(db: Session = Depends(get_db)) -> Any:
    """
    Get all employees for assignment dropdowns.
    """
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
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can create new staff accounts")

    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Supabase admin keys not configured")

    supabase_admin: Client = create_client(supabase_url, supabase_key)

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
            uid=str(employee.id),
            phn_num=employee.phone if employee.phone else "",
            joining_date=employee.joining_date if employee.joining_date else ""
        )

        return employee

    except Exception as e:
        db.rollback()
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
            db.query(models.RoomMember).filter(
                models.RoomMember.employee_id == employee.id
            ).delete()
            for r_id in user_in.room_ids:
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
            uid=str(employee.id),
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
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete staff accounts")

    employee = db.query(models.Employee).filter(models.Employee.id == user_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="User not found")

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
