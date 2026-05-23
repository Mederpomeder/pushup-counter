from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import UploadFile, File, Depends, HTTPException
from botocore.exceptions import BotoCoreError, ClientError
from app.storage import upload_profile_image

from app.database import engine, Base, get_db
from app import models, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Push-Up Social App Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app/main.py (Standard fallback)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_scheme = APIKeyHeader(name="Authorization", auto_error=False)


def get_current_user(authorization: Optional[str] = Depends(api_key_scheme), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing or invalid authentication token header. Format: 'Bearer <token>'"
        )
    token = authorization.split(" ")[1]
    user = db.query(models.User).filter(models.User.session_token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid token signature.")
    return user


def update_user_streak(user: models.User, db: Session):
    now = datetime.now(timezone.utc)
    today = now.date()
    
    if user.last_workout_date:
        last_date = user.last_workout_date.date()
        days_diff = (today - last_date).days
        
        if days_diff == 1:
            user.current_streak += 1
        elif days_diff == 0:
            pass
        else:
            user.current_streak = 1
    else:
        user.current_streak = 1
    
    user.last_workout_date = now
    db.commit()

@app.get("/")
def read_root():
    return {"status": "Online", "engine": "FastAPI Pushup App Engine core v1.0.0"}


@app.post("/auth/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already claimed.")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=pwd_context.hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/auth/login")
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password.")
    
    token = secrets.token_hex(32)
    user.session_token = token
    db.commit()
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "username": user.username}

@app.post("/auth/logout")
def logout(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.session_token = None
    db.commit()
    return {"message": "Logged out successfully."}


@app.get("/users/profile", response_model=schemas.UserProfileResponse)
def get_user_profile(username: Optional[str] = None, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    target_user = current_user
    if username:
        target_user = db.query(models.User).filter(models.User.username == username).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Requested user profile cannot be located.")

    total_pushups = db.query(func.sum(models.Workout.total_pushups)).filter(models.Workout.user_id == target_user.id).scalar() or 0
    best_single_workout = db.query(func.max(models.Workout.total_pushups)).filter(models.Workout.user_id == target_user.id).scalar() or 0
    total_likes_received = db.query(func.count(models.workout_likes.c.user_id)).join(models.Workout).filter(models.Workout.user_id == target_user.id).scalar() or 0

    return schemas.UserProfileResponse(
        username=target_user.username,
        profile_image_url=target_user.profile_image_url,
        current_streak=target_user.current_streak,
        total_pushups=total_pushups,
        best_single_workout=best_single_workout,
        total_likes_received=total_likes_received,
        followers_count=len(target_user.followers),
        following_count=len(target_user.following)
    )


@app.post("/social/follow/{target_id}")
def toggle_follow(target_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if target_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")
    target = db.query(models.User).filter(models.User.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target user not found.")
    
    if target in current_user.following:
        current_user.following.remove(target)
        db.commit()
        return {"status": "unfollowed", "following": False}
    
    current_user.following.append(target)
    db.commit()
    return {"status": "followed", "following": True}

@app.post("/workouts/{workout_id}/like")
def toggle_like_workout(workout_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    workout = db.query(models.Workout).filter(models.Workout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout history trace missing.")
    
    if current_user in workout.liked_by:
        workout.liked_by.remove(current_user)
        db.commit()
        return {"status": "unliked", "liked": False}
    
    workout.liked_by.append(current_user)
    db.commit()
    return {"status": "liked", "liked": True}



@app.post("/workouts/", response_model=schemas.WorkoutResponse)
def submit_workout(workout: schemas.WorkoutCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_workout = models.Workout(
        user_id=current_user.id,
        total_pushups=workout.total_pushups,
        duration_seconds=workout.duration_seconds
    )
    db.add(new_workout)
    update_user_streak(current_user, db)
    db.commit()
    db.refresh(new_workout)
    
    new_workout.likes_count = 0
    return new_workout

@app.get("/workouts/", response_model=List[schemas.WorkoutResponse])
def get_my_workouts(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    response_list = []
    for w in current_user.workouts:
        w.likes_count = len(w.liked_by)
        response_list.append(w)
    return response_list


@app.get("/feed/global")
def global_feed(db: Session = Depends(get_db)):
    workouts = db.query(models.Workout).order_by(models.Workout.created_at.desc()).limit(10).all()
    return [{
        "workout_id": w.id,
        "user_id": w.user_id,
        "username": w.owner.username,
        "user_profile_image": w.owner.profile_image_url,
        "total_pushups": w.total_pushups,
        "duration_seconds": w.duration_seconds,
        "likes_count": len(w.liked_by),
        "created_at": w.created_at
    } for w in workouts]

def build_leaderboard_data(user_ids: List[int], db: Session) -> List[schemas.LeaderboardEntry]:
    if not user_ids:
        return []
    results = db.query(
        models.User.id,
        models.User.username,
        func.sum(models.Workout.total_pushups).label("total"),
        func.max(models.Workout.total_pushups).label("best")
    ).join(models.Workout).group_by(models.User.id).filter(models.User.id.in_(user_ids)).order_by(func.sum(models.Workout.total_pushups).desc()).all()
    
    return [
        schemas.LeaderboardEntry(user_id=r[0], username=r[1], total_pushups=r[2], best_single_workout=r[3])
        for r in results
    ]

@app.get("/leaderboard/global", response_model=List[schemas.LeaderboardEntry])
def global_leaderboard(db: Session = Depends(get_db)):
    all_user_ids = [u.id for u in db.query(models.User.id).all()]
    return build_leaderboard_data(all_user_ids, db)

@app.get("/leaderboard/friends", response_model=List[schemas.LeaderboardEntry])
def friends_leaderboard(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed_ids = [u.id for u in current_user.following]
    allowed_ids.append(current_user.id)
    return build_leaderboard_data(allowed_ids, db)

MAX_FILE_SIZE = 2 * 1024 * 1024

@app.post("/users/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images are permitted.")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the maximum permitted limit of 2MB.")

    try:
        public_url = upload_profile_image(file)
        current_user.profile_image_url = public_url
        db.commit()
        db.refresh(current_user)
        
        return {
            "message": "Profile picture updated successfully.",
            "profile_image_url": public_url
        }
    except (BotoCoreError, ClientError) as storage_err:
        raise HTTPException(
            status_code=503, 
            detail="Cloud storage capacity limit reached or service is temporarily unavailable. Please try again later."
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to process image file. Ensure it is a valid image.")