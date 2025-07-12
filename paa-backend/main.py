from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, cast, Date
from collections import defaultdict
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

# Enhanced Chat endpoint with AI integration
@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get user context
        habits = db.query(models.Habit).filter(
            models.Habit.user_id == current_user.id,
            models.Habit.is_active == 1
        ).all()
        
        # Get recent check-ins
        recent_checkins = db.query(models.DailyCheckIn).filter(
            models.DailyCheckIn.user_id == current_user.id
        ).order_by(models.DailyCheckIn.timestamp.desc()).limit(5).all()
        
        # Get recent conversations for context
        recent_convos = db.query(models.Conversation).filter(
            models.Conversation.user_id == current_user.id
        ).order_by(models.Conversation.timestamp.desc()).limit(5).all()
        
        # Build context
        habit_context = []
        for habit in habits:
            # Check completion status
            today_start = datetime.combine(date.today(), datetime.min.time())
            completed_today = db.query(models.HabitLog).filter(
                models.HabitLog.habit_id == habit.id,
                models.HabitLog.completed_at >= today_start
            ).first() is not None
            
            habit_context.append({
                "name": habit.name,
                "frequency": habit.frequency,
                "completed_today": completed_today,
                "reminder_time": habit.reminder_time
            })
        
        mood_context = []
        for checkin in recent_checkins:
            mood_context.append({
                "date": checkin.timestamp.strftime("%Y-%m-%d"),
                "mood": checkin.mood,
                "notes": checkin.notes
            })
        
        conversation_history = []
        for convo in reversed(recent_convos):  # Oldest first
            conversation_history.append(f"User: {convo.message}")
            conversation_history.append(f"Assistant: {convo.response}")
        
        # Create system prompt
        import json
        system_prompt = f"""You are a friendly, supportive personal AI assistant helping {current_user.username} with their habits and personal development.

Current habits:
{json.dumps(habit_context, indent=2)}

Recent mood check-ins:
{json.dumps(mood_context, indent=2)}

Recent conversation history:
{chr(10).join(conversation_history[-10:])}

Guidelines:
1. Be encouraging and supportive
2. Reference their specific habits when relevant
3. Acknowledge their mood and progress
4. Provide actionable advice
5. Keep responses concise but warm
6. If they haven't completed habits today, gently encourage them
7. Celebrate their successes and streaks"""

        # Call AI API
        if anthropic_client and os.getenv("ANTHROPIC_API_KEY"):
            # Use Claude
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast model for chat
                max_tokens=500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message.message}
                ]
            )
            response_text = response.content[0].text
        else:
            # Fallback response for demo without API key
            response_text = generate_demo_response(message.message, habit_context, mood_context)
        
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
        print(f"Chat error: {str(e)}")
        # Fallback response
        response_text = "I'm here to help! Tell me about your day or ask me anything about your habits."
        
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

def generate_demo_response(message: str, habits: list, moods: list) -> str:
    """Generate a demo response when no AI API is available"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['habit', 'track', 'progress']):
        if habits:
            completed = sum(1 for h in habits if h['completed_today'])
            total = len(habits)
            return f"You're tracking {total} habits! You've completed {completed} out of {total} today. Keep up the great work! 🌟"
        else:
            return "I notice you haven't set up any habits yet. Would you like to start with something simple like daily meditation or drinking more water?"
    
    elif any(word in message_lower for word in ['feel', 'mood', 'today']):
        if moods and moods[0]['mood']:
            mood_score = moods[0]['mood']
            if mood_score >= 4:
                return "I'm glad you're feeling good! What's been going well for you today?"
            else:
                return "I hear you. Some days are tougher than others. What can I do to support you right now?"
        else:
            return "How are you feeling today? I'm here to listen and support you."
    
    elif any(word in message_lower for word in ['help', 'what can you']):
        return "I can help you track habits, check in on your mood, provide motivation, and offer advice on building better routines. What would you like to focus on?"
    
    else:
        return f"I understand you're asking about '{message}'. I'm here to support your personal growth journey. Feel free to ask me about your habits, mood, or anything else on your mind!"

# Get chat history endpoint
@app.get("/chat/history")
def get_chat_history(
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).order_by(models.Conversation.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": conv.id,
            "message": conv.message,
            "response": conv.response,
            "timestamp": conv.timestamp
        }
        for conv in reversed(conversations)  # Return in chronological order
    ]

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


# Analytics endpoints
@app.get("/analytics/habits")
def get_habits_analytics(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get habits with completion data
    habits = db.query(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == 1
    ).all()
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    analytics_data = []
    
    for habit in habits:
        # Get completion logs for this period
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id,
            cast(models.HabitLog.completed_at, Date) >= start_date,
            cast(models.HabitLog.completed_at, Date) <= end_date
        ).all()
        
        # Group by date
        completions_by_date = defaultdict(int)
        for log in logs:
            log_date = log.completed_at.date()
            completions_by_date[log_date] = 1
        
        # Create daily data
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            daily_data.append({
                "date": current_date.isoformat(),
                "completed": completions_by_date.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        # Calculate stats
        total_days = days
        completed_days = len([d for d in daily_data if d["completed"] > 0])
        completion_rate = (completed_days / total_days) * 100 if total_days > 0 else 0
        
        analytics_data.append({
            "habit_id": habit.id,
            "habit_name": habit.name,
            "completion_rate": round(completion_rate, 1),
            "total_completions": completed_days,
            "total_days": total_days,
            "daily_data": daily_data
        })
    
    return analytics_data

@app.get("/analytics/mood")
def get_mood_analytics(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get mood data for the period
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    checkins = db.query(models.DailyCheckIn).filter(
        models.DailyCheckIn.user_id == current_user.id,
        cast(models.DailyCheckIn.timestamp, Date) >= start_date,
        cast(models.DailyCheckIn.timestamp, Date) <= end_date
    ).order_by(models.DailyCheckIn.timestamp.asc()).all()
    
    # Group by date (latest checkin per day)
    mood_by_date = {}
    for checkin in checkins:
        checkin_date = checkin.timestamp.date()
        if checkin_date not in mood_by_date or checkin.timestamp > mood_by_date[checkin_date]['timestamp']:
            mood_by_date[checkin_date] = {
                'mood': checkin.mood,
                'notes': checkin.notes,
                'timestamp': checkin.timestamp
            }
    
    # Create daily data
    daily_moods = []
    current_date = start_date
    while current_date <= end_date:
        mood_data = mood_by_date.get(current_date)
        daily_moods.append({
            "date": current_date.isoformat(),
            "mood": mood_data['mood'] if mood_data else None,
            "notes": mood_data['notes'] if mood_data else None
        })
        current_date += timedelta(days=1)
    
    # Calculate average mood
    mood_values = [m['mood'] for m in daily_moods if m['mood'] is not None]
    average_mood = sum(mood_values) / len(mood_values) if mood_values else None
    
    return {
        "average_mood": round(average_mood, 1) if average_mood else None,
        "total_checkins": len(mood_values),
        "daily_moods": daily_moods
    }

@app.get("/analytics/overview")
def get_overview_analytics(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Habits overview
    total_habits = db.query(func.count(models.Habit.id)).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == 1
    ).scalar()
    
    # Completed today
    today_start = datetime.combine(date.today(), datetime.min.time())
    completed_today = db.query(
        func.count(func.distinct(models.HabitLog.habit_id))
    ).join(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.HabitLog.completed_at >= today_start
    ).scalar()
    
    # Current mood (today's latest checkin)
    today = date.today()
    # Use date() function instead of cast for SQLite compatibility
    today_checkin = db.query(models.DailyCheckIn).filter(
        models.DailyCheckIn.user_id == current_user.id,
        func.date(models.DailyCheckIn.timestamp) == today.isoformat()
    ).order_by(models.DailyCheckIn.timestamp.desc()).first()
    
    # Longest streak (for all habits combined)
    # This is simplified - could be enhanced
    all_logs = db.query(models.HabitLog).join(models.Habit).filter(
        models.Habit.user_id == current_user.id
    ).order_by(models.HabitLog.completed_at.desc()).limit(365).all()
    
    # Calculate longest streak of any activity
    streak_days = set()
    for log in all_logs:
        streak_days.add(log.completed_at.date())
    
    longest_streak = 0
    current_streak = 0
    check_date = date.today()
    
    for i in range(365):  # Check last year
        if check_date in streak_days:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
        check_date -= timedelta(days=1)
    
    return {
        "total_habits": total_habits,
        "completed_today": completed_today,
        "completion_rate": round((completed_today / total_habits) * 100, 1) if total_habits > 0 else 0,
        "current_mood": today_checkin.mood if today_checkin else None,
        "longest_streak": longest_streak,
        "total_conversations": db.query(func.count(models.Conversation.id)).filter(
            models.Conversation.user_id == current_user.id
        ).scalar()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)