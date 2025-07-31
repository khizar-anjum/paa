"""
LLM Processor for Hybrid Pipeline Architecture
Handles structured prompt engineering and response parsing.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from anthropic import Anthropic
from schemas.ai_responses import (
    MessageIntent, StructuredAIResponse, ExtractedCommitment,
    ReminderStrategy, HabitAction, MoodAnalysis, ResponseMetadata,
    EnhancedContext, ScheduledAction, PersonUpdate as AIPersonUpdate
)
from services.time_service import time_service
from debug_logger import debug_logger

logger = logging.getLogger(__name__)


class HybridLLMProcessor:
    """Process messages with structured output guarantees"""
    
    def __init__(self, anthropic_client: Optional[Anthropic] = None):
        self.anthropic_client = anthropic_client
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for structured output"""
        return """You are a proactive AI assistant helping users manage their habits, commitments, and personal well-being.

OUTPUT FORMAT SPECIFICATION:
You MUST output ONLY valid JSON that precisely matches the StructuredAIResponse schema below. Your response must:
- Start with { and end with }
- Contain no text before or after the JSON
- Include every required field from the schema
- Use exact field names and data types as specified
- Follow ISO datetime formats where specified

REQUIRED JSON SCHEMA (you must match this exactly):
{
    "message": "Your conversational response to the user",
    "commitments": [
        {
            "task_description": "description of the task",
            "deadline": "2025-07-29T23:59:59",
            "deadline_type": "specific",
            "priority": "medium",
            "reminder_strategy": {
                "initial_reminder": "2025-07-29T22:00:00",
                "follow_up_reminders": ["2025-07-29T23:30:00"],
                "escalation": "gentle",
                "custom_message": null
            },
            "related_people": [],
            "related_habits": []
        }
    ],
    "habit_actions": [
        {
            "action_type": "log_completion",
            "habit_identifier": "habit name",
            "details": {},
            "completion_date": "2025-07-29",
            "notes": null,
            "new_habit_details": null
        }
    ],
    "people_updates": [
        {
            "person_name": "Name",
            "update_type": "add_note",
            "content": "update content",
            "tags": []
        }
    ],
    "user_profile_updates": [
        {
            "update_type": "add_info",
            "content": "looking for a roommate",
            "category": "personal"
        }
    ],
    "scheduled_actions": [
        {
            "message_content": "follow up message",
            "send_time": "2025-07-30T10:00:00",
            "trigger_type": "time_based",
            "trigger_condition": null,
            "expected_response_type": null
        }
    ],
    "mood_analysis": {
        "detected_mood": "neutral",
        "confidence": 0.8,
        "contributing_factors": [],
        "suggested_interventions": [],
        "should_check_in_later": false
    },
    "response_metadata": {
        "requires_user_confirmation": false,
        "confidence_level": 0.9,
        "alternative_interpretations": [],
        "context_used": []
    }
}

FIELD REQUIREMENTS:
- "message": String - Your conversational response to the user (required)
- "commitments": Array - Only for NEW commitments the user is making (required, can be empty [])
- "habit_actions": Array - Actions related to habits (required, can be empty [])
- "people_updates": Array - Updates about OTHER people (required, can be empty [])
- "user_profile_updates": Array - Updates to user's own profile (required, can be empty [])
- "scheduled_actions": Array - Proactive messages to schedule (required, can be empty [])
- "mood_analysis": Object or null - Mood detection (required)
- "response_metadata": Object - Meta information (required)

CRITICAL DATA FORMATTING:
- Datetime fields: ISO format "2025-07-29T23:59:59"
- Date fields: "2025-07-29"
- Use "task_description" NOT "title" or "name" for commitments
- deadline_type: must be "specific", "fuzzy", or "recurring"
- priority: must be "high", "medium", or "low"
- detected_mood: must be "very_positive", "positive", "neutral", "negative", or "very_negative"

CONTENT GUIDELINES:
- For information queries: describe existing data in "message", don't create new objects
- User personal info (roommate search, job status, goals): use "user_profile_updates"  
- Information about other people: use "people_updates"
- Be encouraging and supportive in the "message" field

Your output must be parseable JSON that validates against this exact schema."""
    
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
        start_time = time.time()
        
        # Debug logging - start
        if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
            context_summary = {
                "conversations": len(context.conversations) if hasattr(context, 'conversations') and context.conversations else 0,
                "habits": len(context.habit_context) if hasattr(context, 'habit_context') and context.habit_context else 0,
                "people": len(context.people_context) if hasattr(context, 'people_context') and context.people_context else 0,
                "semantic_matches": len(context.semantic_matches) if hasattr(context, 'semantic_matches') and context.semantic_matches else 0
            }
            debug_logger.log_llm_call_start(message, context_summary, intent.primary_intent)
        
        # Build the prompt
        prompt = self._build_structured_prompt(message, intent, context, user_data)
        
        # If no Anthropic client, return a demo response
        if not self.anthropic_client:
            return self._generate_demo_response(message, intent, context)
        
        try:
            # Call Anthropic API
            api_start_time = time.time()
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            api_call_time = (time.time() - api_start_time) * 1000  # Convert to milliseconds
            
            # Parse the response
            response_text = response.content[0].text
            
            # Clean up any system reminder tags that might have been injected
            import re
            response_text = re.sub(r'<system-reminder>.*?</system-reminder>', '', response_text, flags=re.DOTALL)
            response_text = response_text.strip()
            
            # Debug logging - show raw LLM response
            if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                debug_logger.debug(f"🤖 Raw LLM Response: {response_text[:1000]}{'...' if len(response_text) > 1000 else ''}")
                debug_logger.debug(f"🔍 Response starts with: {response_text[:100]}")
                debug_logger.debug(f"🔍 Response contains JSON-like content: {'{' in response_text and '}' in response_text}")
                debug_logger.debug(f"🔍 Response is valid JSON: {self._is_valid_json(response_text)}")
            
            # Estimate tokens (rough approximation)
            tokens_estimate = len(prompt.split()) + len(response_text.split())
            
            # Try to parse as JSON
            try:
                # First try direct JSON parsing
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
                if json_match:
                    try:
                        response_data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        raise
                else:
                    raise
            
            # Check if response_data is a dictionary (structured response)
            if not isinstance(response_data, dict):
                logger.warning(f"API returned non-dict JSON: {type(response_data)}")
                return self._create_fallback_response(message, response_text)
            
            try:
                structured_response = self._parse_structured_response(response_data)
            except Exception as schema_error:
                logger.error(f"Schema parsing failed: {schema_error}")
                logger.debug(f"Raw response data: {json.dumps(response_data, indent=2)}")
                return self._create_fallback_response(message, response_text)
            
            # Debug logging - success
            if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                debug_logger.log_llm_call_result(
                    prompt_length=len(prompt),
                    response_length=len(response_text),
                    api_call_time=api_call_time,
                    tokens_used=tokens_estimate,
                    structured_output=structured_response.dict()
                )
            
            return structured_response
                
        except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {response_text}")
                
                # Debug logging - JSON parse error
                if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                    debug_logger.log_llm_call_result(
                        prompt_length=len(prompt),
                        response_length=len(response_text),
                        api_call_time=api_call_time,
                        tokens_used=tokens_estimate,
                        structured_output={"error": "JSON parse failed", "raw_response": response_text[:200]}
                    )
                
                # Return a fallback response
                return self._create_fallback_response(message, response_text)
                
        except Exception as e:
            # Add more detailed error information
            import traceback
            error_details = traceback.format_exc()
            if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                debug_logger.error(f"❌ LLM Processing Error: {e}")
                debug_logger.debug(f"Full traceback: {error_details}")
            else:
                logger.error(f"Error calling Anthropic API: {e}")
            
            # Debug logging - API error
            if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                debug_logger.log_llm_call_result(
                    prompt_length=len(prompt),
                    response_length=0,
                    api_call_time=(time.time() - start_time) * 1000,
                    tokens_used=0,
                    structured_output={"error": str(e), "traceback": error_details[:500]}
                )
            
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
                # Defensive programming: ensure conv is a dictionary
                if isinstance(conv, dict):
                    timestamp = conv.get('timestamp', 'Unknown time')
                    message = conv.get('message', '')
                    prompt_parts.append(f"  - {timestamp}: {message}")
                else:
                    # Handle unexpected format gracefully
                    prompt_parts.append(f"  - Unknown format: {str(conv)[:50]}")
        
        if context.habit_context:
            prompt_parts.append("\nUser's habits:")
            for habit_name, habit_data in context.habit_context.items():
                # Defensive programming: ensure habit_data is a dictionary
                if isinstance(habit_data, dict):
                    streak = habit_data.get('current_streak', 0)
                    completed_today = habit_data.get('completed_today', False)
                    prompt_parts.append(f"  - {habit_name}: {streak} day streak, {'completed' if completed_today else 'not completed'} today")
                else:
                    prompt_parts.append(f"  - {habit_name}: {str(habit_data)[:50]}")
        
        if context.people_context:
            prompt_parts.append("\nPeople mentioned:")
            for person_name, person_data in context.people_context.items():
                # Defensive programming: ensure person_data is a dictionary
                if isinstance(person_data, dict):
                    relationship = person_data.get('relationship', 'Unknown relationship')
                    prompt_parts.append(f"  - {person_name}: {relationship}")
                else:
                    prompt_parts.append(f"  - {person_name}: {str(person_data)[:50]}")
        
        if context.mood_patterns:
            # Defensive programming: ensure mood_patterns is a dictionary
            if isinstance(context.mood_patterns, dict):
                recent_mood = context.mood_patterns.get('recent_average', 'Unknown')
                prompt_parts.append(f"\nRecent mood: {recent_mood}")
            else:
                prompt_parts.append(f"\nRecent mood: {str(context.mood_patterns)[:50]}")
        
        if hasattr(context, 'similar_commitments') and context.similar_commitments:
            prompt_parts.append("\nUser's current commitments and tasks:")
            for commitment in context.similar_commitments[:5]:  # Show top 5 commitments
                if isinstance(commitment, dict):
                    task = commitment.get('task_description', 'Unknown task')
                    deadline_text = commitment.get('deadline_text', 'No deadline')
                    status = commitment.get('status', 'unknown')
                    prompt_parts.append(f"  - {task} ({deadline_text}, status: {status})")
        
        # User data if provided
        if user_data:
            if user_data.get('profile'):
                prompt_parts.append(f"\nUser profile: {user_data['profile'].get('name', 'Unknown')}")
        
        prompt_parts.append("\nPlease provide a structured JSON response following the StructuredAIResponse schema.")
        
        return "\n".join(prompt_parts)
    
    def _parse_structured_response(self, response_data: Dict[str, Any]) -> StructuredAIResponse:
        """Parse the LLM response into our structured format"""
        
        # Defensive check - ensure response_data is a dictionary
        if not isinstance(response_data, dict):
            logger.error(f"Expected dict, got {type(response_data)}: {response_data}")
            raise ValueError(f"Invalid response data type: {type(response_data)}")
        
        # Parse commitments
        commitments = []
        commitments_data = response_data.get('commitments', [])
        
        # Debug logging for commitment data
        if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
            debug_logger.debug(f"🔍 Raw commitments_data: {commitments_data}")
            debug_logger.debug(f"🔍 commitments_data type: {type(commitments_data)}")
            debug_logger.debug(f"🔍 commitments_data length: {len(commitments_data) if isinstance(commitments_data, list) else 'N/A'}")
            
        if not isinstance(commitments_data, list):
            logger.warning(f"Expected list for commitments, got {type(commitments_data)}")
            commitments_data = []
            
        for commit_data in commitments_data:
            if not isinstance(commit_data, dict):
                if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                    debug_logger.debug(f"🔍 Skipping non-dict commitment: {commit_data}")
                continue
                
            # Debug each commitment being processed
            if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                debug_logger.debug(f"🔍 Processing commitment: {commit_data.get('task_description', 'NO_TASK')}")
                
            # Parse deadline
            deadline = None
            if commit_data.get('deadline'):
                try:
                    deadline = datetime.fromisoformat(commit_data['deadline'].replace('Z', '+00:00'))
                except:
                    deadline = self._parse_fuzzy_deadline(commit_data.get('deadline', ''))
            
            # Parse reminder strategy - handle both string and object formats
            reminder_strategy_raw = commit_data.get('reminder_strategy', {})
            
            if isinstance(reminder_strategy_raw, str):
                # API returned string format like "1 day before"
                initial_reminder = self._parse_reminder_string(reminder_strategy_raw, deadline)
                follow_ups = []
                escalation = 'gentle'
                custom_message = None
            elif isinstance(reminder_strategy_raw, dict):
                # API returned object format
                reminder_data = reminder_strategy_raw
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
                
                escalation = reminder_data.get('escalation', 'gentle')
                custom_message = reminder_data.get('custom_message')
            else:
                # Fallback for unexpected format
                initial_reminder = deadline - timedelta(hours=1) if deadline else time_service.now() + timedelta(hours=1)
                follow_ups = []
                escalation = 'gentle'
                custom_message = None
            
            reminder_strategy = ReminderStrategy(
                initial_reminder=initial_reminder,
                follow_up_reminders=follow_ups,
                escalation=escalation,
                custom_message=custom_message
            )
            
            # Normalize deadline_type to valid values
            raw_deadline_type = commit_data.get('deadline_type', 'fuzzy')
            if raw_deadline_type not in ['specific', 'fuzzy', 'recurring']:
                # Map common invalid values to valid ones
                if raw_deadline_type in ['generic', 'flexible']:
                    deadline_type = 'fuzzy'
                elif raw_deadline_type in ['exact', 'fixed']:
                    deadline_type = 'specific'
                else:
                    deadline_type = 'fuzzy'  # default fallback
                    
                if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                    debug_logger.debug(f"🔍 Mapped invalid deadline_type '{raw_deadline_type}' to '{deadline_type}'")
            else:
                deadline_type = raw_deadline_type
            
            # Normalize priority to valid values
            raw_priority = commit_data.get('priority', 'medium')
            if raw_priority not in ['high', 'medium', 'low']:
                priority = 'medium'  # default fallback
                if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                    debug_logger.debug(f"🔍 Mapped invalid priority '{raw_priority}' to '{priority}'")
            else:
                priority = raw_priority

            try:
                commitment = ExtractedCommitment(
                    task_description=commit_data.get('task_description', ''),
                    deadline=deadline,
                    deadline_type=deadline_type,
                    priority=priority,
                    reminder_strategy=reminder_strategy,
                    related_people=commit_data.get('related_people', []),
                    related_habits=commit_data.get('related_habits', [])
                )
                commitments.append(commitment)
                
                # Debug the created commitment
                if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                    debug_logger.debug(f"🔍 Created commitment: {commitment.task_description} (deadline: {commitment.deadline})")
                    
            except Exception as commitment_error:
                logger.error(f"Error creating commitment from data {commit_data}: {commitment_error}")
                if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
                    debug_logger.debug(f"🔍 Failed to create commitment: {commitment_error}")
                continue  # Skip this commitment but continue with others
        
        # Parse habit actions
        habit_actions = []
        habit_actions_data = response_data.get('habit_actions', [])
        if not isinstance(habit_actions_data, list):
            logger.warning(f"Expected list for habit_actions, got {type(habit_actions_data)}")
            habit_actions_data = []
            
        for habit_data in habit_actions_data:
            if isinstance(habit_data, dict):
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
        people_updates_data = response_data.get('people_updates', [])
        if not isinstance(people_updates_data, list):
            logger.warning(f"Expected list for people_updates, got {type(people_updates_data)}")
            people_updates_data = []
            
        for person_data in people_updates_data:
            if isinstance(person_data, dict):
                update = AIPersonUpdate(
                    person_name=person_data.get('person_name', ''),
                    update_type=person_data.get('update_type', 'add_note'),
                    content=person_data.get('content', ''),
                    tags=person_data.get('tags', [])
                )
                people_updates.append(update)
        
        # Parse user profile updates
        user_profile_updates = []
        user_profile_updates_data = response_data.get('user_profile_updates', [])
        if not isinstance(user_profile_updates_data, list):
            logger.warning(f"Expected list for user_profile_updates, got {type(user_profile_updates_data)}")
            user_profile_updates_data = []
            
        for profile_data in user_profile_updates_data:
            if isinstance(profile_data, dict):
                from schemas.ai_responses import UserProfileUpdate as AIUserProfileUpdate
                update = AIUserProfileUpdate(
                    update_type=profile_data.get('update_type', 'add_info'),
                    content=profile_data.get('content', ''),
                    category=profile_data.get('category', 'general')
                )
                user_profile_updates.append(update)
        
        # Parse scheduled actions
        scheduled_actions = []
        scheduled_actions_data = response_data.get('scheduled_actions', [])
        if not isinstance(scheduled_actions_data, list):
            logger.warning(f"Expected list for scheduled_actions, got {type(scheduled_actions_data)}")
            scheduled_actions_data = []
            
        for sched_data in scheduled_actions_data:
            if not isinstance(sched_data, dict):
                continue
                
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
            
            # Normalize mood value to lowercase to match schema
            detected_mood = mood_data.get('detected_mood', 'neutral').lower()
            
            # Validate against allowed values and fallback if invalid
            valid_moods = ['very_positive', 'positive', 'neutral', 'negative', 'very_negative']
            if detected_mood not in valid_moods:
                logger.warning(f"Invalid mood value received: {detected_mood}, falling back to 'neutral'")
                detected_mood = 'neutral'
            
            mood_analysis = MoodAnalysis(
                detected_mood=detected_mood,
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
        
        final_response = StructuredAIResponse(
            message=response_data.get('message', 'I understand. Let me help you with that.'),
            commitments=commitments,
            habit_actions=habit_actions,
            people_updates=people_updates,
            user_profile_updates=user_profile_updates,
            scheduled_actions=scheduled_actions,
            mood_analysis=mood_analysis,
            response_metadata=metadata
        )
        
        # Final debug logging
        if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
            debug_logger.debug(f"🔍 Final StructuredAIResponse: {len(commitments)} commitments, {len(habit_actions)} habits")
            
        return final_response
    
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
    
    def _parse_reminder_string(self, reminder_str: str, deadline: Optional[datetime]) -> datetime:
        """Parse reminder strategy string like '1 day before' into datetime"""
        now = time_service.now()
        reminder_lower = reminder_str.lower()
        
        if not deadline:
            # If no deadline, set reminder for 1 hour from now
            return now + timedelta(hours=1)
        
        # Parse patterns like "X minutes/hours/days before"
        if 'minutes before' in reminder_lower:
            import re
            match = re.search(r'(\d+)\s*minutes?\s*before', reminder_lower)
            if match:
                minutes = int(match.group(1))
                return deadline - timedelta(minutes=minutes)
        
        if 'hours before' in reminder_lower:
            import re
            match = re.search(r'(\d+)\s*hours?\s*before', reminder_lower)
            if match:
                hours = int(match.group(1))
                return deadline - timedelta(hours=hours)
        
        if 'hour before' in reminder_lower:
            return deadline - timedelta(hours=1)
        
        if 'day before' in reminder_lower or 'days before' in reminder_lower:
            import re
            match = re.search(r'(\d+)\s*days?\s*before', reminder_lower)
            if match:
                days = int(match.group(1))
                return deadline - timedelta(days=days)
            else:
                # Default to 1 day before
                return deadline - timedelta(days=1)
        
        # Default fallback - 1 hour before deadline
        return deadline - timedelta(hours=1)
    
    def _create_fallback_response(self, message: str, raw_response: str) -> StructuredAIResponse:
        """Create a fallback response when JSON parsing fails"""
        # Clean the response of any system reminder tags
        import re
        conversational_response = re.sub(r'<system-reminder>.*?</system-reminder>', '', raw_response, flags=re.DOTALL)
        conversational_response = conversational_response.strip()
        
        # Try to extract just the message part if it looks like JSON
        json_like_match = re.search(r'"message"\s*:\s*"([^"]*)"', conversational_response)
        if json_like_match:
            conversational_response = json_like_match.group(1)
        elif conversational_response.startswith('{') and 'message' in conversational_response:
            # If it looks like JSON but we couldn't extract the message, provide a helpful default
            conversational_response = "I understand. Let me help you with that."
        
        # If after cleaning it's empty, provide a default response
        if not conversational_response:
            conversational_response = "I understand. Let me help you with that."
        
        return StructuredAIResponse(
            message=conversational_response,
            commitments=[],
            habit_actions=[],
            people_updates=[],
            user_profile_updates=[],
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
            user_profile_updates=[],
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
    
    def _is_valid_json(self, text: str) -> bool:
        """Check if text is valid JSON"""
        try:
            json.loads(text)
            return True
        except:
            return False
    
    def generate_session_name(self, messages: list) -> str:
        """Generate a session name based on the first few messages"""
        if not messages or len(messages) == 0:
            return "New Chat"
        
        # Combine first 3 message pairs (user + AI) or up to 500 chars
        conversation_text = ""
        char_count = 0
        
        for msg in messages[:6]:  # Up to 3 message pairs
            if hasattr(msg, 'message'):
                text = f"User: {msg.message}\n"
            elif hasattr(msg, 'response'):
                text = f"AI: {msg.response}\n"
            else:
                continue
                
            if char_count + len(text) > 500:
                break
            conversation_text += text
            char_count += len(text)
        
        if not conversation_text.strip():
            return "New Chat"
        
        prompt = f"""Based on this conversation, generate a short, descriptive title (2-5 words) that captures the main topic or purpose. The title should be clear and concise.

Conversation:
{conversation_text}

Respond with ONLY the title, no additional text or punctuation."""
        
        try:
            if not self.anthropic_client:
                # Fallback based on keywords in first message
                first_msg = messages[0]
                msg_text = ""
                if hasattr(first_msg, 'message'):
                    msg_text = first_msg.message.lower()
                elif hasattr(first_msg, 'response'):
                    msg_text = first_msg.response.lower()
                
                if 'habit' in msg_text:
                    return "Habit Discussion"
                elif 'commit' in msg_text or 'task' in msg_text:
                    return "Task Planning"
                elif 'mood' in msg_text or 'feel' in msg_text:
                    return "Mood Check-in"
                else:
                    return "General Chat"
            
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            
            title = response.content[0].text.strip()
            
            # Clean up the title
            title = title.replace('"', '').replace("'", "")
            if len(title) > 30:
                title = title[:27] + "..."
            
            return title if title else "New Chat"
            
        except Exception as e:
            logger.error(f"Failed to generate session name: {e}")
            return "New Chat"


# Global instance for easy importing
llm_processor = HybridLLMProcessor()