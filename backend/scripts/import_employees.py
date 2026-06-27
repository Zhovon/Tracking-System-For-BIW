import os
import sys
import uuid
import re
from html.parser import HTMLParser
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client
from app.database import SessionLocal, engine
from app.models import Employee, Room, RoomMember, RoomType
from sqlalchemy import text


class RosterHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.in_td = False
        self.in_tr = False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.in_tr = True
            self.current_row = []
        elif tag == "td":
            self.in_td = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "tr":
            self.in_tr = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag == "td":
            self.in_td = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_td:
            self.current_cell += data


def parse_roster(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    parser = RosterHTMLParser()
    parser.feed(html_content)

    employees = []
    # Skip the header row
    for row in parser.rows:
        if not row or len(row) < 5:
            continue
        name = row[0]
        phone = row[1]
        email = row[2]
        pin = row[3]
        role_raw = row[4].strip().lower()

        # Skip headers or empty rows
        if name.lower() == "name" or not name:
            continue

        # Normalise email
        email_clean = email
        if not email or "@" not in email or email.lower() == "name":
            # Generate a default safe email
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
            email_clean = f"{safe_name}@biw.com"

        # Map role
        role = "therapist"
        if "manager" in role_raw:
            role = "manager"
        elif "cleaner" in role_raw:
            role = "cleaner"
        elif "nurse" in role_raw:
            role = "therapist"
        elif "therapist" in role_raw:
            role = "therapist"

        employees.append({
            "name": name,
            "phone": phone,
            "email": email_clean,
            "pin": pin,
            "role": role,
            "role_raw": row[4]
        })

    return employees


def bulk_import():
    sheet_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Sheet1.html")
    if not os.path.exists(sheet_path):
        print(f"Error: Sheet1.html not found at {sheet_path}")
        return

    print("Parsing Sheet1.html...")
    employees_to_import = parse_roster(sheet_path)
    print(f"Found {len(employees_to_import)} employees in roster.")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: Supabase admin keys not configured in env.")
        return

    supabase: Client = create_client(supabase_url, supabase_key)
    db = SessionLocal()

    # Get branch rooms to auto-assign
    branch_rooms = db.query(Room).filter(Room.type == RoomType.branch).all()
    branch_room_ids = [r.id for r in branch_rooms]

    imported_count = 0
    skipped_count = 0

    try:
        for emp in employees_to_import:
            email = emp["email"]
            name = emp["name"]
            role = emp["role"]

            # Check if user already exists locally
            existing = db.query(Employee).filter(Employee.email == email).first()
            if existing:
                print(f"Skipping {name} ({email}) - already exists in database.")
                skipped_count += 1
                continue

            # Create in Supabase Auth
            temp_password = f"BiwStaff{emp['pin']}!" if emp['pin'].isdigit() else "BiwStaff2026!"
            print(f"Creating account for {name} ({email}) with temp password: {temp_password}")

            try:
                # Bypass email confirmation
                res = supabase.auth.admin.create_user({
                    "email": email,
                    "password": temp_password,
                    "email_confirm": True,
                    "user_metadata": {
                        "name": name,
                        "role": role
                    }
                })
                auth_id = res.user.id
            except Exception as e:
                # If user already exists in Supabase Auth but not in our DB
                print(f"Auth creation failed or user already exists in auth: {e}")
                # Try to list users to find matching email
                users_res = supabase.auth.admin.list_users()
                user_obj = next((u for u in users_res if u.email == email), None)
                if not user_obj and hasattr(users_res, "users"):
                    user_obj = next((u for u in users_res.users if u.email == email), None)

                if user_obj:
                    auth_id = user_obj.id
                else:
                    print(f"Failed to create or find user: {name} ({email})")
                    skipped_count += 1
                    continue

            # Generate staff ID
            seq_val = db.execute(text("SELECT nextval('staff_id_seq')")).scalar()
            staff_id_str = str(seq_val).zfill(4)

            # Insert into database
            new_emp = Employee(
                id=uuid.UUID(auth_id),
                staff_id=staff_id_str,
                email=email,
                name=name,
                role=role
            )
            db.add(new_emp)
            db.flush()

            # Assign to branch rooms
            for room_id in branch_room_ids:
                membership = RoomMember(employee_id=new_emp.id, room_id=room_id)
                db.add(membership)

            db.commit()
            print(f"Successfully imported {name} as staff ID {staff_id_str} assigned to branch rooms.")
            imported_count += 1

        print("\n--- Import Summary ---")
        print(f"Successfully imported: {imported_count}")
        print(f"Skipped (already exists): {skipped_count}")

    except Exception as e:
        print(f"Fatal error during bulk import: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    bulk_import()
