import os
import sys
import uuid
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client


def setup_team():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        print("Error: Supabase admin keys not configured in env.")
        return

    supabase: Client = create_client(supabase_url, supabase_key)

    # 1. Fetch current users
    print("Fetching existing users in Supabase Auth...")
    res = supabase.auth.admin.list_users()
    users = res.users if hasattr(res, "users") else res
    
    # 2. Cleanup all users except razib@biw.salon
    target_email = "razib@biw.salon"
    razib_id = None
    
    for u in users:
        email = u.email
        uid = u.id
        if email == target_email:
            razib_id = uid
            print(f"Keeping Razib's account ({email}, ID: {uid})")
            continue
            
        print(f"Deleting user {email} (ID: {uid})...")
        try:
            # Delete memberships first to avoid FK constraints
            supabase.table("room_members").delete().eq("employee_id", uid).execute()
            # Delete employee DB record
            supabase.table("employees").delete().eq("id", uid).execute()
            # Delete from Supabase Auth
            supabase.auth.admin.delete_user(uid)
            print(f"Successfully deleted {email}")
        except Exception as e:
            print(f"Failed to fully delete {email}: {e}")

    # 3. Fetch rooms
    print("Fetching active rooms...")
    rooms_res = supabase.table("rooms").select("*").eq("is_active", True).execute()
    rooms = rooms_res.data
    
    branch_room_ids = [r["id"] for r in rooms if r["type"] == "branch"]
    it_room_id = next((r["id"] for r in rooms if "IT" in r["name"]), None)
    hr_room_id = next((r["id"] for r in rooms if "HR" in r["name"]), None)
    owners_room_id = next((r["id"] for r in rooms if "Owners" in r["name"] or "Management" in r["name"]), None)

    # 4. Determine starting staff ID
    print("Fetching highest staff ID...")
    try:
        staff_res = supabase.table("employees").select("staff_id").order("staff_id", desc=True).limit(1).execute()
        highest_staff_id = 0
        if staff_res.data and staff_res.data[0]["staff_id"]:
            highest_staff_id = int(staff_res.data[0]["staff_id"])
        print(f"Starting staff ID generation from: {str(highest_staff_id).zfill(4)}")
    except Exception as e:
        print(f"Error fetching staff ID: {e}")
        highest_staff_id = 100 # Safe fallback

    new_users = [
        {
            "email": "laboni@biw.salon",
            "name": "Laboni Owner",
            "role": "owner",
            "password": "BiwOwner2026!",
            "rooms": [owners_room_id] if owners_room_id else []
        },
        {
            "email": "usman@biw.salon",
            "name": "Usman Owner",
            "role": "owner",
            "password": "BiwOwner2026!",
            "rooms": [owners_room_id] if owners_room_id else []
        },
        {
            "email": "khalid@biw.salon",
            "name": "Khalid Brand Consultant",
            "role": "brand_consultant",
            "password": "BiwBrand2026!",
            "rooms": branch_room_ids + ([it_room_id] if it_room_id else []) + ([hr_room_id] if hr_room_id else [])
        }
    ]

    for user_info in new_users:
        email = user_info["email"]
        name = user_info["name"]
        role = user_info["role"]
        password = user_info["password"]
        target_rooms = [r for r in user_info["rooms"] if r is not None]

        print(f"\nProvisioning user {name} ({email})...")
        try:
            # Create in Supabase Auth
            auth_res = supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "name": name,
                    "role": role
                }
            })
            auth_id = auth_res.user.id
            
            # Generate staff ID
            highest_staff_id += 1
            staff_id_str = str(highest_staff_id).zfill(4)

            # Insert into database
            emp_data = {
                "id": auth_id,
                "staff_id": staff_id_str,
                "email": email,
                "name": name,
                "role": role,
                "is_active": True
            }
            supabase.table("employees").insert(emp_data).execute()

            # Assign to rooms
            memberships = [{"id": str(uuid.uuid4()), "employee_id": auth_id, "room_id": r_id} for r_id in target_rooms]
            if memberships:
                supabase.table("room_members").insert(memberships).execute()

            print(f"Successfully created {email} with staff ID {staff_id_str} and {len(memberships)} room assignments.")
        except Exception as e:
            print(f"Failed to create user {email}: {e}")

    print("\nSetup finished successfully!")


if __name__ == "__main__":
    setup_team()
