from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional, List

# User schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Habit schemas
class HabitBase(BaseModel):
    name: str
    frequency: str = "daily"
    reminder_time: Optional[str] = None

class HabitCreate(HabitBase):
    pass

class Habit(HabitBase):
    id: int
    user_id: int
    created_at: datetime
    is_active: int
    completed_today: bool = False
    current_streak: int = 0
    
    class Config:
        from_attributes = True

# Chat schemas
class ChatMessage(BaseModel):
    message: str

class ChatMessageEnhanced(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    message: str
    response: str
    timestamp: datetime

# Session schemas
class SessionCreate(BaseModel):
    name: str

class SessionUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class SessionResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    last_message_at: Optional[datetime]
    message_count: int
    is_active: bool

class ConversationResponse(BaseModel):
    id: int
    message: str
    response: str
    timestamp: datetime
    session_id: str
    session_name: str

# Check-in schemas
class DailyCheckInCreate(BaseModel):
    mood: int  # 1-5
    notes: Optional[str] = None

class DailyCheckIn(DailyCheckInCreate):
    id: int
    user_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Person schemas
class PersonBase(BaseModel):
    name: str
    how_you_know_them: Optional[str] = None
    pronouns: Optional[str] = None
    description: Optional[str] = None

class PersonCreate(PersonBase):
    pass

class PersonUpdate(PersonBase):
    pass

class Person(PersonBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# UserProfile schemas
class UserProfileBase(BaseModel):
    name: str
    how_you_know_them: Optional[str] = None
    pronouns: Optional[str] = None
    description: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    name: Optional[str] = None

class UserProfile(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Analytics schemas
class HabitAnalytics(BaseModel):
    habit_id: int
    habit_name: str
    total_completions: int
    current_streak: int
    completion_rate: float

class MoodAnalytics(BaseModel):
    average_mood: float
    mood_trend: List[dict]  # [{date: str, mood: int}]

# Commitment schemas (unified system - handles both one-time and recurring)
class CommitmentBase(BaseModel):
    task_description: str
    original_message: Optional[str] = None
    deadline: Optional[date] = None
    recurrence_pattern: str = "none"  # none, daily, weekly, monthly, custom
    recurrence_interval: int = 1  # Every N days/weeks/months
    recurrence_days: Optional[str] = None  # For weekly: "mon,wed,fri"
    recurrence_end_date: Optional[date] = None
    due_time: Optional[time] = None
    reminder_settings: Optional[dict] = None

class CommitmentCreate(CommitmentBase):
    created_from_conversation_id: Optional[int] = None

class CommitmentUpdate(BaseModel):
    task_description: Optional[str] = None
    status: Optional[str] = None  # pending, completed, missed, dismissed, active, archived
    deadline: Optional[date] = None
    recurrence_pattern: Optional[str] = None
    recurrence_interval: Optional[int] = None
    recurrence_days: Optional[str] = None
    recurrence_end_date: Optional[date] = None
    due_time: Optional[time] = None
    reminder_settings: Optional[dict] = None

class Commitment(CommitmentBase):
    id: int
    user_id: int
    status: str
    created_from_conversation_id: Optional[int] = None
    last_reminded_at: Optional[datetime] = None
    reminder_count: int
    created_at: datetime
    completion_count: int = 0
    last_completed_at: Optional[datetime] = None
    
    # Helper properties
    is_recurring: bool = False
    completed_today: bool = False
    
    class Config:
        from_attributes = True

# Commitment completion schemas
class CommitmentCompletionBase(BaseModel):
    notes: Optional[str] = None
    completion_date: Optional[date] = None  # Defaults to today
    skipped: bool = False

class CommitmentCompletionCreate(CommitmentCompletionBase):
    pass

class CommitmentCompletion(CommitmentCompletionBase):
    id: int
    commitment_id: int
    user_id: int
    completed_at: datetime
    completion_date: date
    
    class Config:
        from_attributes = True

# ProactiveMessage schemas
class ProactiveMessageBase(BaseModel):
    message_type: str  # commitment_reminder, scheduled_prompt, escalation
    content: str
    related_commitment_id: Optional[int] = None
    scheduled_for: Optional[datetime] = None

class ProactiveMessageCreate(ProactiveMessageBase):
    pass

class ProactiveMessageResponse(BaseModel):
    response_content: str

class ProactiveMessage(ProactiveMessageBase):
    id: int
    user_id: int
    session_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    user_responded: bool
    response_content: Optional[str] = None
    
    class Config:
        from_attributes = True

# ScheduledPrompt schemas
class ScheduledPromptBase(BaseModel):
    prompt_type: str  # work_checkin, morning_motivation, evening_reflection
    schedule_time: time
    schedule_days: str  # "monday,tuesday,wednesday,thursday,friday"
    prompt_template: str
    is_active: bool = True

class ScheduledPromptCreate(ScheduledPromptBase):
    pass

class ScheduledPromptUpdate(BaseModel):
    prompt_type: Optional[str] = None
    schedule_time: Optional[time] = None
    schedule_days: Optional[str] = None
    prompt_template: Optional[str] = None
    is_active: Optional[bool] = None

class ScheduledPrompt(ScheduledPromptBase):
    id: int
    user_id: int
    last_sent_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Debug schemas
class TimeMultiplierRequest(BaseModel):
    multiplier: int

class FakeTimeStartRequest(BaseModel):
    time_multiplier: int = 600
    fake_start_time: Optional[str] = None