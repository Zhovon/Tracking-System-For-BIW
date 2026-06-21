import os
import sys

# Setup django/fastapi environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app.models import Ticket, Room, TicketRoom

db = SessionLocal()

tickets = db.query(Ticket).all()
print("Tickets:")
for t in tickets:
    print(f" - {t.title} (ID: {t.id})")
    for tr in t.room_links:
        print(f"   -> Room: {tr.room.name} (ID: {tr.room_id})")

rooms = db.query(Room).all()
print("\nRooms:")
for r in rooms:
    print(f" - {r.name} (ID: {r.id})")
    
db.close()
