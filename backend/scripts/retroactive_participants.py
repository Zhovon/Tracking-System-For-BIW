import os
import sys

# Add backend directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Ticket, TicketParticipant

def run():
    db = SessionLocal()
    try:
        print("Fetching all tickets...")
        tickets = db.query(Ticket).all()
        added_count = 0
        
        for ticket in tickets:
            # Check existing participants
            existing = {p.employee_id for p in ticket.participants}
            
            # Ensure creator is a participant
            if ticket.creator_id and ticket.creator_id not in existing:
                db.add(TicketParticipant(ticket_id=ticket.id, employee_id=ticket.creator_id))
                existing.add(ticket.creator_id)
                added_count += 1
                
            # Ensure current assignee is a participant
            if ticket.assigned_to_id and ticket.assigned_to_id not in existing:
                db.add(TicketParticipant(ticket_id=ticket.id, employee_id=ticket.assigned_to_id))
                existing.add(ticket.assigned_to_id)
                added_count += 1
                
        db.commit()
        print(f"Successfully retroactively added {added_count} participants to tickets.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run()
