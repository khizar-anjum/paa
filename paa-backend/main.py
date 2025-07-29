from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, cast, Date
from collections import defaultdict
import os
import logging
import time
from dotenv import load_dotenv

from database import get_db, engine, Base, SessionLocal
from auth import (
    authenticate_user, create_access_token, get_current_user, 
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
import schemas
import database as models
from anthropic import Anthropic
from scheduler import start_scheduler, stop_scheduler, initialize_default_prompts_for_user_sync
from services.commitment_parser import commitment_parser
from services.time_service import time_service
from services.intent_classifier import intent_classifier
from services.llm_processor import llm_processor
from services.rag_system import create_rag_system
from services.action_processor import create_action_processor
from services.vector_store import get_vector_store
from debug_logger import debug_logger
import atexit

load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal AI Assistant API")

# Debug middleware for HTTP request/response logging
@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    if debug_logger.debug_mode and os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true":
        start_time = time.time()
        
        # Log request
        body = await request.body()
        debug_logger.log_http_request(
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            body=body.decode() if body else None
        )
        
        # Process request (need to recreate request with body for downstream)
        from fastapi import Request as FastAPIRequest
        async def receive():
            return {"type": "http.request", "body": body}
        
        request = FastAPIRequest(request.scope, receive)
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        debug_logger.log_http_response(
            status_code=response.status_code,
            process_time=process_time,
            headers=dict(response.headers)
        )
    else:
        response = await call_next(request)
    
    return response

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

# Initialize hybrid pipeline services
rag_system = create_rag_system(lambda: SessionLocal())
action_processor = create_action_processor(lambda: SessionLocal())
vector_store = get_vector_store()
llm_processor.anthropic_client = anthropic_client

# We'll initialize the scheduler on FastAPI startup instead of at import time
# Register cleanup function for graceful shutdown
async def cleanup_schedulers():
    """Cleanup function for graceful shutdown"""
    await stop_scheduler()

# Note: atexit doesn't work well with async functions, so we'll rely on FastAPI shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup schedulers when FastAPI shuts down"""
    await cleanup_schedulers()

@app.on_event("startup")
async def startup_event():
    """Initialize background scheduler when FastAPI starts"""
    await start_scheduler()

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
    
    # Initialize default scheduled prompts for new user
    try:
        initialize_default_prompts_for_user_sync(db_user.id)
    except Exception as e:
        print(f"Note: Default prompts initialization skipped: {e}")
    
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
        today_start = datetime.combine(time_service.now().date(), datetime.min.time())
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
            check_date = time_service.now().date()
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
    
    # Embed the new habit for semantic search
    try:
        vector_store.embed_habit(db_habit, db)
    except Exception as e:
        debug_logger.warning(f"Failed to embed habit {db_habit.id}: {e}")
    
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
    today_start = datetime.combine(time_service.now().date(), datetime.min.time())
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
    today_start = datetime.combine(time_service.now().date(), datetime.min.time())
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
            today_start = datetime.combine(time_service.now().date(), datetime.min.time())
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
        
        # Check if this is a response to a commitment reminder
        # Get recent proactive messages and active commitments
        recent_proactive = db.query(models.ProactiveMessage).filter(
            models.ProactiveMessage.user_id == current_user.id,
            models.ProactiveMessage.user_responded == False,
            models.ProactiveMessage.message_type == 'commitment_reminder'
        ).order_by(models.ProactiveMessage.sent_at.desc()).limit(5).all()
        
        active_commitments = db.query(models.Commitment).filter(
            models.Commitment.user_id == current_user.id,
            models.Commitment.status == 'pending'
        ).all()
        
        # Check if user's message indicates completion, dismissal, or postponement
        commitment_action_taken = False
        message_lower = message.message.lower()
        
        # Keywords for different actions
        completion_keywords = ['done', 'completed', 'finished', 'did it', 'just did', 'already did', 'yes', 'yep', 'yeah']
        dismissal_keywords = ['cancel', 'dismiss', 'forget it', 'nevermind', 'no longer', 'not doing', 'skip']
        postpone_keywords = ['tomorrow', 'later', 'postpone', 'delay', 'not today', 'maybe tomorrow']
        
        # If there are recent proactive messages about commitments
        if recent_proactive and active_commitments:
            # Find which commitment the user might be responding to
            for proactive_msg in recent_proactive:
                if proactive_msg.related_commitment_id:
                    commitment = next((c for c in active_commitments if c.id == proactive_msg.related_commitment_id), None)
                    if commitment:
                        # Check if user's response relates to this commitment
                        if any(keyword in message_lower for keyword in completion_keywords):
                            # Mark commitment as completed
                            commitment.status = 'completed'
                            proactive_msg.user_responded = True
                            proactive_msg.response_content = message.message
                            commitment_action_taken = True
                            db.commit()
                            break
                        elif any(keyword in message_lower for keyword in dismissal_keywords):
                            # Dismiss commitment
                            commitment.status = 'dismissed'
                            proactive_msg.user_responded = True
                            proactive_msg.response_content = message.message
                            commitment_action_taken = True
                            db.commit()
                            break
                        elif any(keyword in message_lower for keyword in postpone_keywords):
                            # Postpone commitment to tomorrow
                            tomorrow = time_service.now().date() + timedelta(days=1)
                            commitment.deadline = tomorrow
                            commitment.reminder_count = 0  # Reset reminder count
                            proactive_msg.user_responded = True
                            proactive_msg.response_content = message.message
                            commitment_action_taken = True
                            db.commit()
                            break
        
        # Detect new commitments in the user's message
        detected_commitments = commitment_parser.extract_commitments(message.message)
        commitment_acknowledgments = []
        
        # Create commitment records for detected commitments
        for commitment_data in detected_commitments:
            try:
                # Create commitment in database
                db_commitment = models.Commitment(
                    user_id=current_user.id,
                    task_description=commitment_data['task_description'],
                    original_message=commitment_data['original_message'],
                    deadline=commitment_data['deadline'],
                    status='pending',
                    reminder_count=0
                )
                db.add(db_commitment)
                db.commit()
                db.refresh(db_commitment)
                
                # Add acknowledgment for AI response
                deadline_str = commitment_data['deadline'].strftime("%A, %B %d")
                if commitment_data['time_phrase'].lower() == 'today':
                    deadline_str = "today"
                elif commitment_data['time_phrase'].lower() == 'tomorrow':
                    deadline_str = "tomorrow"
                
                commitment_acknowledgments.append(
                    f"I'll remind you about '{commitment_data['task_description']}' if needed. You mentioned you want to do it {deadline_str}."
                )
                
            except Exception as e:
                print(f"Error creating commitment: {e}")
                # Continue processing even if one commitment fails
                continue
        
        # Create system prompt
        import json
        commitment_context = ""
        commitment_action_context = ""
        
        if commitment_action_taken and 'commitment' in locals():
            # Add context about the commitment action taken
            if commitment.status == 'completed':
                commitment_action_context = f"\n\nThe user just completed their commitment: '{commitment.task_description}'. Acknowledge this accomplishment warmly!"
            elif commitment.status == 'dismissed':
                commitment_action_context = f"\n\nThe user decided to cancel their commitment: '{commitment.task_description}'. Be understanding and supportive."
            elif commitment.deadline:
                commitment_action_context = f"\n\nThe user postponed their commitment '{commitment.task_description}' to tomorrow. Be supportive and remind them you'll check in tomorrow."
        
        if commitment_acknowledgments:
            commitment_context = f"""

Detected commitments from this message that you should acknowledge:
{chr(10).join(commitment_acknowledgments)}

Important: Include these commitment acknowledgments naturally in your response to show you're tracking their commitments."""

        system_prompt = f"""You are a friendly, supportive personal AI assistant helping {current_user.username} with their habits and personal development.

Current habits:
{json.dumps(habit_context, indent=2)}

Recent mood check-ins:
{json.dumps(mood_context, indent=2)}

Recent conversation history:
{chr(10).join(conversation_history[-10:])}
{commitment_context}
{commitment_action_context}

Guidelines:
1. Be encouraging and supportive
2. Reference their specific habits when relevant
3. Acknowledge their mood and progress
4. Provide actionable advice
5. Keep responses concise but warm
6. If they haven't completed habits today, gently encourage them
7. Celebrate their successes and streaks
8. If commitments were detected, acknowledge them naturally in your response"""

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
            response_text = generate_demo_response(message.message, habit_context, mood_context, commitment_acknowledgments)
        
        # Save conversation
        conversation = models.Conversation(
            user_id=current_user.id,
            message=message.message,
            response=response_text
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Update commitments with conversation reference
        if detected_commitments:
            for commitment_data in detected_commitments:
                try:
                    # Find the commitment we just created and update with conversation ID
                    db_commitment = db.query(models.Commitment).filter(
                        models.Commitment.user_id == current_user.id,
                        models.Commitment.task_description == commitment_data['task_description'],
                        models.Commitment.original_message == commitment_data['original_message'],
                        models.Commitment.created_from_conversation_id.is_(None)
                    ).first()
                    
                    if db_commitment:
                        db_commitment.created_from_conversation_id = conversation.id
                        db.commit()
                except Exception as e:
                    print(f"Error updating commitment with conversation ID: {e}")
                    continue
        
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

# Enhanced Chat endpoint with Hybrid Pipeline Architecture
@app.post("/chat/enhanced", response_model=schemas.ChatResponse)
async def enhanced_chat(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enhanced chat endpoint using the Hybrid Pipeline Architecture:
    1. Intent Classification
    2. RAG Context Retrieval  
    3. LLM Processing with Structured Output
    4. Action Processing
    """
    # Start pipeline execution tracking
    execution_id = debug_logger.start_pipeline_execution(current_user.id, message.message)
    
    try:
        # 1. Intent Classification
        intent = intent_classifier.classify(message.message)
        
        # 2. RAG Context Retrieval
        context = rag_system.retrieve_context(message.message, intent, current_user.id)
        
        # Get user profile if available
        user_data = {}
        user_profile = db.query(models.UserProfile).filter(
            models.UserProfile.user_id == current_user.id
        ).first()
        if user_profile:
            user_data['profile'] = {
                'name': user_profile.name,
                'pronouns': user_profile.pronouns,
                'description': user_profile.description
            }
        
        # 3. LLM Processing with Structured Output
        ai_response = llm_processor.process_message(
            message.message,
            intent,
            context,
            user_data
        )
        
        # 4. Action Processing
        processing_result = await action_processor.process_response(
            ai_response,
            current_user.id
        )
        
        # 5. Store conversation with metadata
        conversation = models.Conversation(
            user_id=current_user.id,
            message=message.message,
            response=ai_response.message,
            timestamp=time_service.now()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # 6. Embed the conversation for future semantic search
        try:
            vector_store.embed_conversation(conversation)
        except Exception as e:
            debug_logger.warning(f"Failed to embed conversation {conversation.id}: {e}")
        
        # 7. Return enhanced response
        debug_logger.end_pipeline_execution(success=True)
        
        return schemas.ChatResponse(
            message=message.message,
            response=ai_response.message,
            timestamp=conversation.timestamp
        )
        
    except Exception as e:
        debug_logger.error(f"Enhanced chat error: {str(e)}")
        # Fallback to basic response
        fallback_response = "I'm here to help! Tell me about your day or ask me anything about your habits."
        
        conversation = models.Conversation(
            user_id=current_user.id,
            message=message.message,
            response=fallback_response,
            timestamp=time_service.now()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Embed the fallback conversation too
        try:
            vector_store.embed_conversation(conversation)
        except Exception as e:
            debug_logger.warning(f"Failed to embed fallback conversation {conversation.id}: {e}")
        
        debug_logger.end_pipeline_execution(success=False, error=str(e))
        
        return schemas.ChatResponse(
            message=message.message,
            response=fallback_response,
            timestamp=conversation.timestamp
        )

def generate_demo_response(message: str, habits: list, moods: list, commitment_acknowledgments: list = None) -> str:
    """Generate a demo response when no AI API is available"""
    message_lower = message.lower()
    
    # Build base response
    base_response = ""
    
    if any(word in message_lower for word in ['habit', 'track', 'progress']):
        if habits:
            completed = sum(1 for h in habits if h['completed_today'])
            total = len(habits)
            base_response = f"You're tracking {total} habits! You've completed {completed} out of {total} today. Keep up the great work! 🌟"
        else:
            base_response = "I notice you haven't set up any habits yet. Would you like to start with something simple like daily meditation or drinking more water?"
    
    elif any(word in message_lower for word in ['feel', 'mood', 'today']):
        if moods and moods[0]['mood']:
            mood_score = moods[0]['mood']
            if mood_score >= 4:
                base_response = "I'm glad you're feeling good! What's been going well for you today?"
            else:
                base_response = "I hear you. Some days are tougher than others. What can I do to support you right now?"
        else:
            base_response = "How are you feeling today? I'm here to listen and support you."
    
    elif any(word in message_lower for word in ['help', 'what can you']):
        base_response = "I can help you track habits, check in on your mood, provide motivation, and offer advice on building better routines. What would you like to focus on?"
    
    else:
        base_response = f"I understand you're asking about '{message}'. I'm here to support your personal growth journey. Feel free to ask me about your habits, mood, or anything else on your mind!"
    
    # Add commitment acknowledgments if any were detected
    if commitment_acknowledgments:
        commitment_text = " " + " ".join(commitment_acknowledgments)
        base_response += commitment_text
    
    return base_response

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


# People endpoints
@app.get("/people", response_model=List[schemas.Person])
def get_people(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    people = db.query(models.Person).filter(
        models.Person.user_id == current_user.id
    ).order_by(models.Person.name).all()
    return people

@app.post("/people", response_model=schemas.Person)
def create_person(
    person: schemas.PersonCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_person = models.Person(
        **person.dict(),
        user_id=current_user.id
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    
    # Embed the new person for semantic search
    try:
        vector_store.embed_person(db_person)
    except Exception as e:
        debug_logger.warning(f"Failed to embed person {db_person.id}: {e}")
    
    return db_person

@app.get("/people/{person_id}", response_model=schemas.Person)
def get_person(
    person_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person = db.query(models.Person).filter(
        models.Person.id == person_id,
        models.Person.user_id == current_user.id
    ).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

@app.put("/people/{person_id}", response_model=schemas.Person)
def update_person(
    person_id: int,
    person_update: schemas.PersonUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person = db.query(models.Person).filter(
        models.Person.id == person_id,
        models.Person.user_id == current_user.id
    ).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    for field, value in person_update.dict(exclude_unset=True).items():
        setattr(person, field, value)
    
    person.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(person)
    return person

@app.delete("/people/{person_id}")
def delete_person(
    person_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    person = db.query(models.Person).filter(
        models.Person.id == person_id,
        models.Person.user_id == current_user.id
    ).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    db.delete(person)
    db.commit()
    return {"message": "Person deleted successfully"}


# User Profile endpoints
@app.get("/profile", response_model=schemas.UserProfile)
def get_user_profile(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/profile", response_model=schemas.UserProfile)
def create_user_profile(
    profile: schemas.UserProfileCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if profile already exists
    existing_profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    db_profile = models.UserProfile(
        **profile.dict(),
        user_id=current_user.id
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@app.put("/profile", response_model=schemas.UserProfile)
def update_user_profile(
    profile_update: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


# Proactive AI endpoints

# Commitment management endpoints
@app.get("/commitments", response_model=List[schemas.Commitment])
def get_commitments(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    commitments = db.query(models.Commitment).filter(
        models.Commitment.user_id == current_user.id
    ).order_by(models.Commitment.created_at.desc()).all()
    return commitments

@app.post("/commitments/{commitment_id}/complete")
def complete_commitment(
    commitment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    commitment.status = "completed"
    db.commit()
    return {"message": "Commitment marked as completed"}

@app.post("/commitments/{commitment_id}/dismiss")
def dismiss_commitment(
    commitment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    commitment.status = "dismissed"
    db.commit()
    return {"message": "Commitment dismissed"}

@app.post("/commitments/{commitment_id}/postpone")
def postpone_commitment(
    commitment_id: int,
    commitment_update: schemas.CommitmentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    if commitment_update.deadline:
        commitment.deadline = commitment_update.deadline
    commitment.status = "pending"
    commitment.reminder_count = 0  # Reset reminder count
    db.commit()
    return {"message": "Commitment postponed"}

# Proactive message endpoints
@app.get("/proactive-messages", response_model=List[schemas.ProactiveMessage])
def get_proactive_messages(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(models.ProactiveMessage).filter(
        models.ProactiveMessage.user_id == current_user.id,
        models.ProactiveMessage.sent_at.isnot(None)
    ).order_by(models.ProactiveMessage.sent_at.desc()).limit(50).all()
    return messages

@app.post("/proactive-messages/{message_id}/acknowledge")
def acknowledge_proactive_message(
    message_id: int,
    response: schemas.ProactiveMessageResponse,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    message = db.query(models.ProactiveMessage).filter(
        models.ProactiveMessage.id == message_id,
        models.ProactiveMessage.user_id == current_user.id
    ).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    message.user_responded = True
    message.response_content = response.response_content
    db.commit()
    return {"message": "Message acknowledged"}

# Scheduled prompt endpoints
@app.get("/scheduled-prompts", response_model=List[schemas.ScheduledPrompt])
def get_scheduled_prompts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompts = db.query(models.ScheduledPrompt).filter(
        models.ScheduledPrompt.user_id == current_user.id
    ).all()
    return prompts

@app.put("/scheduled-prompts/{prompt_id}", response_model=schemas.ScheduledPrompt)
def update_scheduled_prompt(
    prompt_id: int,
    prompt_update: schemas.ScheduledPromptUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompt = db.query(models.ScheduledPrompt).filter(
        models.ScheduledPrompt.id == prompt_id,
        models.ScheduledPrompt.user_id == current_user.id
    ).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Scheduled prompt not found")
    
    for field, value in prompt_update.dict(exclude_unset=True).items():
        setattr(prompt, field, value)
    
    db.commit()
    db.refresh(prompt)
    return prompt


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
    end_date = time_service.now().date()
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
    end_date = time_service.now().date()
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
    today_start = datetime.combine(time_service.now().date(), datetime.min.time())
    completed_today = db.query(
        func.count(func.distinct(models.HabitLog.habit_id))
    ).join(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.HabitLog.completed_at >= today_start
    ).scalar()
    
    # Current mood (today's latest checkin)
    today = time_service.now().date()
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

# Debug API endpoints for time acceleration testing
@app.post("/debug/time/start")
def start_fake_time(
    fake_start_time: str = None,  # ISO format datetime string
    time_multiplier: int = 600,
    current_user: models.User = Depends(get_current_user)
):
    """Start fake time acceleration for testing proactive AI features"""
    try:
        start_datetime = None
        if fake_start_time:
            start_datetime = datetime.fromisoformat(fake_start_time.replace('Z', '+00:00'))
        
        result = time_service.start_fake_time(start_datetime, time_multiplier)
        return {
            "success": True,
            "message": f"Fake time started with {time_multiplier}x acceleration",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error starting fake time: {str(e)}")

@app.post("/debug/time/stop")
def stop_fake_time(current_user: models.User = Depends(get_current_user)):
    """Stop fake time and return to real time"""
    try:
        result = time_service.stop_fake_time()
        return {
            "success": True,
            "message": "Fake time stopped, returned to real time",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error stopping fake time: {str(e)}")

@app.post("/debug/time/set-multiplier")
def set_time_multiplier(
    request: schemas.TimeMultiplierRequest,
    current_user: models.User = Depends(get_current_user)
):
    """Change the time acceleration multiplier while fake time is running"""
    try:
        result = time_service.set_multiplier(request.multiplier)
        
        # Check if the time service returned an error
        if result.get("status") == "error":
            return {
                "success": False,
                "message": result.get("message", "Unknown error")
            }
        
        return {
            "success": True,
            "message": f"Time multiplier set to {request.multiplier}x",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error setting multiplier: {str(e)}")

@app.post("/debug/time/jump")
def jump_to_time(
    target_time: str,  # ISO format datetime string
    current_user: models.User = Depends(get_current_user)
):
    """Jump fake time to a specific datetime"""
    try:
        target_datetime = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
        result = time_service.jump_to_time(target_datetime)
        return {
            "success": True,
            "message": f"Jumped to fake time: {target_time}",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error jumping to time: {str(e)}")

@app.get("/debug/time/status")
def get_time_status(current_user: models.User = Depends(get_current_user)):
    """Get current time service status"""
    try:
        from services.fake_time_scheduler import fake_time_scheduler
        
        time_status = time_service.get_status()
        scheduler_status = fake_time_scheduler.get_status()
        
        return {
            "success": True,
            "time_service": time_status,
            "fake_scheduler": scheduler_status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting time status: {str(e)}")

# Additional Debug Endpoints
@app.get("/debug/status")
def get_debug_status(current_user: models.User = Depends(get_current_user)):
    """Get current debug configuration status"""
    return debug_logger.get_debug_status()

@app.get("/debug/pipeline/recent-executions")
def get_recent_pipeline_executions(current_user: models.User = Depends(get_current_user)):
    """Get recent pipeline execution details"""
    return {
        "success": True,
        "recent_executions": debug_logger.get_recent_executions()
    }

@app.get("/debug/vector-store/stats")
def get_vector_store_stats(current_user: models.User = Depends(get_current_user)):
    """Get vector store collection statistics"""
    try:
        # Get collection counts
        stats = {
            "collections": {
                "conversations": 0,
                "habits": 0,
                "people": 0,
                "commitments": 0
            },
            "status": "healthy"
        }
        
        try:
            # Get collection counts from ChromaDB
            conv_count = vector_store.conversations_collection.count()
            habits_count = vector_store.habits_collection.count()
            people_count = vector_store.people_collection.count()
            commitments_count = vector_store.commitments_collection.count()
            
            stats["collections"] = {
                "conversations": conv_count,
                "habits": habits_count,
                "people": people_count,
                "commitments": commitments_count
            }
            stats["total_documents"] = conv_count + habits_count + people_count + commitments_count
            
        except Exception as e:
            stats["status"] = "error"
            stats["error"] = str(e)
        
        return {
            "success": True,
            "vector_store_stats": stats
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/debug/pipeline/last-execution")
def get_last_pipeline_execution(current_user: models.User = Depends(get_current_user)):
    """Get detailed info about the last pipeline execution"""
    try:
        recent_executions = debug_logger.get_recent_executions()
        if not recent_executions:
            return {
                "success": True,
                "last_execution": None,
                "message": "No recent pipeline executions found"
            }
        
        return {
            "success": True,
            "last_execution": recent_executions[0]  # Most recent execution
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/debug/clear-logs")
def clear_debug_logs(current_user: models.User = Depends(get_current_user)):
    """Clear recent pipeline execution logs"""
    try:
        # Clear recent executions
        debug_logger.recent_executions = []
        
        return {
            "success": True,
            "message": "Debug logs cleared successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)