from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    profile_image_url: Optional[str] = None

    class Config:
        from_attributes = True

class WorkoutCreate(BaseModel):
    total_pushups: int
    duration_seconds: int

class WorkoutResponse(BaseModel):
    id: int
    user_id: int
    total_pushups: int
    duration_seconds: int
    likes_count: int  
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: int
    username: str
    profile_image_url: Optional[str] = None
    current_streak: int
    total_pushups: int
    best_single_workout: int
    total_likes_received: int
    followers_count: int
    following_count: int

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    user_id: int
    username: str
    total_pushups: int
    best_single_workout: int