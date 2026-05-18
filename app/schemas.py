from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

# --- USER SCHEMAS ---
class UserCreate(BaseModel):
    username: str
    email: str  # You can use EmailStr if you run 'pip install pydantic[email]'
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


# --- WORKOUT SCHEMAS ---
class WorkoutCreate(BaseModel):
    total_pushups: int
    duration_seconds: int

class WorkoutResponse(BaseModel):
    id: int
    user_id: int
    total_pushups: int
    duration_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True