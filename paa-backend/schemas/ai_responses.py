"""
Structured AI Response Schemas for Hybrid Pipeline Architecture
These schemas ensure consistent, parseable outputs from the LLM.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Dict, Literal, Optional, Any


# Intent Classification Schema
class MessageIntent(BaseModel):
    """First stage: Understand what the user wants"""
    primary_intent: Literal[
        'habit_tracking',      # "I worked out today"
        'commitment_making',   # "I'll call mom tomorrow"
        'social_reference',    # "John mentioned a good book"
        'mood_reflection',     # "Feeling anxious about work"
        'information_query',   # "How many times did I meditate?"
        'general_chat'        # "Tell me a joke"
    ]
    
    secondary_intents: List[str] = Field(default_factory=list)  # Multiple intents possible
    
    entities: Dict[str, List[str]] = Field(default_factory=lambda: {
        'people': [],          # ["mom", "John"]
        'habits': [],          # ["workout", "meditate"]
        'time_references': [], # ["tomorrow", "last week"]
        'emotions': [],        # ["anxious", "happy"]
        'actions': []          # ["call", "worked out"]
    })
    
    context_needed: List[Literal[
        'recent_conversations',
        'habit_history',
        'person_profile',
        'mood_trends',
        'similar_commitments',
        'temporal_context'
    ]] = Field(default_factory=list)
    
    urgency: Literal['immediate', 'normal', 'low'] = 'normal'
    confidence: float = Field(ge=0.0, le=1.0)


# Reminder Strategy Schema
class ReminderStrategy(BaseModel):
    """How to remind about this commitment"""
    initial_reminder: datetime
    follow_up_reminders: List[datetime] = Field(default_factory=list)
    escalation: Literal['gentle', 'persistent', 'urgent'] = 'gentle'
    custom_message: Optional[str] = None


# Extracted Commitment Schema (Enhanced for unified system)
class ExtractedCommitment(BaseModel):
    """When user makes a commitment (one-time or recurring)"""
    task_description: str
    deadline: Optional[datetime] = None
    deadline_type: Literal['specific', 'fuzzy', 'recurring'] = 'fuzzy'
    priority: Literal['high', 'medium', 'low'] = 'medium'
    
    # Recurrence fields for unified system
    recurrence_pattern: Literal['none', 'daily', 'weekly', 'monthly', 'custom'] = 'none'
    recurrence_days: Optional[List[str]] = None  # ['mon', 'wed', 'fri']
    due_time: Optional[str] = None  # "07:00" for recurring tasks
    
    reminder_strategy: ReminderStrategy
    related_people: List[str] = Field(default_factory=list)
    related_habits: List[str] = Field(default_factory=list)


# Habit Action Schema
class HabitAction(BaseModel):
    """Actions related to habits"""
    action_type: Literal['log_completion', 'update_schedule', 'create_new', 'modify_existing']
    habit_identifier: str
    details: Dict[str, Any] = Field(default_factory=dict)
    completion_date: Optional[date] = None
    notes: Optional[str] = None
    new_habit_details: Optional[Dict[str, Any]] = None


# Person Update Schema
class PersonUpdate(BaseModel):
    """Updates to relationship/people data"""
    person_name: str
    update_type: Literal['add_note', 'create_new', 'update_info']
    content: str
    tags: List[str] = Field(default_factory=list)


# Scheduled Action Schema
class ScheduledAction(BaseModel):
    """Proactive messages to schedule"""
    message_content: str
    send_time: datetime
    trigger_type: Literal['time_based', 'event_based', 'condition_based']
    trigger_condition: Optional[Dict[str, Any]] = None
    expected_response_type: Optional[str] = None
    follow_up_if_no_response: Optional['ScheduledAction'] = None


# Mood Analysis Schema
class MoodAnalysis(BaseModel):
    """Emotional state analysis"""
    detected_mood: Literal['very_positive', 'positive', 'neutral', 'negative', 'very_negative']
    confidence: float = Field(ge=0.0, le=1.0)
    contributing_factors: List[str] = Field(default_factory=list)
    suggested_interventions: List[str] = Field(default_factory=list)
    should_check_in_later: bool = False


# Response Metadata Schema
class ResponseMetadata(BaseModel):
    """Meta information about the response"""
    requires_user_confirmation: bool = False
    confidence_level: float = Field(ge=0.0, le=1.0)
    alternative_interpretations: List[str] = Field(default_factory=list)
    context_used: List[str] = Field(default_factory=list)


# User Profile Update Schema
class UserProfileUpdate(BaseModel):
    """Update to user's own profile information"""
    update_type: Literal['add_info', 'update_info', 'append_info']
    content: str
    category: Optional[Literal['personal', 'professional', 'preferences', 'goals', 'general']] = 'general'


# Enhanced Context Schema for RAG System
class EnhancedContext(BaseModel):
    """Context retrieved by the RAG system"""
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    people_context: Dict[str, Any] = Field(default_factory=dict)
    habit_context: Dict[str, Any] = Field(default_factory=dict)
    mood_patterns: Dict[str, Any] = Field(default_factory=dict)
    similar_commitments: List[Dict[str, Any]] = Field(default_factory=list)
    temporal: Dict[str, Any] = Field(default_factory=dict)
    semantic_matches: List[Dict[str, Any]] = Field(default_factory=list)


# Main Structured AI Response Schema
class StructuredAIResponse(BaseModel):
    """The complete structured response from the LLM"""
    
    message: str  # The conversational response
    commitments: List[ExtractedCommitment] = Field(default_factory=list)
    habit_actions: List[HabitAction] = Field(default_factory=list)
    people_updates: List[PersonUpdate] = Field(default_factory=list)
    user_profile_updates: List[UserProfileUpdate] = Field(default_factory=list)
    scheduled_actions: List[ScheduledAction] = Field(default_factory=list)
    mood_analysis: Optional[MoodAnalysis] = None
    response_metadata: ResponseMetadata



# Processing Result Schema
class ProcessingResult(BaseModel):
    """Result of processing all actions from structured response"""
    outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    def summary(self) -> Dict[str, Any]:
        """Get a summary of processing outcomes"""
        successful = [o for o in self.outcomes if o.get('success', False)]
        failed = [o for o in self.outcomes if not o.get('success', False)]
        
        return {
            'total_actions': len(self.outcomes),
            'successful': len(successful),
            'failed': len(failed),
            'errors': self.errors
        }
    
    def get_user_visible_actions(self) -> List[str]:
        """Get actions that should be shown to the user"""
        visible_actions = []
        for outcome in self.outcomes:
            if outcome.get('user_visible', True) and outcome.get('description'):
                visible_actions.append(outcome['description'])
        return visible_actions


# Update model forward reference
ScheduledAction.model_rebuild()