from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_
import os
from dotenv import load_dotenv

from database import get_db, engine, Base
from auth import (
    authenticate_user, create_access_token, get_current_user, 
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
import schemas
import database as models
from anthropic import Anthropic

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal AI Assistant API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

@app.get("/")
def read_root():
    return {"message": "Personal AI Assistant API"}

# Authentication endpoints
@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | 
        (models.User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

# Habits endpoints
@app.get("/habits", response_model=List[schemas.Habit])
def get_habits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habits = db.query(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == 1
    ).all()
    
    # Add stats to each habit
    for habit in habits:
        # Check if completed today
        today_start = datetime.combine(date.today(), datetime.min.time())
        habit.completed_today = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id,
            models.HabitLog.completed_at >= today_start
        ).first() is not None
        
        # Get streak
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id
        ).order_by(models.HabitLog.completed_at.desc()).limit(30).all()
        
        current_streak = 0
        if logs:
            check_date = date.today()
            for log in logs:
                log_date = log.completed_at.date()
                if log_date == check_date or (current_streak == 0 and log_date == check_date - timedelta(days=1)):
                    current_streak += 1
                    check_date = log_date - timedelta(days=1)
                else:
                    break
        
        habit.current_streak = current_streak
    
    return habits

@app.post("/habits", response_model=schemas.Habit)
def create_habit(
    habit: schemas.HabitCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_habit = models.Habit(
        **habit.dict(),
        user_id=current_user.id
    )
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

# Add habit completion endpoint
@app.post("/habits/{habit_id}/complete")
def complete_habit(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify habit belongs to user
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Check if already completed today
    today_start = datetime.combine(date.today(), datetime.min.time())
    existing_log = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id,
        models.HabitLog.completed_at >= today_start
    ).first()
    
    if existing_log:
        raise HTTPException(status_code=400, detail="Habit already completed today")
    
    # Create completion log
    log = models.HabitLog(habit_id=habit_id)
    db.add(log)
    db.commit()
    
    return {"message": "Habit completed!", "completed_at": log.completed_at}

# Add habit stats endpoint
@app.get("/habits/{habit_id}/stats")
def get_habit_stats(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify habit belongs to user
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Calculate stats
    total_completions = db.query(func.count(models.HabitLog.id)).filter(
        models.HabitLog.habit_id == habit_id
    ).scalar()
    
    # Calculate current streak
    logs = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id
    ).order_by(models.HabitLog.completed_at.desc()).all()
    
    current_streak = 0
    if logs:
        check_date = date.today()
        for log in logs:
            log_date = log.completed_at.date()
            if log_date == check_date:
                current_streak += 1
                check_date -= timedelta(days=1)
            elif log_date == check_date - timedelta(days=1):
                current_streak += 1
                check_date = log_date - timedelta(days=1)
            else:
                break
    
    # Check if completed today
    today_start = datetime.combine(date.today(), datetime.min.time())
    completed_today = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id,
        models.HabitLog.completed_at >= today_start
    ).first() is not None
    
    return {
        "habit_id": habit_id,
        "total_completions": total_completions,
        "current_streak": current_streak,
        "completed_today": completed_today
    }

# Update habit endpoint
@app.put("/habits/{habit_id}", response_model=schemas.Habit)
def update_habit(
    habit_id: int,
    habit_update: schemas.HabitCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Update habit fields
    for field, value in habit_update.dict().items():
        setattr(habit, field, value)
    
    db.commit()
    db.refresh(habit)
    return habit

# Delete habit endpoint
@app.delete("/habits/{habit_id}")
def delete_habit(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Soft delete
    habit.is_active = 0
    db.commit()
    
    return {"message": "Habit deleted successfully"}

# Chat endpoint (placeholder for now)
@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # For hackathon, simple implementation
    try:
        # Get user context (habits, recent check-ins)
        habits = db.query(models.Habit).filter(
            models.Habit.user_id == current_user.id
        ).all()
        
        habit_context = "\n".join([f"- {h.name} ({h.frequency})" for h in habits])
        
        prompt = f"""You are a friendly personal AI assistant helping {current_user.username}.
        Their current habits are:
        {habit_context}
        
        User message: {message.message}
        
        Respond in a helpful, encouraging way."""
        
        # For demo, you can use a simple response or integrate with AI
        response_text = f"I understand you're asking about: {message.message}. Let me help you with that!"
        
        # Save conversation
        conversation = models.Conversation(
            user_id=current_user.id,
            message=message.message,
            response=response_text
        )
        db.add(conversation)
        db.commit()
        
        return schemas.ChatResponse(
            message=message.message,
            response=response_text,
            timestamp=conversation.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Daily check-in endpoint
@app.post("/checkin/daily", response_model=schemas.DailyCheckIn)
def create_daily_checkin(
    checkin: schemas.DailyCheckInCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_checkin = models.DailyCheckIn(
        **checkin.dict(),
        user_id=current_user.id
    )
    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)
    return db_checkin

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)