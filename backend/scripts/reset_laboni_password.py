import os
import sys
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import Client, create_client

def reset_laboni():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    email = "laboni@biw.salon"
    new_password = "laboni123"
    
    print(f"Fetching user record for {email}...")
    res = supabase.table("employees").select("id, name, role, phone, joining_date").eq("email", email).execute()
    if not res.data:
        print("Error: Laboni not found in employees table.")
        return
        
    uid = res.data[0]["id"]
    name = res.data[0]["name"]
    role = res.data[0]["role"]
    phone = res.data[0]["phone"] or "-"
    joining = res.data[0]["joining_date"] or "-"
    
    print(f"Updating password in Supabase Auth for UID {uid}...")
    try:
        supabase.auth.admin.update_user_by_id(uid, {"password": new_password})
        print("Supabase Auth password updated successfully.")
    except Exception as e:
        print(f"Error updating password in Auth: {e}")
        return
        
    # Also sync to Google Sheet
    webhook_url = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
    if webhook_url:
        print("Syncing updated password to Google Sheet...")
        try:
            payload = {
                "action": "update",
                "uid": "0003",
                "email": email,
                "name": name,
                "role": role,
                "password": new_password,
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
                print(f"Sheet Sync message: {res_body.get('message')}")
        except Exception as e:
            print(f"Error syncing to sheet: {e}")

if __name__ == "__main__":
    reset_laboni()
