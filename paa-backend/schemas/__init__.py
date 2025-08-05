"""
Schemas package for Personal AI Assistant
"""

# Import all base schemas
from .base import (
    # User schemas
    UserBase, UserCreate, User,
    # Habit schemas
    HabitBase, HabitCreate, Habit,
    # Chat schemas
    ChatMessage, ChatMessageEnhanced, ChatResponse,
    # Session schemas
    SessionCreate, SessionUpdate, SessionResponse, ConversationResponse,
    # Check-in schemas
    DailyCheckInCreate, DailyCheckIn,
    # Person schemas
    PersonBase, PersonCreate, PersonUpdate, Person,
    # UserProfile schemas
    UserProfileBase, UserProfileCreate, UserProfileUpdate, UserProfile,
    # Analytics schemas
    HabitAnalytics, MoodAnalytics,
    # Commitment schemas
    CommitmentBase, CommitmentCreate, CommitmentUpdate, Commitment,
    CommitmentCompletionBase, CommitmentCompletionCreate, CommitmentCompletion,
    # ProactiveMessage schemas
    ProactiveMessageBase, ProactiveMessageCreate, ProactiveMessageResponse, ProactiveMessage,
    # ScheduledPrompt schemas
    ScheduledPromptBase, ScheduledPromptCreate, ScheduledPromptUpdate, ScheduledPrompt,
    # Debug schemas
    TimeMultiplierRequest, FakeTimeStartRequest
)

# Import all AI response schemas
from .ai_responses import (
    MessageIntent,
    ReminderStrategy,
    ExtractedCommitment,
    HabitAction,
    PersonUpdate as AIPersonUpdate,  # Renamed to avoid conflict
    ScheduledAction,
    MoodAnalysis,
    ResponseMetadata,
    StructuredAIResponse,
    EnhancedContext,
    ProcessingResult
)

__all__ = [
    # Base schemas
    'UserBase', 'UserCreate', 'User',
    'HabitBase', 'HabitCreate', 'Habit',
    'ChatMessage', 'ChatMessageEnhanced', 'ChatResponse',
    'SessionCreate', 'SessionUpdate', 'SessionResponse', 'ConversationResponse',
    'DailyCheckInCreate', 'DailyCheckIn',
    'PersonBase', 'PersonCreate', 'PersonUpdate', 'Person',
    'UserProfileBase', 'UserProfileCreate', 'UserProfileUpdate', 'UserProfile',
    'HabitAnalytics', 'MoodAnalytics',
    'CommitmentBase', 'CommitmentCreate', 'CommitmentUpdate', 'Commitment',
    'CommitmentCompletionBase', 'CommitmentCompletionCreate', 'CommitmentCompletion',
    'ProactiveMessageBase', 'ProactiveMessageCreate', 'ProactiveMessageResponse', 'ProactiveMessage',
    'ScheduledPromptBase', 'ScheduledPromptCreate', 'ScheduledPromptUpdate', 'ScheduledPrompt',
    'TimeMultiplierRequest', 'FakeTimeStartRequest',
    # AI Response schemas
    'MessageIntent',
    'ReminderStrategy',
    'ExtractedCommitment',
    'HabitAction',
    'AIPersonUpdate',
    'ScheduledAction',
    'MoodAnalysis',
    'ResponseMetadata',
    'StructuredAIResponse',
    'EnhancedContext',
    'ProcessingResult'
]