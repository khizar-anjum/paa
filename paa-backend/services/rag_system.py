"""
Hybrid RAG System for Hybrid Pipeline Architecture
Combines semantic search with SQL queries for comprehensive context retrieval.
"""

import os
import time
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from schemas.ai_responses import MessageIntent, EnhancedContext
import database as models
from services.time_service import time_service
from services.vector_store import get_vector_store
from debug_logger import debug_logger


class HybridRAGSystem:
    """
    Intelligent context retrieval system that combines semantic search 
    with structured SQL queries for comprehensive context.
    """
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.vector_store = get_vector_store()
    
    def retrieve_context(
        self,
        message: str,
        intent: MessageIntent,
        user_id: int
    ) -> EnhancedContext:
        """
        Multi-strategy retrieval based on intent.
        
        Args:
            message: The user's message
            intent: Classified intent
            user_id: User ID for scoping
            
        Returns:
            EnhancedContext with relevant information
        """
        start_time = time.time()
        
        # Debug logging - start
        if os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true":
            debug_logger.log_rag_retrieval_start(intent, user_id)
        
        db = self.db_session_factory()
        context = EnhancedContext()
        context_sources = []
        retrieved_items = 0
        
        try:
            # 1. Semantic search across relevant collections (NEW)
            context.semantic_matches = self._get_semantic_matches(message, intent, user_id)
            
            # 2. Recent conversations (ENHANCED with semantic search)
            if 'recent_conversations' in intent.context_needed:
                context.conversations = self._get_enhanced_conversations(db, user_id, message)
                context_sources.append("conversations")
                retrieved_items += len(context.conversations)
            
            # 3. Person profiles (ENHANCED with semantic search)
            if 'person_profile' in intent.context_needed and intent.entities.get('people'):
                context.people_context = self._get_enhanced_people_context(db, user_id, intent.entities['people'], message)
                context_sources.append("people")
                retrieved_items += len(context.people_context)
            
            # 4. Habit context (ENHANCED with semantic search)
            if ('habit_history' in intent.context_needed or 
                intent.primary_intent == 'habit_tracking' or 
                intent.entities.get('habits')):
                context.habit_context = self._get_enhanced_habit_context(db, user_id, intent.entities.get('habits', []), message)
                context_sources.append("habits")
                retrieved_items += len(context.habit_context)
            
            # 5. Mood trends (existing)
            if 'mood_trends' in intent.context_needed or intent.primary_intent == 'mood_reflection':
                context.mood_patterns = self._get_mood_patterns(db, user_id)
                context_sources.append("mood_patterns")
                retrieved_items += len(context.mood_patterns)
            
            # 6. Similar commitments (ENHANCED with semantic search)
            if 'similar_commitments' in intent.context_needed or intent.primary_intent == 'commitment_making':
                context.similar_commitments = self._get_enhanced_similar_commitments(db, user_id, message)
                context_sources.append("commitments")
                retrieved_items += len(context.similar_commitments)
            
            # 7. Temporal context (existing)
            if 'temporal_context' in intent.context_needed and intent.entities.get('time_references'):
                context.temporal = self._get_temporal_context(db, user_id, intent.entities['time_references'])
                context_sources.append("temporal")
                retrieved_items += len(context.temporal)
        
        finally:
            db.close()
        
        # Debug logging - result
        if os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true":
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            similarity_scores = []
            
            # Extract similarity scores from semantic matches
            if hasattr(context, 'semantic_matches') and context.semantic_matches:
                similarity_scores = [match.get('similarity_score', 0) for match in context.semantic_matches]
            
            debug_logger.log_rag_retrieval_result(
                context_sources=context_sources,
                similarity_scores=similarity_scores,
                retrieved_items=retrieved_items,
                processing_time=processing_time
            )
        
        return context
    
    def _get_semantic_matches(self, message: str, intent: MessageIntent, user_id: int) -> List[Dict[str, Any]]:
        """Get semantic matches across all collections based on intent"""
        semantic_matches = []
        
        # Search conversations for semantic similarity
        if intent.primary_intent in ['general_chat', 'information_query', 'mood_reflection']:
            conv_matches = self.vector_store.search_conversations(message, user_id, limit=3)
            for match in conv_matches:
                if match['similarity_score'] > 0.7:  # High similarity threshold
                    semantic_matches.append({
                        'type': 'conversation',
                        'content': match['user_message'],
                        'response': match['ai_response'],
                        'similarity': match['similarity_score'],
                        'timestamp': match['timestamp']
                    })
        
        # Search habits if habit-related
        if intent.primary_intent == 'habit_tracking' or intent.entities.get('habits'):
            habit_matches = self.vector_store.search_habits(message, user_id, limit=2)
            for match in habit_matches:
                if match['similarity_score'] > 0.6:
                    semantic_matches.append({
                        'type': 'habit',
                        'name': match['name'],
                        'description': match['description'],
                        'similarity': match['similarity_score']
                    })
        
        # Search people if people mentioned
        if intent.entities.get('people'):
            people_matches = self.vector_store.search_people(message, user_id, limit=2)
            for match in people_matches:
                if match['similarity_score'] > 0.6:
                    semantic_matches.append({
                        'type': 'person',
                        'name': match['name'],
                        'relationship': match['relationship'],
                        'similarity': match['similarity_score']
                    })
        
        # Search commitments if commitment-related
        if intent.primary_intent == 'commitment_making':
            commitment_matches = self.vector_store.search_commitments(message, user_id, limit=2)
            for match in commitment_matches:
                if match['similarity_score'] > 0.6:
                    semantic_matches.append({
                        'type': 'commitment',
                        'task': match['task_description'],
                        'status': match['status'],
                        'priority': match['priority'],
                        'similarity': match['similarity_score']
                    })
        
        return semantic_matches
    
    def _get_enhanced_conversations(self, db: Session, user_id: int, message: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Enhanced conversation retrieval combining recent + semantic"""
        # Get recent conversations (SQL)
        recent_conversations = self._get_recent_conversations(db, user_id, limit=3)
        
        # Get semantically similar conversations (Vector)
        semantic_conversations = self.vector_store.search_conversations(message, user_id, limit=2)
        
        # Combine and deduplicate
        all_conversations = {}
        
        # Add recent conversations
        for conv in recent_conversations:
            all_conversations[conv['id']] = {
                **conv,
                'retrieval_method': 'recent',
                'similarity_score': None
            }
        
        # Add semantic matches if not already included
        for conv in semantic_conversations:
            conv_id = conv['conversation_id']
            if conv_id not in all_conversations and conv['similarity_score'] > 0.6:
                all_conversations[conv_id] = {
                    'id': conv_id,
                    'message': conv['user_message'],
                    'response': conv['ai_response'],
                    'timestamp': conv['timestamp'],
                    'retrieval_method': 'semantic',
                    'similarity_score': conv['similarity_score']
                }
        
        return list(all_conversations.values())[:limit]
    
    def _get_enhanced_people_context(
        self,
        db: Session,
        user_id: int,
        people_names: List[str],
        message: str
    ) -> Dict[str, Any]:
        """Enhanced people context with semantic search"""
        # Get exact matches first
        people_context = self._get_people_context(db, user_id, people_names)
        
        # Add semantic matches for people not found
        for name in people_names:
            if people_context.get(name, {}).get('status') == 'unknown':
                # Search for similar people
                semantic_matches = self.vector_store.search_people(f"{name} {message}", user_id, limit=1)
                if semantic_matches and semantic_matches[0]['similarity_score'] > 0.7:
                    match = semantic_matches[0]
                    people_context[name] = {
                        'status': 'similar_found',
                        'similar_person': match['name'],
                        'relationship': match['relationship'],
                        'similarity': match['similarity_score'],
                        'suggestion': 'might_be_referring_to'
                    }
        
        return people_context
    
    def _get_enhanced_habit_context(
        self,
        db: Session,
        user_id: int,
        mentioned_habits: List[str],
        message: str
    ) -> Dict[str, Any]:
        """Enhanced habit context with semantic search"""
        # Get all habit context first
        habit_context = self._get_habit_context(db, user_id, mentioned_habits)
        
        # Add semantic matches for additional relevant habits
        semantic_habits = self.vector_store.search_habits(message, user_id, limit=3)
        
        habit_context['semantic_matches'] = []
        for match in semantic_habits:
            if match['similarity_score'] > 0.6:
                habit_context['semantic_matches'].append({
                    'name': match['name'],
                    'description': match['description'],
                    'similarity': match['similarity_score']
                })
        
        return habit_context
    
    def _get_enhanced_similar_commitments(
        self,
        db: Session,
        user_id: int,
        message: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Enhanced commitment search using both SQL and vector search"""
        # Get SQL-based similar commitments
        sql_commitments = self._get_similar_commitments(db, user_id, message, limit=2)
        
        # Get vector-based similar commitments
        vector_commitments = self.vector_store.search_commitments(message, user_id, limit=2)
        
        # Combine and format
        all_commitments = {}
        
        # Add SQL matches
        for commitment in sql_commitments:
            all_commitments[commitment['id']] = {
                **commitment,
                'retrieval_method': 'keyword',
                'semantic_similarity': None
            }
        
        # Add vector matches
        for commitment in vector_commitments:
            commit_id = commitment['commitment_id']
            if commit_id not in all_commitments and commitment['similarity_score'] > 0.6:
                all_commitments[commit_id] = {
                    'id': commit_id,
                    'task_description': commitment['task_description'],
                    'status': commitment['status'],
                    'priority': commitment['priority'],
                    'deadline': commitment['deadline'],
                    'retrieval_method': 'semantic',
                    'semantic_similarity': commitment['similarity_score']
                }
        
        # Sort by relevance (semantic similarity or keyword overlap)
        sorted_commitments = sorted(
            all_commitments.values(),
            key=lambda x: x.get('semantic_similarity', x.get('similarity_score', 0)),
            reverse=True
        )
        
        return sorted_commitments[:limit]
    
    def _get_recent_conversations(self, db: Session, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        conversations = db.query(models.Conversation).filter(
            models.Conversation.user_id == user_id
        ).order_by(desc(models.Conversation.timestamp)).limit(limit).all()
        
        return [
            {
                'message': conv.message,
                'response': conv.response,
                'timestamp': conv.timestamp.isoformat(),
                'id': conv.id
            }
            for conv in conversations
        ]
    
    def _get_people_context(
        self,
        db: Session,
        user_id: int,
        people_names: List[str]
    ) -> Dict[str, Any]:
        """Get context about mentioned people"""
        people_context = {}
        
        for name in people_names:
            # Find person by name (case insensitive)
            person = db.query(models.Person).filter(
                models.Person.user_id == user_id,
                models.Person.name.ilike(f"%{name}%")
            ).first()
            
            if person:
                people_context[name] = {
                    'id': person.id,
                    'full_name': person.name,
                    'relationship': person.how_you_know_them,
                    'pronouns': person.pronouns,
                    'description': person.description,
                    'last_updated': person.updated_at.isoformat()
                }
            else:
                people_context[name] = {
                    'status': 'unknown',
                    'suggestion': 'create_profile'
                }
        
        return people_context
    
    def _get_habit_context(
        self,
        db: Session,
        user_id: int,
        mentioned_habits: List[str]
    ) -> Dict[str, Any]:
        """Get context about user's habits"""
        habit_context = {}
        
        # Get all active habits
        habits = db.query(models.Habit).filter(
            models.Habit.user_id == user_id,
            models.Habit.is_active == 1
        ).all()
        
        today = time_service.now().date()
        
        for habit in habits:
            # Check if completed today
            completed_today = db.query(models.HabitLog).filter(
                models.HabitLog.habit_id == habit.id,
                func.date(models.HabitLog.completed_at) == today
            ).first() is not None
            
            # Calculate current streak
            current_streak = self._calculate_habit_streak(db, habit.id)
            
            # Get recent completion rate
            week_ago = today - timedelta(days=7)
            recent_completions = db.query(models.HabitLog).filter(
                models.HabitLog.habit_id == habit.id,
                func.date(models.HabitLog.completed_at) >= week_ago
            ).count()
            
            habit_context[habit.name] = {
                'id': habit.id,
                'completed_today': completed_today,
                'current_streak': current_streak,
                'frequency': habit.frequency,
                'recent_completions': recent_completions,
                'reminder_time': habit.reminder_time,
                'created_at': habit.created_at.isoformat()
            }
        
        return habit_context
    
    def _get_mood_patterns(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get mood trends and patterns"""
        # Get recent mood data
        week_ago = time_service.now() - timedelta(days=7)
        recent_checkins = db.query(models.DailyCheckIn).filter(
            models.DailyCheckIn.user_id == user_id,
            models.DailyCheckIn.timestamp >= week_ago
        ).order_by(desc(models.DailyCheckIn.timestamp)).all()
        
        if not recent_checkins:
            return {'status': 'no_recent_data'}
        
        # Calculate average mood
        moods = [checkin.mood for checkin in recent_checkins]
        avg_mood = sum(moods) / len(moods)
        
        # Get today's mood if exists
        today = time_service.now().date()
        today_checkin = db.query(models.DailyCheckIn).filter(
            models.DailyCheckIn.user_id == user_id,
            func.date(models.DailyCheckIn.timestamp) == today
        ).first()
        
        # Convert mood numbers to labels
        mood_labels = {1: 'very_negative', 2: 'negative', 3: 'neutral', 4: 'positive', 5: 'very_positive'}
        
        return {
            'recent_average': round(avg_mood, 1),
            'recent_average_label': mood_labels.get(round(avg_mood), 'neutral'),
            'today_mood': today_checkin.mood if today_checkin else None,
            'today_mood_label': mood_labels.get(today_checkin.mood) if today_checkin else None,
            'trend_days': len(recent_checkins),
            'recent_entries': [
                {
                    'date': checkin.timestamp.date().isoformat(),
                    'mood': checkin.mood,
                    'mood_label': mood_labels.get(checkin.mood, 'neutral'),
                    'notes': checkin.notes
                }
                for checkin in recent_checkins[:5]  # Last 5 entries
            ]
        }
    
    def _get_similar_commitments(
        self,
        db: Session,
        user_id: int,
        message: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar past commitments (basic keyword matching)"""
        # Get recent commitments
        recent_commitments = db.query(models.Commitment).filter(
            models.Commitment.user_id == user_id
        ).order_by(desc(models.Commitment.created_at)).limit(20).all()
        
        # Simple keyword matching
        message_words = set(message.lower().split())
        similar_commitments = []
        
        for commitment in recent_commitments:
            commitment_words = set(commitment.task_description.lower().split())
            overlap = len(message_words.intersection(commitment_words))
            
            if overlap >= 2:  # At least 2 words in common
                similar_commitments.append({
                    'id': commitment.id,
                    'task_description': commitment.task_description,
                    'status': commitment.status,
                    'deadline': commitment.deadline.isoformat() if commitment.deadline else None,
                    'created_at': commitment.created_at.isoformat(),
                    'similarity_score': overlap
                })
        
        # Sort by similarity and return top matches
        similar_commitments.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_commitments[:limit]
    
    def _get_temporal_context(
        self,
        db: Session,
        user_id: int,
        time_references: List[str]
    ) -> Dict[str, Any]:
        """Get temporal context based on time references"""
        now = time_service.now()
        temporal_context = {
            'current_time': now.isoformat(),
            'day_of_week': now.strftime('%A'),
            'time_references_found': time_references
        }
        
        # Check for relevant deadlines
        upcoming_deadlines = db.query(models.Commitment).filter(
            models.Commitment.user_id == user_id,
            models.Commitment.status == 'pending',
            models.Commitment.deadline.isnot(None),
            models.Commitment.deadline >= now.date(),
            models.Commitment.deadline <= (now.date() + timedelta(days=7))
        ).order_by(models.Commitment.deadline).all()
        
        temporal_context['upcoming_deadlines'] = [
            {
                'task': commitment.task_description,
                'deadline': commitment.deadline.isoformat(),
                'days_until': (commitment.deadline - now.date()).days
            }
            for commitment in upcoming_deadlines
        ]
        
        return temporal_context
    
    def _calculate_habit_streak(self, db: Session, habit_id: int) -> int:
        """Calculate current streak for a habit"""
        # Get all completions for this habit, ordered by date
        completions = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit_id
        ).order_by(desc(models.HabitLog.completed_at)).all()
        
        if not completions:
            return 0
        
        # Calculate streak from most recent completion
        streak = 0
        current_date = time_service.now().date()
        
        # Convert completions to dates
        completion_dates = [comp.completed_at.date() for comp in completions]
        completion_dates = sorted(set(completion_dates), reverse=True)  # Remove duplicates and sort
        
        for date in completion_dates:
            expected_date = current_date - timedelta(days=streak)
            if date == expected_date:
                streak += 1
            else:
                break
        
        return streak


# Factory function to create RAG system
def create_rag_system(db_session_factory):
    """Factory function to create enhanced RAG system with dependencies"""
    return HybridRAGSystem(db_session_factory)