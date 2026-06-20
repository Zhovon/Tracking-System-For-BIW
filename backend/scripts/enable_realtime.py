import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

# Add the parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

load_dotenv()

def enable_realtime():
    with engine.connect() as conn:
        try:
            # First, try to add tables to the existing supabase_realtime publication
            conn.execute(text("ALTER PUBLICATION supabase_realtime ADD TABLE tickets, messages, notifications;"))
            conn.commit()
            print("Successfully added tables to supabase_realtime publication.")
        except Exception as e:
            print(f"Warning: {e}")
            try:
                # If it fails, maybe the publication doesn't exist? (Unlikely on Supabase, but just in case)
                conn.execute(text("CREATE PUBLICATION supabase_realtime FOR TABLE tickets, messages, notifications;"))
                conn.commit()
                print("Created publication and added tables.")
            except Exception as e2:
                print(f"Failed to create publication: {e2}")

if __name__ == "__main__":
    enable_realtime()
