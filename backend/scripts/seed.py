import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Room, Employee, RoomMember, RoomType
from supabase import create_client, Client

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)

    try:
        print("Seeding database...")

        # 1. Create Rooms (Branches & Departments)
        branches = ["Uttara Ladies", "Bashundhara Gents", "Bashundhara Ladies"]
        depts = ["HR", "IT Support", "Management"]
        rooms = {}

        for b in branches:
            r = Room(name=b, type=RoomType.branch)
            db.add(r)
            rooms[b] = r
        for d in depts:
            r = Room(name=d, type=RoomType.department)
            db.add(r)
            rooms[d] = r
            
        founder_room = Room(name="Owners", type=RoomType.founder)
        db.add(founder_room)
        rooms["Owners"] = founder_room
        db.commit()

        # 2. Create Owner Account in Supabase
        owner_email = "alice@example.com"
        owner_password = "password123"
        print(f"Creating Owner account in Supabase: {owner_email}")
        
        # Check if user exists (simple approach: just try to create, catch if exists)
        try:
            res = supabase.auth.admin.create_user({
                "email": owner_email,
                "password": owner_password,
                "email_confirm": True,
                "user_metadata": {"name": "Alice Owner", "role": "owner"}
            })
            owner_uuid = res.user.id
        except Exception as e:
            print(f"Creation failed, checking if user already exists... (Original error: {e})")
            # Fetch existing users
            users_res = supabase.auth.admin.list_users()
            existing_user = next((u for u in users_res if u.email == owner_email), None)
            if not existing_user:
                # In some python client versions list_users returns an object with a .users attribute
                if hasattr(users_res, 'users'):
                    existing_user = next((u for u in users_res.users if u.email == owner_email), None)
            
            if existing_user:
                owner_uuid = existing_user.id
                # Ensure the email is confirmed and password is correct just in case
                supabase.auth.admin.update_user_by_id(
                    owner_uuid,
                    {"password": owner_password, "email_confirm": True}
                )
            else:
                raise Exception(f"Failed to create user and user does not exist. Original error: {e}") from e

        # 3. Insert Owner into DB
        alice = Employee(
            id=uuid.UUID(owner_uuid),
            name="Alice Owner", 
            email=owner_email, 
            role="owner"
        )
        db.add(alice)
        db.commit()

        # 4. Assign Owner to Management Room
        db.add(RoomMember(employee_id=alice.id, room_id=rooms["Management"].id))
        db.commit()

        print("Database seeding completed successfully!")
        print(f"You can now log in at /login with:")
        print(f"Email: {owner_email}")
        print(f"Password: {owner_password}")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
