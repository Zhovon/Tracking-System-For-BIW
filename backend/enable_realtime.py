from sqlalchemy import text

from app.database import SessionLocal


def enable_realtime():
    db = SessionLocal()
    try:
        print("Enabling realtime for tables...")
        # Supabase uses a publication named 'supabase_realtime'
        # We need to add our tables to it
        tables = ['tickets', 'messages', 'notifications']

        for table in tables:
            try:
                db.execute(text(f"ALTER PUBLICATION supabase_realtime ADD TABLE {table};"))
                print(f"Added {table} to supabase_realtime publication")
            except Exception as e:
                if 'already added' in str(e).lower() or 'already a member' in str(e).lower():
                    print(f"Table {table} is already in the publication")
                elif 'does not exist' in str(e).lower():
                    # If publication doesn't exist (e.g. not on supabase), create it
                    print("Publication might not exist. Attempting to create it...")
                    db.execute(text("CREATE PUBLICATION supabase_realtime FOR ALL TABLES;"))
                    print("Created supabase_realtime publication")
                    break
                else:
                    print(f"Warning for {table}: {e}")

        db.commit()
        print("Done!")
    finally:
        db.close()

if __name__ == "__main__":
    enable_realtime()
