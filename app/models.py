from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,  Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


followers = Table(
    "followers",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("followed_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)


workout_likes = Table(
    "workout_likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("workout_id", Integer, ForeignKey("workouts.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False) 
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    profile_image_url = Column(String, nullable=True)
    current_streak = Column(Integer, default=0, nullable=False)
    last_workout_date = Column(DateTime(timezone = True), nullable=True)
    session_token = Column(String, nullable=True, unique=True) 

    workouts = relationship("Workout", back_populates="owner", cascade="all, delete-orphan")
    
    following = relationship(
        "User",
        secondary=followers,
        primaryjoin=(id == followers.c.follower_id),
        secondaryjoin=(id == followers.c.followed_id),
        backref="followers"
    )

class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_pushups = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone = True), default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="workouts")
    liked_by = relationship("User", secondary=workout_likes, backref="liked_workouts")