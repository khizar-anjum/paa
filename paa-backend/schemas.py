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

class ChatResponse(BaseModel):
    message: str
    response: str
    timestamp: datetime

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

# Commitment schemas
class CommitmentBase(BaseModel):
    task_description: str
    original_message: Optional[str] = None
    deadline: Optional[date] = None

class CommitmentCreate(CommitmentBase):
    created_from_conversation_id: Optional[int] = None

class CommitmentUpdate(BaseModel):
    status: Optional[str] = None  # pending, completed, missed, dismissed
    deadline: Optional[date] = None

class Commitment(CommitmentBase):
    id: int
    user_id: int
    status: str
    created_from_conversation_id: Optional[int] = None
    last_reminded_at: Optional[datetime] = None
    reminder_count: int
    created_at: datetime
    
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