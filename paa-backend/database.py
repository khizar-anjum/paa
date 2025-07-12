from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./paa.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    habits = relationship("Habit", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    checkins = relationship("DailyCheckIn", back_populates="user")
    people = relationship("Person", back_populates="user")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    commitments = relationship("Commitment", back_populates="user")
    proactive_messages = relationship("ProactiveMessage", back_populates="user")
    scheduled_prompts = relationship("ScheduledPrompt", back_populates="user")

class Habit(Base):
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    frequency = Column(String, default="daily")  # daily, weekly
    reminder_time = Column(String)  # Store as "HH:MM"
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)
    
    user = relationship("User", back_populates="habits")
    logs = relationship("HabitLog", back_populates="habit")

class HabitLog(Base):
    __tablename__ = "habit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"))
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    habit = relationship("Habit", back_populates="logs")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")

class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mood = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="checkins")

class Person(Base):
    __tablename__ = "people"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    how_you_know_them = Column(Text)
    pronouns = Column(String)
    description = Column(Text)  # Markdown compatible
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="people")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)  # One profile per user
    name = Column(String, nullable=False)
    how_you_know_them = Column(Text)  # About yourself/background
    pronouns = Column(String)
    description = Column(Text)  # Markdown compatible
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="profile")

class Commitment(Base):
    __tablename__ = "commitments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_description = Column(Text, nullable=False)
    original_message = Column(Text)
    deadline = Column(Date)
    status = Column(String, default="pending")  # pending, completed, missed, dismissed
    created_from_conversation_id = Column(Integer, ForeignKey("conversations.id"))
    last_reminded_at = Column(DateTime)
    reminder_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="commitments")
    conversation = relationship("Conversation")

class ProactiveMessage(Base):
    __tablename__ = "proactive_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message_type = Column(String)  # commitment_reminder, scheduled_prompt, escalation
    content = Column(Text, nullable=False)
    related_commitment_id = Column(Integer, ForeignKey("commitments.id"))
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    user_responded = Column(Boolean, default=False)
    response_content = Column(Text)
    
    user = relationship("User", back_populates="proactive_messages")
    commitment = relationship("Commitment")

class ScheduledPrompt(Base):
    __tablename__ = "scheduled_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt_type = Column(String)  # work_checkin, morning_motivation, evening_reflection
    schedule_time = Column(Time)
    schedule_days = Column(String)  # "monday,tuesday,wednesday,thursday,friday"
    prompt_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="scheduled_prompts")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()