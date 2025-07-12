from pydantic import BaseModel
from datetime import datetime
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