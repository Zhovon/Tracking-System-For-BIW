import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")

def run():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # 1. Alter enum
    try:
        print("Adding 'universal' to roomtype enum...")
        cursor.execute("ALTER TYPE roomtype ADD VALUE IF NOT EXISTS 'universal';")
        print("Enum updated.")
    except Exception as e:
        print(f"Enum might already have 'universal' or error: {e}")
        
    # 2. Add Rooms
    try:
        # Check existing rooms
        cursor.execute("SELECT name FROM rooms;")
        existing_rooms = [r[0] for r in cursor.fetchall()]
        
        rooms_to_add = [
            ("Owners", "founder"),
            ("IT Team", "department"),
            ("Universal", "universal"),
        ]
        
        for name, rtype in rooms_to_add:
            if name not in existing_rooms:
                print(f"Adding room: {name}")
                cursor.execute("INSERT INTO rooms (name, type) VALUES (%s, %s);", (name, rtype))
            else:
                print(f"Room {name} already exists.")
                
    except Exception as e:
        print(f"Error adding rooms: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()
