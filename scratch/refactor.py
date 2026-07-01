import re
import os

ROUTER_PATH = "backend/app/domains/tickets/router.py"
with open(ROUTER_PATH, "r") as f:
    content = f.read()

# 1. Imports
if "BackgroundTasks" not in content:
    content = content.replace("from fastapi import APIRouter, Depends", "from fastapi import APIRouter, BackgroundTasks, Depends")
if "send_web_push" not in content:
    content = content.replace("from app.api.deps import get_current_user, get_db", "from app.api.deps import get_current_user, get_db\nfrom app.database import SessionLocal\nfrom app.domains.notifications.push import send_web_push")

# 2. Add Helper Function
helper = """
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

"""
if "def dispatch_notification" not in content:
    content = content.replace("router = APIRouter()\n", "router = APIRouter()\n\n" + helper)

# 3. Fix signatures
# We will just find 'current_user: models.Employee = Depends(get_current_user),' 
# inside the specific functions and append 'background_tasks: BackgroundTasks = None,'
targets = ["def create_ticket", "async def post_message", "def assign_ticket", "def update_ticket"]
for tgt in targets:
    # Find the function def start
    idx = content.find(tgt)
    if idx == -1:
        print(f"NOT FOUND: {tgt}")
        continue
    # Find the end of the signature ')'
    end_idx = content.find(") -> Any:", idx)
    if end_idx == -1:
        end_idx = content.find("):", idx)
        
    sig = content[idx:end_idx]
    if "background_tasks: BackgroundTasks" not in sig:
        # replace the last parameter with background tasks added
        new_sig = sig + ",\n    background_tasks: BackgroundTasks"
        content = content[:idx] + new_sig + content[end_idx:]

# 4. Replace Notifications
content = re.sub(
    r"db\.add\(models\.Notification\(\s*user_id=(.*?),\s*ticket_id=(.*?),\s*message=(.*?)\s*\)\)",
    r"dispatch_notification(db, background_tasks, \1, \2, \3)",
    content,
    flags=re.DOTALL
)

content = re.sub(
    r"notification = models\.Notification\(\s*user_id=(.*?),\s*ticket_id=(.*?),\s*message=(.*?)\s*\)\s*db\.add\(notification\)",
    r"dispatch_notification(db, background_tasks, \1, \2, \3)",
    content,
    flags=re.DOTALL
)

with open(ROUTER_PATH, "w") as f:
    f.write(content)
print("Done")
