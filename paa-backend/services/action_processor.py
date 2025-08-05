"""
Action Processor for Hybrid Pipeline Architecture
Executes all structured actions from LLM responses.
"""

import asyncio
import logging
import os
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from schemas.ai_responses import (
    StructuredAIResponse, ExtractedCommitment, HabitAction,
    PersonUpdate as AIPersonUpdate, ScheduledAction, MoodAnalysis,
    ProcessingResult
)
from schemas import (
    CommitmentCreate, DailyCheckInCreate, PersonCreate, PersonUpdate,
    ProactiveMessageCreate
)
import database as models
from services.time_service import time_service
from services.habit_matcher import habit_matcher
from debug_logger import debug_logger

logger = logging.getLogger(__name__)


class ActionProcessor:
    """Execute all structured actions from LLM response"""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
    
    async def process_response(
        self,
        response: StructuredAIResponse,
        user_id: int
    ) -> ProcessingResult:
        """
        Process all actions from a structured AI response.
        
        Args:
            response: The structured response from the LLM
            user_id: The user ID for scoping
            
        Returns:
            ProcessingResult with outcomes and errors
        """
        results = ProcessingResult()
        
        # Debug logging - start
        if os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true":
            debug_logger.log_action_processing_start(
                commitments_count=len(response.commitments),
                habit_actions_count=len(response.habit_actions),
                people_updates_count=len(response.people_updates),
                user_profile_updates_count=len(response.user_profile_updates),
                scheduled_actions_count=len(response.scheduled_actions)
            )
            debug_logger.info(f"🎯 Action Processor: Processing {len(response.commitments)} commitments for user {user_id}")
            for i, commitment in enumerate(response.commitments):
                debug_logger.info(f"  📋 Commitment {i+1}: {commitment.task_description}")
        
        # Get database session
        db = self.db_session_factory()
        executed_actions = {"commitments": 0, "habit_actions": 0, "people_updates": 0, "user_profile_updates": 0, "scheduled_actions": 0}
        failed_actions = {"commitments": 0, "habit_actions": 0, "people_updates": 0, "user_profile_updates": 0, "scheduled_actions": 0}
        database_changes = {}
        
        try:
            # Process in parallel where possible
            tasks = []
            
            # 1. Handle commitments
            for commitment in response.commitments:
                tasks.append(self._create_commitment(commitment, user_id, db))
            
            # 2. Handle habit actions  
            for habit_action in response.habit_actions:
                tasks.append(self._process_habit_action(habit_action, user_id, db))
            
            # 3. Handle people updates
            for person_update in response.people_updates:
                tasks.append(self._update_person(person_update, user_id, db))
            
            # 4. Handle user profile updates
            for profile_update in response.user_profile_updates:
                tasks.append(self._update_user_profile(profile_update, user_id, db))
            
            # 5. Process mood if detected
            if response.mood_analysis:
                tasks.append(self._process_mood(response.mood_analysis, user_id, db))
            
            # Execute database tasks sequentially (to avoid conflicts)
            for task in tasks:
                try:
                    result = await task
                    results.outcomes.append(result)
                    
                    # Track successful actions for debug logging
                    action_type = result.get('action_type', 'unknown')
                    if result.get('success', False):
                        if action_type in executed_actions:
                            executed_actions[action_type] += 1
                        else:
                            executed_actions[action_type] = 1
                        
                        # Track database changes
                        db_action = result.get('db_action', 'unknown')
                        if db_action in database_changes:
                            database_changes[db_action] += 1
                        else:
                            database_changes[db_action] = 1
                    else:
                        if action_type in failed_actions:
                            failed_actions[action_type] += 1
                        else:
                            failed_actions[action_type] = 1
                            
                except Exception as e:
                    error_msg = f"Error processing action: {str(e)}"
                    logger.error(error_msg)
                    results.errors.append(error_msg)
                    results.outcomes.append({
                        'success': False,
                        'error': error_msg,
                        'user_visible': False
                    })
                    failed_actions['unknown'] = failed_actions.get('unknown', 0) + 1
            
            # 6. Schedule proactive messages (separate transaction)
            for scheduled in response.scheduled_actions:
                try:
                    result = await self._schedule_action(scheduled, user_id, db)
                    results.outcomes.append(result)
                    
                    if result.get('success', False):
                        executed_actions['scheduled_actions'] += 1
                        database_changes['scheduled_messages'] = database_changes.get('scheduled_messages', 0) + 1
                    else:
                        failed_actions['scheduled_actions'] += 1
                        
                except Exception as e:
                    error_msg = f"Error scheduling action: {str(e)}"
                    logger.error(error_msg)
                    results.errors.append(error_msg)
                    failed_actions['scheduled_actions'] += 1
            
            # Commit all changes
            db.commit()
            
        except Exception as e:
            logger.error(f"Error in action processing: {e}")
            db.rollback()
            results.errors.append(f"Transaction error: {str(e)}")
        finally:
            db.close()
        
        # Debug logging - result
        if os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true":
            debug_logger.log_action_processing_result(
                executed_actions=executed_actions,
                failed_actions=failed_actions,
                database_changes=database_changes
            )
        
        return results
    
    def _is_content_duplicate(self, existing_description: str, new_content: str) -> bool:
        """Check if new content already exists in the description"""
        if not existing_description:
            return False
            
        # Normalize both strings for comparison
        # Remove extra whitespace and convert to lowercase
        normalized_existing = ' '.join(existing_description.lower().split())
        normalized_new = ' '.join(new_content.lower().split())
        
        # Check if the new content is already in the existing description
        return normalized_new in normalized_existing
    
    async def _create_commitment(
        self,
        commitment: ExtractedCommitment,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Create a commitment in the database"""
        try:
            # Create the commitment with unified system fields
            db_commitment = models.Commitment(
                user_id=user_id,
                task_description=commitment.task_description,
                deadline=commitment.deadline.date() if commitment.deadline else None,
                status="active" if commitment.recurrence_pattern != "none" else "pending",
                original_message=f"Auto-extracted commitment",
                reminder_count=0,
                created_at=time_service.now(),
                # New unified system fields
                recurrence_pattern=commitment.recurrence_pattern,
                recurrence_interval=1,
                recurrence_days=','.join(commitment.recurrence_days) if commitment.recurrence_days else None,
                due_time=commitment.due_time,
                completion_count=0
            )
            
            db.add(db_commitment)
            db.flush()  # Get the ID
            
            # Schedule reminders if needed
            reminder_count = 0
            if commitment.reminder_strategy.initial_reminder:
                reminder_count += 1
                self._create_proactive_message(
                    db,
                    user_id,
                    "commitment_reminder",
                    commitment.reminder_strategy.custom_message or 
                    f"Reminder: {commitment.task_description}",
                    db_commitment.id,
                    commitment.reminder_strategy.initial_reminder
                )
            
            for follow_up in commitment.reminder_strategy.follow_up_reminders:
                reminder_count += 1
                self._create_proactive_message(
                    db,
                    user_id,
                    "commitment_reminder",
                    f"Follow-up: {commitment.task_description}",
                    db_commitment.id,
                    follow_up
                )
            
            return {
                'success': True,
                'type': 'commitment_created',
                'description': f"Created commitment: {commitment.task_description}",
                'data': {
                    'commitment_id': db_commitment.id,
                    'task': commitment.task_description,
                    'deadline': commitment.deadline.isoformat() if commitment.deadline else None,
                    'reminders_scheduled': reminder_count
                },
                'user_visible': True
            }
            
        except Exception as e:
            logger.error(f"Error creating commitment: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': 'commitment_creation_failed',
                'user_visible': False
            }
    
    async def _process_habit_action(
        self,
        habit_action: HabitAction,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Process a habit-related action - now converted to commitment actions in unified system"""
        try:
            if habit_action.action_type == 'log_completion':
                return await self._log_commitment_completion(habit_action, user_id, db)
            elif habit_action.action_type == 'create_new':
                return await self._create_new_recurring_commitment(habit_action, user_id, db)
            elif habit_action.action_type == 'update_schedule':
                return await self._update_commitment_schedule(habit_action, user_id, db)
            else:
                return {
                    'success': False,
                    'error': f"Unknown habit action type: {habit_action.action_type}",
                    'user_visible': False
                }
        except Exception as e:
            logger.error(f"Error processing habit action: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': 'habit_action_failed',
                'user_visible': False
            }
    
    async def _log_commitment_completion(
        self,
        habit_action: HabitAction,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Log a commitment completion (formerly habit completion) in unified system"""
        # Find existing recurring commitment
        commitment = db.query(models.Commitment).filter(
            models.Commitment.user_id == user_id,
            models.Commitment.task_description.ilike(f"%{habit_action.habit_identifier}%"),
            models.Commitment.recurrence_pattern != "none",
            models.Commitment.status == "active"
        ).first()
        
        if commitment:
            debug_logger.info(f"🔍 Found similar recurring commitment: '{habit_action.habit_identifier}' -> '{commitment.task_description}' (ID: {commitment.id})")
        
        was_auto_created = False
        if not commitment:
            # Auto-create as recurring commitment if it doesn't exist
            try:
                suggested_name = habit_action.habit_identifier.strip()
                
                debug_logger.info(f"🔧 Auto-creating missing recurring commitment: '{habit_action.habit_identifier}' -> '{suggested_name}'")
                was_auto_created = True
                
                commitment = models.Commitment(
                    user_id=user_id,
                    task_description=suggested_name,
                    recurrence_pattern='daily',  # default assumption for habits
                    recurrence_interval=1,
                    status='active',
                    completion_count=0,
                    created_at=time_service.now(),
                    original_message="Auto-created from habit tracking"
                )
                
                db.add(commitment)
                db.flush()  # Get the ID for logging
                
                debug_logger.info(f"✅ Auto-created recurring commitment: {commitment.task_description} (ID: {commitment.id})")
                
            except Exception as create_error:
                debug_logger.error(f"❌ Failed to auto-create recurring commitment: {create_error}")
                return {
                    'success': False,
                    'error': f"Failed to create recurring commitment '{habit_action.habit_identifier}': {str(create_error)}",
                    'user_visible': True,
                    'type': 'commitment_creation_failed'
                }
        
        # Check if already completed today
        completion_date = habit_action.completion_date or date.today()
        existing_completion = db.query(models.CommitmentCompletion).filter(
            models.CommitmentCompletion.commitment_id == commitment.id,
            models.CommitmentCompletion.completion_date == completion_date
        ).first()
        
        if existing_completion:
            return {
                'success': True,
                'type': 'commitment_already_completed',
                'description': f"'{commitment.task_description}' was already marked complete for {completion_date}",
                'user_visible': True
            }
        
        # Create completion record
        completion_record = models.CommitmentCompletion(
            commitment_id=commitment.id,
            user_id=user_id,
            completion_date=completion_date,
            completed_at=time_service.now(),
            notes=habit_action.notes,
            skipped=False
        )
        
        db.add(completion_record)
        
        # Update commitment stats
        commitment.completion_count += 1
        commitment.last_completed_at = time_service.now()
        
        # Create description based on whether commitment was auto-created
        if was_auto_created:
            description = f"Created and logged completion of new recurring commitment '{commitment.task_description}'"
        else:
            description = f"Logged completion of '{commitment.task_description}'"
        
        return {
            'success': True,
            'type': 'commitment_completed',
            'description': description,
            'data': {
                'commitment_id': commitment.id,
                'task_description': commitment.task_description,
                'completion_date': completion_date.isoformat(),
                'notes': habit_action.notes,
                'was_auto_created': was_auto_created,
                'is_recurring': True
            },
            'user_visible': True
        }
    
    async def _create_new_recurring_commitment(
        self,
        habit_action: HabitAction,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Create a new recurring commitment (formerly habit creation)"""
        if not habit_action.new_habit_details:
            return {
                'success': False,
                'error': "No details provided for new recurring commitment creation",
                'user_visible': False
            }
        
        details = habit_action.new_habit_details
        commitment_name = details.get('name', habit_action.habit_identifier)
        
        # Check if recurring commitment already exists
        existing = db.query(models.Commitment).filter(
            models.Commitment.user_id == user_id,
            models.Commitment.task_description.ilike(commitment_name),
            models.Commitment.recurrence_pattern != "none",
            models.Commitment.status == "active"
        ).first()
        
        if existing:
            return {
                'success': False,
                'error': f"Recurring commitment '{commitment_name}' already exists",
                'user_visible': True,
                'description': f"You already have a recurring commitment called '{commitment_name}'"
            }
        
        # Create new recurring commitment
        recurrence_pattern = details.get('frequency', 'daily')
        if recurrence_pattern not in ['daily', 'weekly', 'monthly']:
            recurrence_pattern = 'daily'  # fallback
        
        new_commitment = models.Commitment(
            user_id=user_id,
            task_description=commitment_name,
            recurrence_pattern=recurrence_pattern,
            recurrence_interval=1,
            due_time=details.get('reminder_time'),
            status='active',
            completion_count=0,
            created_at=time_service.now(),
            original_message="Created via AI interaction"
        )
        
        db.add(new_commitment)
        
        return {
            'success': True,
            'type': 'recurring_commitment_created',
            'description': f"Created new recurring commitment: {commitment_name}",
            'data': {
                'task_description': commitment_name,
                'recurrence_pattern': recurrence_pattern,
                'is_recurring': True
            },
            'user_visible': True
        }
    
    async def _update_commitment_schedule(
        self,
        habit_action: HabitAction,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Update recurring commitment schedule/settings (formerly habit update)"""
        # Find the recurring commitment
        commitment = db.query(models.Commitment).filter(
            models.Commitment.user_id == user_id,
            models.Commitment.task_description.ilike(f"%{habit_action.habit_identifier}%"),
            models.Commitment.recurrence_pattern != "none",
            models.Commitment.status == "active"
        ).first()
        
        if not commitment:
            return {
                'success': False,
                'error': f"Recurring commitment '{habit_action.habit_identifier}' not found",
                'user_visible': True
            }
        
        # Update commitment details
        updated_fields = []
        details = habit_action.details
        
        if 'frequency' in details:
            frequency = details['frequency']
            if frequency in ['daily', 'weekly', 'monthly']:
                commitment.recurrence_pattern = frequency
                updated_fields.append('frequency')
        
        if 'reminder_time' in details:
            commitment.due_time = details['reminder_time']
            updated_fields.append('reminder time')
        
        return {
            'success': True,
            'type': 'recurring_commitment_updated',
            'description': f"Updated {commitment.task_description}: {', '.join(updated_fields)}",
            'user_visible': True
        }
    
    async def _update_user_profile(
        self,
        profile_update: Any,  # Will be AIUserProfileUpdate
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Update the user's own profile information"""
        try:
            # Get or create user profile
            profile = db.query(models.UserProfile).filter(
                models.UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                # Create profile if it doesn't exist
                profile = models.UserProfile(
                    user_id=user_id,
                    display_name="",
                    description="",
                    created_at=time_service.now(),
                    updated_at=time_service.now()
                )
                db.add(profile)
                db.flush()
            
            # Apply the update based on type
            if profile_update.update_type == 'update_info':
                # Replace existing content
                profile.description = profile_update.content
            elif profile_update.update_type == 'add_info' or profile_update.update_type == 'append_info':
                # Check if content already exists before appending
                if not self._is_content_duplicate(profile.description or "", profile_update.content):
                    # Append to existing content
                    if profile.description:
                        # Add new info on a new paragraph
                        profile.description += f"\n\n{profile_update.content}"
                    else:
                        profile.description = profile_update.content
                else:
                    debug_logger.info(f"ℹ️ Skipping duplicate profile update: {profile_update.content[:50]}...")
                    return {
                        'success': True,
                        'type': 'user_profile_duplicate_skipped',
                        'description': f"Information already in your profile: {profile_update.content[:50]}...",
                        'user_visible': True,
                        'action_type': 'user_profile_updates',
                        'db_action': 'skipped_duplicate'
                    }
            
            profile.updated_at = time_service.now()
            
            debug_logger.info(f"✅ Updated user profile: {profile_update.update_type} - {profile_update.content[:50]}...")
            
            return {
                'success': True,
                'type': 'user_profile_updated',
                'description': f"Updated your profile with: {profile_update.content[:50]}...",
                'user_visible': True,
                'action_type': 'user_profile_updates',
                'db_action': 'profile_updated'
            }
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': 'user_profile_update_failed',
                'user_visible': False,
                'action_type': 'user_profile_updates'
            }
    
    async def _update_person(
        self,
        person_update: AIPersonUpdate,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Update or create person information"""
        try:
            # Find existing person
            person = db.query(models.Person).filter(
                models.Person.user_id == user_id,
                models.Person.name.ilike(f"%{person_update.person_name}%")
            ).first()
            
            if person_update.update_type == 'create_new' or not person:
                # Create new person
                person = models.Person(
                    user_id=user_id,
                    name=person_update.person_name,
                    description=person_update.content,
                    created_at=time_service.now(),
                    updated_at=time_service.now()
                )
                db.add(person)
                
                return {
                    'success': True,
                    'type': 'person_created',
                    'description': f"Created profile for {person_update.person_name}",
                    'user_visible': True
                }
            
            elif person_update.update_type == 'add_note':
                # Check if content already exists before adding note
                if not self._is_content_duplicate(person.description or "", person_update.content):
                    # Add note to existing description
                    if person.description:
                        person.description += f"\n\n{person_update.content}"
                    else:
                        person.description = person_update.content
                    person.updated_at = time_service.now()
                    
                    return {
                        'success': True,
                        'type': 'person_note_added',
                        'description': f"Added note about {person_update.person_name}",
                        'user_visible': True,
                        'action_type': 'people_updates',
                        'db_action': 'note_added'
                    }
                else:
                    debug_logger.info(f"ℹ️ Skipping duplicate note for {person_update.person_name}: {person_update.content[:50]}...")
                    return {
                        'success': True,
                        'type': 'person_note_duplicate_skipped',
                        'description': f"Note already exists for {person_update.person_name}: {person_update.content[:50]}...",
                        'user_visible': True,
                        'action_type': 'people_updates',
                        'db_action': 'skipped_duplicate'
                    }
            
            elif person_update.update_type == 'update_info':
                # Update person info
                person.description = person_update.content
                person.updated_at = time_service.now()
                
                return {
                    'success': True,
                    'type': 'person_updated',
                    'description': f"Updated info for {person_update.person_name}",
                    'user_visible': True
                }
            
        except Exception as e:
            logger.error(f"Error updating person: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': 'person_update_failed',
                'user_visible': False
            }
    
    async def _process_mood(
        self,
        mood_analysis: MoodAnalysis,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Process mood analysis and create check-in if appropriate"""
        try:
            # Convert mood to numeric scale
            mood_scale = {
                'very_negative': 1,
                'negative': 2,
                'neutral': 3,
                'positive': 4,
                'very_positive': 5
            }
            
            mood_score = mood_scale.get(mood_analysis.detected_mood, 3)
            
            # Check if user already has a check-in today
            today = time_service.now().date()
            existing_checkin = db.query(models.DailyCheckIn).filter(
                models.DailyCheckIn.user_id == user_id,
                func.date(models.DailyCheckIn.timestamp) == today
            ).first()
            
            if existing_checkin:
                # Update existing check-in
                existing_checkin.mood = mood_score
                existing_checkin.notes = f"Updated via chat - {', '.join(mood_analysis.contributing_factors)}"
                
                return {
                    'success': True,
                    'type': 'mood_updated',
                    'description': f"Updated today's mood to {mood_analysis.detected_mood}",
                    'user_visible': True
                }
            else:
                # Create new check-in
                checkin = models.DailyCheckIn(
                    user_id=user_id,
                    mood=mood_score,
                    notes=f"Detected via chat - {', '.join(mood_analysis.contributing_factors)}",
                    timestamp=time_service.now()
                )
                db.add(checkin)
                
                return {
                    'success': True,
                    'type': 'mood_recorded',
                    'description': f"Recorded mood: {mood_analysis.detected_mood}",
                    'data': {
                        'mood_score': mood_score,
                        'factors': mood_analysis.contributing_factors
                    },
                    'user_visible': True
                }
        
        except Exception as e:
            logger.error(f"Error processing mood: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': 'mood_processing_failed',
                'user_visible': False
            }
    
    async def _schedule_action(
        self,
        scheduled: ScheduledAction,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Schedule a proactive action"""
        try:
            self._create_proactive_message(
                db,
                user_id,
                "scheduled_prompt",
                scheduled.message_content,
                None,
                scheduled.send_time
            )
            
            return {
                'success': True,
                'type': 'action_scheduled',
                'description': f"Scheduled follow-up for {scheduled.send_time.strftime('%Y-%m-%d %H:%M')}",
                'user_visible': True
            }
        
        except Exception as e:
            logger.error(f"Error scheduling action: {e}")
            return {
                'success': False,
                'error': str(e),
                'type': 'scheduling_failed',
                'user_visible': False
            }
    
    def _create_proactive_message(
        self,
        db: Session,
        user_id: int,
        message_type: str,
        content: str,
        related_commitment_id: Optional[int],
        scheduled_for: datetime
    ):
        """Helper to create proactive messages"""
        # Get the most recent active session for this user
        # First try to get session with messages (last_message_at not null)
        session = db.query(models.ChatSession).filter(
            models.ChatSession.user_id == user_id,
            models.ChatSession.is_active == True,
            models.ChatSession.last_message_at.isnot(None)
        ).order_by(models.ChatSession.last_message_at.desc()).first()
        
        # If no session with messages, get the most recent created session
        if not session:
            session = db.query(models.ChatSession).filter(
                models.ChatSession.user_id == user_id,
                models.ChatSession.is_active == True
            ).order_by(models.ChatSession.created_at.desc()).first()
        
        session_id = session.id if session else None
        
        message = models.ProactiveMessage(
            user_id=user_id,
            message_type=message_type,
            content=content,
            related_commitment_id=related_commitment_id,
            session_id=session_id,
            scheduled_for=scheduled_for,
            user_responded=False
        )
        db.add(message)


# Function to create action processor instance
def create_action_processor(db_session_factory):
    """Factory function to create ActionProcessor with dependencies"""
    return ActionProcessor(db_session_factory)