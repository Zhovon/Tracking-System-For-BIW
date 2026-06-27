import os
import sys
import urllib.request
import json
from dotenv import load_dotenv

# Load env variables and append path
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client

ROSTER = [
    {"name": "Tamanna", "email": "ayshatamanna96@gmail.com", "phone": "01971319176", "role": "manager", "joining": "20 August 2024", "password": "BiwStaff2000!", "nid": "2864914250"},
    {"name": "Akhi Khan", "email": "akhi45651@gmail.com", "phone": "01758679900", "role": "manager", "joining": "28 February 2023", "password": "BiwStaff1998!", "nid": "8731478593"},
    {"name": "Nova", "email": "farihanova03@gmail.com", "phone": "01908027282", "role": "manager", "joining": "7 February 2026", "password": "BiwStaff2000!", "nid": "2861264139"},
    {"name": "Sharmin Akter", "email": "sharmin07717@gmail.com", "phone": "01883376681", "role": "therapist", "joining": "15 June 2026", "password": "BiwStaff2002!", "nid": "6460821488"},
    {"name": "Shahanaj", "email": "doashaharaz93@gmail.com", "phone": "01781874346", "role": "therapist", "joining": "19 April 2026", "password": "BiwStaff2001!", "nid": "2868916566"},
    {"name": "Moitree", "email": "mmoitree605@gmail.com", "phone": "01581488173", "role": "therapist", "joining": "11 January 2023", "password": "BiwStaff2002!", "nid": ""},
    {"name": "Rabina", "email": "rabinahaque29@gmail.com", "phone": "01600580204", "role": "therapist", "joining": "11 January 2023", "password": "BiwStaff2002!", "nid": "2002611317616944"},
    {"name": "Anjuman", "email": "anjumanaktar540@gmail.com", "phone": "01320368639", "role": "therapist", "joining": "1 November 2024", "password": "BiwStaff2001!", "nid": "1513946708"},
    {"name": "Rima", "email": "darothitripura@gmail.com", "phone": "01318383279", "role": "therapist", "joining": "1 June 2023", "password": "BiwStaff1995!", "nid": "8706329425"},
    {"name": "Ajmeri", "email": "angelazmir5060@gmail.com", "phone": "01736715396", "role": "therapist", "joining": "1 November 2025", "password": "BiwStaff2000!", "nid": "4212976981"},
    {"name": "Helena", "email": "nitikattripura@gmail.com", "phone": "01840626458", "role": "therapist", "joining": "1 June 2023", "password": "BiwStaff1997!", "nid": "19970319152001750"},
    {"name": "Ishikha", "email": "khumbatripura@gmail.com", "phone": "01627753206", "role": "therapist", "joining": "6 March 2024", "password": "BiwStaff2001!", "nid": "6918896124"},
    {"name": "Runa", "email": "sangmarahul604@gmail.com", "phone": "01580738658", "role": "therapist", "joining": "6 March 2024", "password": "BiwStaff1995!", "nid": "19956111631000037"},
    {"name": "Dichi", "email": "dichimree99@gmail.com", "phone": "01722745259", "role": "therapist", "joining": "1 December 2024", "password": "BiwStaff1995!", "nid": "6137021071"},
    {"name": "Sobita", "email": "sobitripura98@gmail.com", "phone": "01841152879", "role": "therapist", "joining": "13 October 2025", "password": "BiwStaff1998!", "nid": "4667659868"},
    {"name": "Kajoli", "email": "kajolysangma@gmail.com", "phone": "01903411357", "role": "therapist", "joining": "16 October 2025", "password": "BiwStaff1999!", "nid": "2856306309"},
    {"name": "Baby", "email": "babysangma650@gmail.com", "phone": "01942904689", "role": "therapist", "joining": "10 June 2025", "password": "BiwStaff2003!", "nid": "3773685395"},
    {"name": "Eti", "email": "dofoety@gmail.com", "phone": "01406948581", "role": "therapist", "joining": "17 June 2025", "password": "BiwStaff1997!", "nid": "2851950366"},
    {"name": "Sonia", "email": "sonia@biw.com", "phone": "01302540310", "role": "therapist", "joining": "4 February 2026", "password": "BiwStaff1995!", "nid": "19966111610115828"},
    {"name": "Rani", "email": "santitripura687@gmail.com", "phone": "01572707764", "role": "therapist", "joining": "7 November 2024", "password": "BiwStaff2004!", "nid": "7368863580"},
    {"name": "Mili", "email": "milimrong357@gmail.com", "phone": "01774709094", "role": "therapist", "joining": "1 December 2024", "password": "BiwStaff1998!", "nid": ""},
    {"name": "Borsha", "email": "borsharunam80@gmail.com", "phone": "01740642824", "role": "therapist", "joining": "11 December 2024", "password": "BiwStaff2005!", "nid": "1974921619"},
    {"name": "Lipi", "email": "anikhawee556@gmail.com", "phone": "01610598572", "role": "therapist", "joining": "11 December 2024", "password": "BiwStaff1997!", "nid": "601425436"},
    {"name": "Munni", "email": "titanongrin@gmail.com", "phone": "01992515770", "role": "therapist", "joining": "4 June 2026", "password": "BiwStaff2008!", "nid": "20098917075112187"},
    {"name": "Konika", "email": "khankonika692@gmail.com", "phone": "01340145602", "role": "cleaner", "joining": "6 October 2025", "password": "BiwStaff2007!", "nid": "20070695126000051"},
    {"name": "Popy", "email": "pppju0243@gmail.com", "phone": "01301116582", "role": "cleaner", "joining": "6 October 2025", "password": "BiwStaff2011!", "nid": ""},
    {"name": "Samia", "email": "samiaakterbd2011@gmail.com", "phone": "01839297670", "role": "cleaner", "joining": "25 April 2026", "password": "BiwStaff2005!", "nid": ""},
    {"name": "Takmina", "email": "dhdhdhdjddhh658@gmail.com", "phone": "01863180726", "role": "cleaner", "joining": "25 April 2026", "password": "BiwStaff2007!", "nid": ""}
]

# Parsed chronological mapping
from datetime import datetime
import re

months = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
}

def get_sort_key(item):
    date_str = item["joining"].lower().strip()
    match = re.search(r'(\d+)\s*([a-z]+)\s*(\d{4})', date_str)
    if not match:
        return datetime(2050, 1, 1)
    day, month_name, year = match.groups()
    return datetime(int(year), months.get(month_name, 1), int(day))

# Sort the roster chronologically
ROSTER.sort(key=get_sort_key)


def reset_and_sync():
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    if not webhook_url:
        print("Error: GOOGLE_SHEET_WEBHOOK_URL not set in env.")
        return

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)

    # Razib Ahamed UID
    razib_uid = None
    try:
        res = supabase.table("employees").select("id").eq("email", "razib@biw.salon").execute()
        if res.data:
            razib_uid = res.data[0]["id"]
    except Exception as e:
        print(f"Error fetching Razib UID: {e}")
        return

    if not razib_uid:
        print("Error: Could not find Razib Ahamed in employees table.")
        return

    # 1. Delete test accounts (john and Ratul) from Supabase and Local database
    test_emails = ["cena@gmail.com", "zaidulislamratul025@gmail.com"]
    for email in test_emails:
        print(f"Reassigning tickets and deleting test account: {email}")
        try:
            # Delete from sheet
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps({"action": "delete", "email": email}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                urllib.request.urlopen(req)
            except Exception as se:
                print(f"  Warning: failed to delete from sheet: {se}")

            # Fetch user ID from local DB
            res = supabase.table("employees").select("id").eq("email", email).execute()
            if res.data:
                user_id = res.data[0]["id"]
                
                # Reassign tickets where they are creator to Razib
                supabase.table("tickets").update({"creator_id": razib_uid}).eq("creator_id", user_id).execute()
                # Reassign tickets where they are assigned_to to NULL
                supabase.table("tickets").update({"assigned_to_id": None}).eq("assigned_to_id", user_id).execute()
                # Reassign messages where they are author
                supabase.table("messages").update({"author_id": razib_uid}).eq("author_id", user_id).execute()
                # Reassign audit logs where they are user_id
                try:
                    supabase.table("audit_logs").update({"user_id": razib_uid}).eq("user_id", user_id).execute()
                except Exception:
                    pass

                # Delete notifications
                try:
                    supabase.table("notifications").delete().eq("user_id", user_id).execute()
                except Exception as ne:
                    print(f"    Warning: failed to delete notifications: {ne}")

                # Delete room memberships
                supabase.table("room_members").delete().eq("employee_id", user_id).execute()
                # Delete employee
                supabase.table("employees").delete().eq("id", user_id).execute()
                # Delete from Supabase Auth
                supabase.auth.admin.delete_user(user_id)
                print(f"  Successfully deleted {email} from DB and Auth.")
        except Exception as e:
            print(f"  Error deleting {email}: {e}")

    # 2. To avoid unique key conflicts during re-ordering, clear the staff_id column for all users to NULL first
    print("Clearing staff_ids temporarily to avoid unique constraints...")
    try:
        all_emp_res = supabase.table("employees").select("id").execute()
        for emp_row in all_emp_res.data:
            supabase.table("employees").update({"staff_id": None}).eq("id", emp_row["id"]).execute()
        print("  All staff_ids temporarily cleared.")
    except Exception as e:
        print(f"Error clearing staff IDs: {e}")
        return

    # 3. Update core user details
    # 1: Razib Ahamed (email razib@biw.salon)
    try:
        supabase.table("employees").update({"name": "Razib Ahamed", "staff_id": "0001"}).eq("id", razib_uid).execute()
        supabase.auth.admin.update_user_by_id(razib_uid, {"user_metadata": {"name": "Razib Ahamed"}})
        print("Updated Razib Ahamed profile.")
    except Exception as e:
        print(f"Error updating Razib: {e}")

    # 2: Usman Hossain (email usman@biw.salon)
    try:
        res = supabase.table("employees").select("id").eq("email", "usman@biw.salon").execute()
        if res.data:
            uid = res.data[0]["id"]
            supabase.table("employees").update({"name": "Usman Hossain", "staff_id": "0002"}).eq("id", uid).execute()
            supabase.auth.admin.update_user_by_id(uid, {"user_metadata": {"name": "Usman Hossain"}})
            print("Updated Usman Hossain profile.")
    except Exception as e:
        print(f"Error updating Usman: {e}")

    # 3: Laboni Akter (email laboni@biw.salon)
    try:
        res = supabase.table("employees").select("id").eq("email", "laboni@biw.salon").execute()
        if res.data:
            uid = res.data[0]["id"]
            supabase.table("employees").update({"name": "Laboni Akter", "staff_id": "0003"}).eq("id", uid).execute()
            supabase.auth.admin.update_user_by_id(uid, {"user_metadata": {"name": "Laboni Akter"}})
            print("Updated Laboni Akter profile.")
    except Exception as e:
        print(f"Error updating Laboni: {e}")

    # 4: Khalid Brand Consultant (email khalid@biw.salon)
    try:
        res = supabase.table("employees").select("id").eq("email", "khalid@biw.salon").execute()
        if res.data:
            uid = res.data[0]["id"]
            supabase.table("employees").update({"staff_id": "0004"}).eq("id", uid).execute()
            print("Updated Khalid staff_id to 0004.")
    except Exception as e:
        print(f"Error updating Khalid: {e}")

    # 4. Process the chronologically sorted employees from staff_id 0005 to 0032
    current_id = 5
    for emp in ROSTER:
        email = emp["email"]
        name = emp["name"]
        role = emp["role"]
        phone = emp["phone"]
        joining = emp["joining"]
        password = emp["password"]
        
        staff_id_str = str(current_id).zfill(4)

        try:
            res = supabase.table("employees").select("id").eq("email", email).execute()
            if res.data:
                uid = res.data[0]["id"]
                # Update staff_id, phone, nid, joining_date in local DB
                supabase.table("employees").update({
                    "staff_id": staff_id_str,
                    "phone": phone,
                    "nid": emp.get("nid", ""),
                    "joining_date": joining
                }).eq("id", uid).execute()
                print(f"Assigned staff_id {staff_id_str} and fields to {name} ({email})")
                
                # Push to sheet
                payload = {
                    "action": "create",
                    "uid": staff_id_str,
                    "email": email,
                    "name": name,
                    "role": role,
                    "password": password,
                    "phn_num": phone,
                    "joining_date": joining
                }
                
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    print(f"  Sheet Sync for {name}: {res_body.get('message')}")
                    
                current_id += 1
        except Exception as e:
            print(f"Error processing {name}: {e}")

    # 5. Push core users to sheet too
    core_users = [
        {"email": "razib@biw.salon", "uid": "0001", "name": "Razib Ahamed", "role": "owner", "password": "Existing Account", "phone": "-", "joining": "-"},
        {"email": "usman@biw.salon", "uid": "0002", "name": "Usman Hossain", "role": "owner", "password": "BiwOwner2026!", "phone": "-", "joining": "-"},
        {"email": "laboni@biw.salon", "uid": "0003", "name": "Laboni Akter", "role": "owner", "password": "laboni123", "phone": "-", "joining": "-"},
        {"email": "khalid@biw.salon", "uid": "0004", "name": "Khalid Brand Consultant", "role": "brand_consultant", "password": "BiwBrand2026!", "phone": "-", "joining": "-"}
    ]
    for core in core_users:
        print(f"Syncing core user {core['name']} to sheet...")
        try:
            payload = {
                "action": "create",
                "uid": core["uid"],
                "email": core["email"],
                "name": core["name"],
                "role": core["role"],
                "password": core["password"],
                "phn_num": core["phone"],
                "joining_date": core["joining"]
            }
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                print(f"  Sheet Sync for {core['name']}: {res_body.get('message')}")
        except Exception as e:
            print(f"Error syncing core: {e}")

    print("Reset and ordered sync completed!")


if __name__ == "__main__":
    reset_and_sync()
