"""
LLM Processor for Hybrid Pipeline Architecture
Handles structured prompt engineering and response parsing.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from anthropic import Anthropic
from schemas.ai_responses import (
    MessageIntent, StructuredAIResponse, ExtractedCommitment,
    ReminderStrategy, HabitAction, MoodAnalysis, ResponseMetadata,
    EnhancedContext, ScheduledAction, PersonUpdate as AIPersonUpdate
)
from services.time_service import time_service

logger = logging.getLogger(__name__)


class HybridLLMProcessor:
    """Process messages with structured output guarantees"""
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        self.anthropic_client = anthropic_client
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for structured output"""
        return """You are a proactive AI assistant helping users manage their habits, commitments, and personal well-being.

Your responses must be in valid JSON format matching the StructuredAIResponse schema:
{
    "message": "Your conversational response to the user",
    "commitments": [...],  // Extracted commitments with reminders
    "habit_actions": [...],  // Habit-related actions to take
    "people_updates": [...],  // Updates about people mentioned
    "scheduled_actions": [...],  // Proactive follow-ups to schedule
    "mood_analysis": {...},  // If mood is detected
    "response_metadata": {
        "requires_user_confirmation": false,
        "confidence_level": 0.9,
        "alternative_interpretations": [],
        "context_used": []
    }
}

Guidelines:
1. Extract ALL commitments with specific or fuzzy deadlines
2. Detect habit completions and log them appropriately
3. Note any people mentioned for relationship tracking
4. Analyze emotional state when expressed
5. Schedule proactive follow-ups when appropriate
6. Be encouraging and supportive
7. Keep responses concise but warm

For commitments:
- Parse natural language deadlines (today, tomorrow, next week, etc.)
- Set appropriate reminder strategies based on urgency
- Include related people or habits when mentioned

For habits:
- Detect when users report completing habits
- Suggest creating new habits when patterns emerge
- Provide encouragement for streaks

For mood:
- Detect emotional indicators in the message
- Suggest appropriate interventions
- Schedule check-ins if concerning mood detected

Always respond with valid JSON matching the schema."""
    
    def process_message(
        self,
        message: str,
        intent: MessageIntent,
        context: EnhancedContext,
        user_data: Optional[Dict[str, Any]] = None
    ) -> StructuredAIResponse:
        """
        Process a message with structured output.
        
        Args:
            message: User's message
            intent: Classified intent
            context: Retrieved context
            user_data: Optional user-specific data
            
        Returns:
            StructuredAIResponse with all extracted information
        """
        # Build the prompt
        prompt = self._build_structured_prompt(message, intent, context, user_data)
        
        # If no Anthropic client, return a demo response
        if not self.anthropic_client:
            return self._generate_demo_response(message, intent, context)
        
        try:
            # Call Anthropic API
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse the response
            response_text = response.content[0].text
            
            # Try to parse as JSON
            try:
                response_data = json.loads(response_text)
                return self._parse_structured_response(response_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {response_text}")
                # Return a fallback response
                return self._create_fallback_response(message, response_text)
                
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return self._generate_demo_response(message, intent, context)
    
    def _build_structured_prompt(
        self,
        message: str,
        intent: MessageIntent,
        context: EnhancedContext,
        user_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a structured prompt with all context"""
        prompt_parts = []
        
        # Current time context
        now = time_service.now()
        prompt_parts.append(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        prompt_parts.append(f"Day of week: {now.strftime('%A')}")
        
        # User message
        prompt_parts.append(f"\nUser message: {message}")
        
        # Intent analysis
        prompt_parts.append(f"\nDetected intent: {intent.primary_intent}")
        if intent.secondary_intents:
            prompt_parts.append(f"Secondary intents: {', '.join(intent.secondary_intents)}")
        
        # Entities
        if any(intent.entities.values()):
            prompt_parts.append("\nExtracted entities:")
            for entity_type, values in intent.entities.items():
                if values:
                    prompt_parts.append(f"  {entity_type}: {', '.join(values)}")
        
        # Context
        if context.conversations:
            prompt_parts.append("\nRecent conversations:")
            for conv in context.conversations[:3]:
                prompt_parts.append(f"  - {conv.get('timestamp', 'Unknown time')}: {conv.get('message', '')}")
        
        if context.habit_context:
            prompt_parts.append("\nUser's habits:")
            for habit_name, habit_data in context.habit_context.items():
                streak = habit_data.get('current_streak', 0)
                completed_today = habit_data.get('completed_today', False)
                prompt_parts.append(f"  - {habit_name}: {streak} day streak, {'completed' if completed_today else 'not completed'} today")
        
        if context.people_context:
            prompt_parts.append("\nPeople mentioned:")
            for person_name, person_data in context.people_context.items():
                prompt_parts.append(f"  - {person_name}: {person_data.get('relationship', 'Unknown relationship')}")
        
        if context.mood_patterns:
            prompt_parts.append(f"\nRecent mood: {context.mood_patterns.get('recent_average', 'Unknown')}")
        
        # User data if provided
        if user_data:
            if user_data.get('profile'):
                prompt_parts.append(f"\nUser profile: {user_data['profile'].get('name', 'Unknown')}")
        
        prompt_parts.append("\nPlease provide a structured JSON response following the StructuredAIResponse schema.")
        
        return "\n".join(prompt_parts)
    
    def _parse_structured_response(self, response_data: Dict[str, Any]) -> StructuredAIResponse:
        """Parse the LLM response into our structured format"""
        # Parse commitments
        commitments = []
        for commit_data in response_data.get('commitments', []):
            # Parse deadline
            deadline = None
            if commit_data.get('deadline'):
                try:
                    deadline = datetime.fromisoformat(commit_data['deadline'].replace('Z', '+00:00'))
                except:
                    deadline = self._parse_fuzzy_deadline(commit_data.get('deadline', ''))
            
            # Parse reminder strategy
            reminder_data = commit_data.get('reminder_strategy', {})
            initial_reminder = reminder_data.get('initial_reminder')
            if initial_reminder:
                try:
                    initial_reminder = datetime.fromisoformat(initial_reminder.replace('Z', '+00:00'))
                except:
                    initial_reminder = deadline - timedelta(hours=1) if deadline else time_service.now() + timedelta(hours=1)
            else:
                initial_reminder = deadline - timedelta(hours=1) if deadline else time_service.now() + timedelta(hours=1)
            
            follow_ups = []
            for fu in reminder_data.get('follow_up_reminders', []):
                try:
                    follow_ups.append(datetime.fromisoformat(fu.replace('Z', '+00:00')))
                except:
                    pass
            
            reminder_strategy = ReminderStrategy(
                initial_reminder=initial_reminder,
                follow_up_reminders=follow_ups,
                escalation=reminder_data.get('escalation', 'gentle'),
                custom_message=reminder_data.get('custom_message')
            )
            
            commitment = ExtractedCommitment(
                task_description=commit_data.get('task_description', ''),
                deadline=deadline,
                deadline_type=commit_data.get('deadline_type', 'fuzzy'),
                priority=commit_data.get('priority', 'medium'),
                reminder_strategy=reminder_strategy,
                related_people=commit_data.get('related_people', []),
                related_habits=commit_data.get('related_habits', [])
            )
            commitments.append(commitment)
        
        # Parse habit actions
        habit_actions = []
        for habit_data in response_data.get('habit_actions', []):
            action = HabitAction(
                action_type=habit_data.get('action_type', 'log_completion'),
                habit_identifier=habit_data.get('habit_identifier', ''),
                details=habit_data.get('details', {}),
                completion_date=habit_data.get('completion_date'),
                notes=habit_data.get('notes'),
                new_habit_details=habit_data.get('new_habit_details')
            )
            habit_actions.append(action)
        
        # Parse people updates
        people_updates = []
        for person_data in response_data.get('people_updates', []):
            update = AIPersonUpdate(
                person_name=person_data.get('person_name', ''),
                update_type=person_data.get('update_type', 'add_note'),
                content=person_data.get('content', ''),
                tags=person_data.get('tags', [])
            )
            people_updates.append(update)
        
        # Parse scheduled actions
        scheduled_actions = []
        for sched_data in response_data.get('scheduled_actions', []):
            send_time = sched_data.get('send_time')
            if send_time:
                try:
                    send_time = datetime.fromisoformat(send_time.replace('Z', '+00:00'))
                except:
                    send_time = time_service.now() + timedelta(hours=1)
            else:
                send_time = time_service.now() + timedelta(hours=1)
            
            action = ScheduledAction(
                message_content=sched_data.get('message_content', ''),
                send_time=send_time,
                trigger_type=sched_data.get('trigger_type', 'time_based'),
                trigger_condition=sched_data.get('trigger_condition'),
                expected_response_type=sched_data.get('expected_response_type')
            )
            scheduled_actions.append(action)
        
        # Parse mood analysis
        mood_analysis = None
        if response_data.get('mood_analysis'):
            mood_data = response_data['mood_analysis']
            mood_analysis = MoodAnalysis(
                detected_mood=mood_data.get('detected_mood', 'neutral'),
                confidence=mood_data.get('confidence', 0.5),
                contributing_factors=mood_data.get('contributing_factors', []),
                suggested_interventions=mood_data.get('suggested_interventions', []),
                should_check_in_later=mood_data.get('should_check_in_later', False)
            )
        
        # Parse metadata
        metadata_data = response_data.get('response_metadata', {})
        metadata = ResponseMetadata(
            requires_user_confirmation=metadata_data.get('requires_user_confirmation', False),
            confidence_level=metadata_data.get('confidence_level', 0.8),
            alternative_interpretations=metadata_data.get('alternative_interpretations', []),
            context_used=metadata_data.get('context_used', [])
        )
        
        return StructuredAIResponse(
            message=response_data.get('message', 'I understand. Let me help you with that.'),
            commitments=commitments,
            habit_actions=habit_actions,
            people_updates=people_updates,
            scheduled_actions=scheduled_actions,
            mood_analysis=mood_analysis,
            response_metadata=metadata
        )
    
    def _parse_fuzzy_deadline(self, deadline_str: str) -> Optional[datetime]:
        """Parse fuzzy deadline strings"""
        now = time_service.now()
        deadline_lower = deadline_str.lower()
        
        if 'today' in deadline_lower:
            return now.replace(hour=23, minute=59, second=59)
        elif 'tomorrow' in deadline_lower:
            return (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif 'next week' in deadline_lower:
            return (now + timedelta(days=7)).replace(hour=23, minute=59, second=59)
        elif 'this week' in deadline_lower:
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            return (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59)
        
        return None
    
    def _create_fallback_response(self, message: str, raw_response: str) -> StructuredAIResponse:
        """Create a fallback response when JSON parsing fails"""
        # Extract the conversational part if possible
        conversational_response = raw_response
        if len(raw_response) > 500:
            conversational_response = raw_response[:500] + "..."
        
        return StructuredAIResponse(
            message=conversational_response,
            commitments=[],
            habit_actions=[],
            people_updates=[],
            scheduled_actions=[],
            mood_analysis=None,
            response_metadata=ResponseMetadata(
                requires_user_confirmation=False,
                confidence_level=0.5,
                alternative_interpretations=[],
                context_used=["fallback_mode"]
            )
        )
    
    def _generate_demo_response(
        self,
        message: str,
        intent: MessageIntent,
        context: EnhancedContext
    ) -> StructuredAIResponse:
        """Generate a demo response when no API is available"""
        now = time_service.now()
        
        # Base response
        response = StructuredAIResponse(
            message="I understand. Let me help you with that.",
            commitments=[],
            habit_actions=[],
            people_updates=[],
            scheduled_actions=[],
            mood_analysis=None,
            response_metadata=ResponseMetadata(
                requires_user_confirmation=False,
                confidence_level=0.8,
                alternative_interpretations=[],
                context_used=["demo_mode"]
            )
        )
        
        # Customize based on intent
        if intent.primary_intent == 'commitment_making':
            response.message = "I've noted your commitment. I'll remind you when it's time!"
            
            # Extract a simple commitment
            task = "complete the task"
            deadline = now + timedelta(days=1)
            
            # Look for task description in entities
            if intent.entities.get('actions'):
                task = f"{intent.entities['actions'][0]} the task"
            
            # Look for time references
            if 'tomorrow' in message.lower():
                deadline = (now + timedelta(days=1)).replace(hour=17, minute=0)
            elif 'today' in message.lower():
                deadline = now.replace(hour=23, minute=59)
            
            response.commitments.append(
                ExtractedCommitment(
                    task_description=task,
                    deadline=deadline,
                    deadline_type='specific',
                    priority='medium',
                    reminder_strategy=ReminderStrategy(
                        initial_reminder=deadline - timedelta(hours=2),
                        follow_up_reminders=[deadline - timedelta(minutes=30)],
                        escalation='gentle'
                    ),
                    related_people=intent.entities.get('people', []),
                    related_habits=intent.entities.get('habits', [])
                )
            )
        
        elif intent.primary_intent == 'habit_tracking':
            response.message = "Great job on completing your habit! Keep up the good work!"
            
            # Find habit name
            habit_name = "your habit"
            if intent.entities.get('habits'):
                habit_name = intent.entities['habits'][0]
            
            response.habit_actions.append(
                HabitAction(
                    action_type='log_completion',
                    habit_identifier=habit_name,
                    details={'source': 'chat'},
                    completion_date=now.date(),
                    notes="Completed via chat"
                )
            )
        
        elif intent.primary_intent == 'mood_reflection':
            response.message = "Thank you for sharing how you're feeling. I'm here to support you."
            
            # Detect mood from emotions
            detected_mood = 'neutral'
            if intent.entities.get('emotions'):
                emotion = intent.entities['emotions'][0].lower()
                if emotion in ['happy', 'excited', 'great', 'good']:
                    detected_mood = 'positive'
                elif emotion in ['sad', 'anxious', 'stressed', 'worried']:
                    detected_mood = 'negative'
            
            response.mood_analysis = MoodAnalysis(
                detected_mood=detected_mood,
                confidence=0.7,
                contributing_factors=intent.entities.get('emotions', []),
                suggested_interventions=[],
                should_check_in_later=detected_mood == 'negative'
            )
            
            if detected_mood == 'negative':
                response.scheduled_actions.append(
                    ScheduledAction(
                        message_content="Hi! Just checking in to see how you're feeling now. How has your day been?",
                        send_time=now + timedelta(hours=3),
                        trigger_type='time_based'
                    )
                )
        
        elif intent.primary_intent == 'information_query':
            response.message = "Based on your data, here's what I found..."
            response.response_metadata.requires_user_confirmation = False
        
        else:
            response.message = "I'm here to help! Feel free to tell me about your habits, commitments, or how you're feeling."
        
        return response


# Global instance for easy importing
llm_processor = HybridLLMProcessor()