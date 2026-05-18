from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import List

from app.database import engine, Base, get_db
from app import models, schemas

# Initialize database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Push-Ups Counter Backend")

# Setup password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- HELPER SECURITY FUNCTIONS ---
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ==========================================
# 1. USER ENDPOINTS & OPERATIONS (SIGN UP)
# ==========================================
@app.post("/users/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Securely hash the password using bcrypt
    hashed_password = get_password_hash(user.password)
    
    # Create database record
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ==========================================
# 2. THE 5 WORKOUT CRUD ENDPOINTS
# ==========================================

# CRUD 1: CREATE a new workout session record
@app.post("/users/{user_id}/workouts/", response_model=schemas.WorkoutResponse)
def create_workout(user_id: int, workout: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    # Ensure the user exists first
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    new_workout = models.Workout(
        user_id=user_id,
        total_pushups=workout.total_pushups,
        duration_seconds=workout.duration_seconds
    )
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    return new_workout


# CRUD 2: READ (List) all workouts belonging to a specific user
@app.get("/users/{user_id}/workouts/", response_model=List[schemas.WorkoutResponse])
def read_user_workouts(user_id: int, db: Session = Depends(get_db)):
    workouts = db.query(models.Workout).filter(models.Workout.user_id == user_id).all()
    return workouts


# CRUD 3: READ (Single) specific workout details
@app.get("/workouts/{workout_id}", response_model=schemas.WorkoutResponse)
def read_single_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout record not found")
    return workout


# CRUD 4: UPDATE an existing workout record description/stats
@app.put("/workouts/{workout_id}", response_model=schemas.WorkoutResponse)
def update_workout(workout_id: int, updated_data: schemas.WorkoutCreate, db: Session = Depends(get_db)):
    db_workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout record not found")
    
    # Modify data fields safely
    db_workout.total_pushups = updated_data.total_pushups
    db_workout.duration_seconds = updated_data.duration_seconds
    
    db.commit()
    db.refresh(db_workout)
    return db_workout


# CRUD 5: DELETE a specific workout record from history
@app.delete("/workouts/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    db_workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not db_workout:
        raise HTTPException(status_code=404, detail="Workout record not found")
        
    db.delete(db_workout)
    db.commit()
    return {"message": "Workout successfully deleted"}