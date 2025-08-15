from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, cast, Date
from collections import defaultdict
import os
import logging
import time
import uuid
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
from services.nlp_intent_classifier import nlp_intent_classifier
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

# CORS configuration - Allow all origins for development
# In production, you should restrict this to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
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

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and scripts"""
    return {"status": "healthy", "service": "PAA Backend", "timestamp": datetime.utcnow()}

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

# Habits endpoints - REMOVED in unified system migration
# All habit functionality moved to unified commitments system



# Enhanced Chat endpoint with AI integration
@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get user context - using unified commitments system
        recurring_commitments = db.query(models.Commitment).filter(
            models.Commitment.user_id == current_user.id,
            models.Commitment.recurrence_pattern != "none",
            models.Commitment.status == "active"
        ).all()
        
        # Get recent check-ins
        recent_checkins = db.query(models.DailyCheckIn).filter(
            models.DailyCheckIn.user_id == current_user.id
        ).order_by(models.DailyCheckIn.timestamp.desc()).limit(5).all()
        
        # Get recent conversations for context
        recent_convos = db.query(models.Conversation).filter(
            models.Conversation.user_id == current_user.id
        ).order_by(models.Conversation.timestamp.desc()).limit(5).all()
        
        # Build context - recurring commitments (formerly habits)
        habit_context = []
        today = date.today()
        for commitment in recurring_commitments:
            # Check completion status for today
            completed_today = db.query(models.CommitmentCompletion).filter(
                models.CommitmentCompletion.commitment_id == commitment.id,
                models.CommitmentCompletion.completion_date == today
            ).first() is not None
            
            habit_context.append({
                "name": commitment.task_description,
                "frequency": commitment.recurrence_pattern,
                "completed_today": completed_today,
                "reminder_time": commitment.due_time.strftime("%H:%M") if commitment.due_time else None
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
    message: schemas.ChatMessageEnhanced,
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
        # Get session information
        chat_session = db.query(models.ChatSession).filter(
            models.ChatSession.id == message.session_id,
            models.ChatSession.user_id == current_user.id
        ).first()
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
        # 1. Intent Classification
        intent = nlp_intent_classifier.classify(message.message)
        
        # 2. RAG Context Retrieval (session-aware)
        context = rag_system.retrieve_context(message.message, intent, current_user.id, session_id=message.session_id)
        
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
        
        # Debug: Log the structured response
        debug_logger.info(f"📊 Structured AI Response: message='{ai_response.message[:100]}...', commitments={len(ai_response.commitments)}, habits={len(ai_response.habit_actions)}")
        
        # 4. Action Processing
        processing_result = await action_processor.process_response(
            ai_response,
            current_user.id
        )
        
        # 5. Store conversation with metadata
        conversation = models.Conversation(
            user_id=current_user.id,
            session_id=message.session_id,
            session_name=chat_session.name,
            message=message.message,
            response=ai_response.message,
            timestamp=time_service.now()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Update session's last_message_at
        chat_session.last_message_at = time_service.now()
        db.commit()
        
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
            session_id=message.session_id,
            session_name=chat_session.name if 'chat_session' in locals() else "General",
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
@app.get("/chat/history/{session_id}")
def get_chat_history(
    session_id: str,
    limit: int = 50,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session belongs to user
    chat_session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.session_id == session_id
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
    status: Optional[str] = None,
    overdue: Optional[bool] = None,
    sort_by: Optional[str] = "created_at",
    order: Optional[str] = "desc",
    type: Optional[str] = None,  # all, one-time, recurring
    recurrence: Optional[str] = None,  # none, daily, weekly, monthly
    due: Optional[str] = None,  # today, this-week, overdue, upcoming
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get commitments with comprehensive filtering for unified system
    Supports both one-time and recurring commitments (formerly habits)
    """
    query = db.query(models.Commitment).filter(
        models.Commitment.user_id == current_user.id
    )
    
    # Filter by status
    if status:
        query = query.filter(models.Commitment.status == status)
    
    # Filter by type (unified system)
    if type == "one-time":
        query = query.filter(models.Commitment.recurrence_pattern == "none")
    elif type == "recurring":
        query = query.filter(models.Commitment.recurrence_pattern != "none")
    
    # Filter by specific recurrence pattern
    if recurrence:
        query = query.filter(models.Commitment.recurrence_pattern == recurrence)
    
    # Filter by due date
    today = date.today()
    if due == "today":
        # One-time due today OR recurring that should be done today
        query = query.filter(
            or_(
                and_(
                    models.Commitment.recurrence_pattern == "none",
                    models.Commitment.deadline == today
                ),
                and_(
                    models.Commitment.recurrence_pattern != "none",
                    models.Commitment.status == "active"
                )
            )
        )
    elif due == "this-week":
        week_end = today + timedelta(days=7)
        query = query.filter(
            or_(
                and_(
                    models.Commitment.recurrence_pattern == "none",
                    models.Commitment.deadline.between(today, week_end)
                ),
                and_(
                    models.Commitment.recurrence_pattern != "none",
                    models.Commitment.status == "active"
                )
            )
        )
    elif due == "overdue":
        query = query.filter(
            models.Commitment.recurrence_pattern == "none",
            models.Commitment.deadline < today,
            models.Commitment.status == "pending"
        )
    elif due == "upcoming":
        query = query.filter(
            models.Commitment.recurrence_pattern == "none",
            models.Commitment.deadline > today,
            models.Commitment.status == "pending"
        )
    
    # Legacy overdue filter (for backward compatibility)
    if overdue is not None:
        if overdue:
            query = query.filter(
                models.Commitment.deadline < today,
                models.Commitment.status == "pending"
            )
        else:
            query = query.filter(
                models.Commitment.deadline >= today
            )
    
    # Sorting
    if sort_by == "deadline":
        if order == "asc":
            query = query.order_by(models.Commitment.deadline.asc())
        else:
            query = query.order_by(models.Commitment.deadline.desc())
    elif sort_by == "created_at":
        if order == "asc":
            query = query.order_by(models.Commitment.created_at.asc())
        else:
            query = query.order_by(models.Commitment.created_at.desc())
    elif sort_by == "completion_count":
        if order == "asc":
            query = query.order_by(models.Commitment.completion_count.asc())
        else:
            query = query.order_by(models.Commitment.completion_count.desc())
    
    commitments = query.all()
    
    # Add computed fields
    for commitment in commitments:
        commitment.is_recurring = commitment.recurrence_pattern != "none"
        
        # Check if completed today (for recurring commitments)
        if commitment.is_recurring:
            completion = db.query(models.CommitmentCompletion).filter(
                models.CommitmentCompletion.commitment_id == commitment.id,
                models.CommitmentCompletion.completion_date == today
            ).first()
            commitment.completed_today = completion is not None
        else:
            commitment.completed_today = False
    
    return commitments

@app.post("/commitments/{commitment_id}/complete")
def complete_commitment(
    commitment_id: int,
    completion_data: schemas.CommitmentCompletionCreate = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a commitment as completed (unified system)
    For one-time commitments: marks as completed
    For recurring commitments: logs completion for today
    """
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    if commitment.recurrence_pattern == "none":
        # One-time commitment - mark as completed
        commitment.status = "completed"
        db.commit()
        return {"message": "Commitment marked as completed"}
    else:
        # Recurring commitment - log completion for today
        today = completion_data.completion_date if completion_data and completion_data.completion_date else date.today()
        
        # Check if already completed for this date
        existing = db.query(models.CommitmentCompletion).filter(
            models.CommitmentCompletion.commitment_id == commitment_id,
            models.CommitmentCompletion.completion_date == today
        ).first()
        
        if existing:
            return {"message": f"Commitment already completed for {today}"}
        
        # Create completion record
        completion = models.CommitmentCompletion(
            commitment_id=commitment_id,
            user_id=current_user.id,
            completion_date=today,
            notes=completion_data.notes if completion_data else None,
            skipped=False
        )
        db.add(completion)
        
        # Update commitment stats
        commitment.completion_count += 1
        commitment.last_completed_at = datetime.utcnow()
        
        db.commit()
        return {"message": f"Recurring commitment completed for {today}"}
    
    db.commit()
    return {"message": "Commitment completed"}

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

@app.put("/commitments/{commitment_id}", response_model=schemas.Commitment)
def update_commitment(
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
    
    # Update fields if provided
    if commitment_update.status:
        commitment.status = commitment_update.status
    if commitment_update.deadline:
        commitment.deadline = commitment_update.deadline
    
    db.commit()
    db.refresh(commitment)
    return commitment

@app.delete("/commitments/{commitment_id}")
def delete_commitment(
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
    
    db.delete(commitment)
    db.commit()
    return {"message": "Commitment deleted"}

# New unified system endpoints
@app.post("/commitments/{commitment_id}/skip")
def skip_commitment(
    commitment_id: int,
    skip_data: dict = {},
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Skip a recurring commitment for today"""
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    if commitment.recurrence_pattern == "none":
        raise HTTPException(status_code=400, detail="Cannot skip one-time commitment")
    
    today = date.today()
    
    # Check if already completed or skipped for this date
    existing = db.query(models.CommitmentCompletion).filter(
        models.CommitmentCompletion.commitment_id == commitment_id,
        models.CommitmentCompletion.completion_date == today
    ).first()
    
    if existing:
        if existing.skipped:
            return {"message": f"Commitment already skipped for {today}"}
        else:
            return {"message": f"Commitment already completed for {today}"}
    
    # Create skip record
    skip_record = models.CommitmentCompletion(
        commitment_id=commitment_id,
        user_id=current_user.id,
        completion_date=today,
        notes=skip_data.get("reason", "Skipped"),
        skipped=True
    )
    db.add(skip_record)
    db.commit()
    
    return {"message": f"Commitment skipped for {today}"}

@app.get("/commitments/{commitment_id}/completions", response_model=List[schemas.CommitmentCompletion])
def get_commitment_completions(
    commitment_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get completion history for a commitment"""
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    query = db.query(models.CommitmentCompletion).filter(
        models.CommitmentCompletion.commitment_id == commitment_id
    )
    
    if start_date:
        query = query.filter(models.CommitmentCompletion.completion_date >= start_date)
    if end_date:
        query = query.filter(models.CommitmentCompletion.completion_date <= end_date)
    
    return query.order_by(models.CommitmentCompletion.completion_date.desc()).all()

@app.post("/commitments", response_model=schemas.Commitment)
def create_commitment(
    commitment: schemas.CommitmentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new commitment (one-time or recurring)"""
    db_commitment = models.Commitment(
        user_id=current_user.id,
        task_description=commitment.task_description,
        original_message=commitment.original_message,
        deadline=commitment.deadline,
        recurrence_pattern=commitment.recurrence_pattern,
        recurrence_interval=commitment.recurrence_interval,
        recurrence_days=commitment.recurrence_days,
        recurrence_end_date=commitment.recurrence_end_date,
        due_time=commitment.due_time,
        reminder_settings=commitment.reminder_settings,
        status="active" if commitment.recurrence_pattern != "none" else "pending",
        completion_count=0,
        created_from_conversation_id=commitment.created_from_conversation_id
    )
    
    db.add(db_commitment)
    db.commit()
    db.refresh(db_commitment)
    
    # Add computed fields
    db_commitment.is_recurring = db_commitment.recurrence_pattern != "none"
    db_commitment.completed_today = False
    
    return db_commitment

@app.get("/commitments/{commitment_id}/reminders", response_model=List[schemas.ProactiveMessage])
def get_commitment_reminders(
    commitment_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # First verify the commitment belongs to the user
    commitment = db.query(models.Commitment).filter(
        models.Commitment.id == commitment_id,
        models.Commitment.user_id == current_user.id
    ).first()
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    # Get all proactive messages related to this commitment
    reminders = db.query(models.ProactiveMessage).filter(
        models.ProactiveMessage.related_commitment_id == commitment_id,
        models.ProactiveMessage.user_id == current_user.id
    ).order_by(models.ProactiveMessage.sent_at.desc()).all()
    
    return reminders

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


# Session Management endpoints
@app.post("/sessions", response_model=schemas.SessionResponse)
async def create_session(
    session_data: schemas.SessionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    # Create session
    chat_session = models.ChatSession(
        id=session_id,
        user_id=current_user.id,
        name=session_data.name,
        created_at=time_service.now()
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    # Get message count (will be 0 for new session)
    message_count = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.session_id == session_id
    ).count()
    
    return schemas.SessionResponse(
        id=chat_session.id,
        name=chat_session.name,
        created_at=chat_session.created_at,
        last_message_at=chat_session.last_message_at,
        message_count=message_count,
        is_active=chat_session.is_active
    )


@app.post("/sessions/auto", response_model=schemas.SessionResponse)
async def create_session_auto(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session with auto-generated name"""
    session_id = str(uuid.uuid4())
    
    # Create session with temporary name
    chat_session = models.ChatSession(
        id=session_id,
        user_id=current_user.id,
        name="New Chat",
        created_at=time_service.now()
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    
    return schemas.SessionResponse(
        id=chat_session.id,
        name=chat_session.name,
        created_at=chat_session.created_at,
        last_message_at=chat_session.last_message_at,
        message_count=0,
        is_active=chat_session.is_active
    )


@app.put("/sessions/{session_id}/generate-name")
async def generate_session_name(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate and update session name based on conversation content"""
    from services.llm_processor import llm_processor
    
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get first few messages from this session
    messages = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.session_id == session_id
    ).order_by(models.Conversation.timestamp.asc()).limit(6).all()
    
    if not messages:
        return {"message": "No messages to generate name from"}
    
    # Generate name using LLM
    new_name = llm_processor.generate_session_name(messages)
    
    # Update session name
    session.name = new_name
    db.commit()
    
    return {"message": f"Session renamed to: {new_name}", "name": new_name}


def get_active_session_id(user_id: int, db: Session) -> Optional[str]:
    """Get the most recent session ID for a user (for proactive messages)"""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == user_id,
        models.ChatSession.is_active == True
    ).order_by(models.ChatSession.last_message_at.desc().nullslast()).first()
    
    return session.id if session else None


@app.get("/sessions", response_model=List[schemas.SessionResponse])
async def get_sessions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sessions for current user"""
    sessions = db.query(models.ChatSession).filter(
        models.ChatSession.user_id == current_user.id
    ).order_by(models.ChatSession.last_message_at.desc().nullslast()).all()
    
    response = []
    for session in sessions:
        # Get message count for each session
        message_count = db.query(models.Conversation).filter(
            models.Conversation.user_id == current_user.id,
            models.Conversation.session_id == session.id
        ).count()
        
        response.append(schemas.SessionResponse(
            id=session.id,
            name=session.name,
            created_at=session.created_at,
            last_message_at=session.last_message_at,
            message_count=message_count,
            is_active=session.is_active
        ))
    
    return response


@app.put("/sessions/{session_id}", response_model=schemas.SessionResponse)
async def update_session(
    session_id: str,
    session_data: schemas.SessionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update session name or archive"""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_data.name is not None:
        session.name = session_data.name
    if session_data.is_active is not None:
        session.is_active = session_data.is_active
    
    db.commit()
    db.refresh(session)
    
    # Get message count
    message_count = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.session_id == session_id
    ).count()
    
    return schemas.SessionResponse(
        id=session.id,
        name=session.name,
        created_at=session.created_at,
        last_message_at=session.last_message_at,
        message_count=message_count,
        is_active=session.is_active
    )


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a session and all its conversations"""
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete all conversations in this session
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.session_id == session_id
    ).all()
    
    # Delete from vector store
    if conversations:
        try:
            for conv in conversations:
                vector_store.conversations_collection.delete(
                    where={"conversation_id": str(conv.id)}
                )
        except Exception as e:
            debug_logger.log(f"Warning: Could not delete from vector store: {e}")
    
    # Delete conversations from database
    db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id,
        models.Conversation.session_id == session_id
    ).delete()
    
    # Delete the session
    db.delete(session)
    db.commit()
    
    return {"detail": "Session deleted successfully"}


# Analytics endpoints
# Habits analytics endpoint - REMOVED in unified system migration
# Use /commitments/analytics/completion-rates instead

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
    # Get all commitments counts
    total_commitments = db.query(func.count(models.Commitment.id)).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.status.in_(["active", "completed"])
    ).scalar()
    
    recurring_commitments = db.query(func.count(models.Commitment.id)).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.recurrence_pattern != "none",
        models.Commitment.status.in_(["active", "completed"])
    ).scalar()
    
    one_time_commitments = db.query(func.count(models.Commitment.id)).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.recurrence_pattern == "none",
        models.Commitment.status.in_(["active", "completed"])
    ).scalar()
    
    # Completed today (both recurring and one-time)
    today = time_service.now().date()
    
    # Count recurring commitments completed today
    recurring_completed_today = db.query(
        func.count(func.distinct(models.CommitmentCompletion.commitment_id))
    ).join(models.Commitment).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.recurrence_pattern != "none",
        models.CommitmentCompletion.completion_date == today,
        models.CommitmentCompletion.skipped == False
    ).scalar()
    
    # Count one-time commitments completed today
    one_time_completed_today = db.query(
        func.count(func.distinct(models.CommitmentCompletion.commitment_id))
    ).join(models.Commitment).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.recurrence_pattern == "none",
        models.CommitmentCompletion.completion_date == today,
        models.CommitmentCompletion.skipped == False
    ).scalar()
    
    completed_today = recurring_completed_today + one_time_completed_today
    
    # Current mood (today's latest checkin)
    today_checkin = db.query(models.DailyCheckIn).filter(
        models.DailyCheckIn.user_id == current_user.id,
        func.date(models.DailyCheckIn.timestamp) == today.isoformat()
    ).order_by(models.DailyCheckIn.timestamp.desc()).first()
    
    # Longest streak calculation - simplified for unified system
    # Get all completions for recurring commitments
    all_completions = db.query(models.CommitmentCompletion).join(models.Commitment).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.recurrence_pattern != "none",
        models.CommitmentCompletion.skipped == False
    ).order_by(models.CommitmentCompletion.completion_date.desc()).limit(365).all()
    
    # Calculate longest streak of any activity
    completion_days = set()
    for completion in all_completions:
        completion_days.add(completion.completion_date)
    
    longest_streak = 0
    current_streak = 0
    check_date = date.today()
    
    for i in range(365):  # Check last year
        if check_date in completion_days:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
        check_date -= timedelta(days=1)
    
    return {
        "total_commitments": total_commitments,
        "recurring_commitments": recurring_commitments,
        "one_time_commitments": one_time_commitments,
        "completed_today": completed_today,
        "completion_rate": round((completed_today / total_commitments) * 100, 1) if total_commitments > 0 else 0,
        "current_mood": today_checkin.mood if today_checkin else None,
        "longest_streak": longest_streak,
        "total_conversations": db.query(func.count(models.Conversation.id)).filter(
            models.Conversation.user_id == current_user.id
        ).scalar(),
        # Keep old field for backward compatibility
        "total_habits": recurring_commitments
    }

@app.get("/analytics/commitments")
def get_commitments_analytics(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for commitments over a specified time period"""
    # Get date range
    end_date = time_service.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get all active commitments for the user
    commitments = db.query(models.Commitment).filter(
        models.Commitment.user_id == current_user.id,
        models.Commitment.status.in_(["active", "completed"])
    ).all()
    
    analytics_data = []
    
    for commitment in commitments:
        # Get completions for this commitment in the date range
        completions = db.query(models.CommitmentCompletion).filter(
            models.CommitmentCompletion.commitment_id == commitment.id,
            models.CommitmentCompletion.completion_date >= start_date,
            models.CommitmentCompletion.completion_date <= end_date,
            models.CommitmentCompletion.skipped == False
        ).all()
        
        # Create daily data array
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            completed_count = len([c for c in completions if c.completion_date == current_date])
            daily_data.append({
                "date": current_date.isoformat(),
                "completed": completed_count
            })
            current_date += timedelta(days=1)
        
        # Calculate completion rate
        if commitment.recurrence_pattern != "none":
            # For recurring commitments, calculate based on expected vs actual completions
            total_expected_days = days
            total_completions = len(completions)
            completion_rate = (total_completions / total_expected_days) * 100 if total_expected_days > 0 else 0
        else:
            # For one-time commitments, it's either 0% or 100%
            total_completions = len(completions)
            completion_rate = 100.0 if total_completions > 0 else 0.0
        
        analytics_data.append({
            "commitment_id": commitment.id,
            "commitment_name": commitment.task_description,
            "completion_rate": round(completion_rate, 1),
            "total_completions": len(completions),
            "total_days": days,
            "recurrence_pattern": commitment.recurrence_pattern,
            "is_recurring": commitment.recurrence_pattern != "none",
            "daily_data": daily_data
        })
    
    return analytics_data

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