import re
import os

ROUTER_PATH = "backend/app/domains/tickets/router.py"
with open(ROUTER_PATH, "r") as f:
    content = f.read()

# 1. Add BackgroundTasks and dispatch_notification import
if "from fastapi import BackgroundTasks" not in content:
    content = content.replace("from fastapi import APIRouter", "from fastapi import APIRouter, BackgroundTasks")

if "from app.domains.notifications.push import send_web_push" not in content:
    content = content.replace("from app.database import get_db", "from app.database import get_db, SessionLocal\nfrom app.domains.notifications.push import send_web_push")

# 2. Add dispatch_notification helper function
helper_code = """
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
    else:
        _send()
"""
if "def dispatch_notification(" not in content:
    content = content.replace("router = APIRouter()", "router = APIRouter()\n" + helper_code)

# 3. Add background_tasks to function signatures
funcs = [
    r"(def create_ticket\([^)]*?)(, *\n *current_user: models\.Employee = Depends\(get_current_user\),*\n*\) -> Any:)",
    r"(def create_message\([^)]*?)(, *\n *current_user: models\.Employee = Depends\(get_current_user\),*\n*\) -> Any:)",
    r"(def assign_ticket\([^)]*?)(, *\n *current_user: models\.Employee = Depends\(get_current_user\),*\n*\) -> Any:)",
    r"(def update_ticket_status\([^)]*?)(, *\n *current_user: models\.Employee = Depends\(get_current_user\),*\n*\) -> Any:)"
]
for p in funcs:
    content = re.sub(p, r"\1, background_tasks: BackgroundTasks\2", content)

# 4. Replace db.add(models.Notification(...)) with dispatch_notification
# e.g.:
# db.add(models.Notification(
#     user_id=owner.id,
#     ticket_id=ticket.id,
#     message=msg
# ))
content = re.sub(
    r"db\.add\(models\.Notification\(\s*user_id=(.*?),\s*ticket_id=(.*?),\s*message=(.*?)\s*\)\)",
    r"dispatch_notification(db, background_tasks, \1, \2, \3)",
    content
)

# And the one where it creates notification first:
# notification = models.Notification(
#     user_id=target_user_id,
#     ticket_id=ticket.id,
#     message=f"New comment on ticket: {ticket.title}"
# )
# db.add(notification)
content = re.sub(
    r"notification = models\.Notification\(\s*user_id=(.*?),\s*ticket_id=(.*?),\s*message=(.*?)\s*\)\s*db\.add\(notification\)",
    r"dispatch_notification(db, background_tasks, \1, \2, \3)",
    content
)

with open(ROUTER_PATH, "w") as f:
    f.write(content)
print("Done")
