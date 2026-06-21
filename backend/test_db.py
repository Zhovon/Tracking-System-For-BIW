import os
import sys
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

print(f"Connecting to: {db_url}")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

session = SessionLocal()
try:
    from app.models import Employee
    users = session.query(Employee).all()
    print(f"Success! Found {len(users)} users.")
except Exception as e:
    print(f"Error querying users: {e}")
