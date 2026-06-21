import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

# Mock the Employee and UserOut behavior
class UserOut(BaseModel):
    id: UUID
    name: str
    room_ids: List[UUID] = []
    
    class Config:
        from_attributes = True

class Employee:
    def __init__(self, id, name):
        self.id = id
        self.name = name

import uuid
emp = Employee(id=uuid.uuid4(), name="Test")

try:
    user = UserOut.model_validate(emp)
    print("Success:", user)
except Exception as e:
    print("Error:", e)
