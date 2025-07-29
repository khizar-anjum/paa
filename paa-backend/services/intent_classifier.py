"""
Intent Classification Service for Hybrid Pipeline Architecture
Analyzes user messages to determine intent and extract entities.
"""

import re
from typing import Dict, List, Optional
from schemas.ai_responses import MessageIntent


class IntentClassifier:
    """
    Classifies user messages into intents and extracts entities.
    Uses pattern matching for speed and reliability.
    """
    
    def __init__(self):
        # Intent patterns
        self.habit_patterns = [
            r"(worked out|exercised|meditated|studied|practiced|completed|finished|did)\s*(today|this morning|just now)?",
            r"I\s*(just|already)?\s*(went|did|completed|finished)",
            r"(✓|✅|done|completed)\s*(\w+)",
        ]
        
        self.commitment_patterns = [
            r"I'll\s+(.+?)\s+(today|tomorrow|later|this\s+\w+|by\s+\w+)",
            r"I\s*(need|have|want|should|must)\s+to\s+(.+?)\s+(today|tomorrow|later|this\s+\w+|by\s+\w+)",
            r"(remind me|don't let me forget)\s+to\s+(.+)",
            r"I\s*(promise|commit)\s+to\s+(.+)",
        ]
        
        self.social_patterns = [
            r"(\w+)\s+(said|mentioned|told me|recommended|suggested)",
            r"(talked|spoke|met|saw|hung out with)\s+(\w+)",
            r"(\w+)\s+and\s+I\s+(discussed|talked about)",
        ]
        
        self.mood_patterns = [
            r"(feeling|feel|I'm|I am)\s+(stressed|anxious|happy|sad|tired|excited|overwhelmed|great|good|bad)",
            r"(stressed|anxious|worried|concerned)\s+about",
            r"(excited|happy|thrilled)\s+(about|for)",
            r"(my mood|emotionally|mentally)",
        ]
        
        self.query_patterns = [
            r"(how many|how often|when did|what time|show me|tell me about)",
            r"(did I|have I|was I|were I)",
            r"(statistics|stats|progress|summary|overview)",
            r"(\\?|what|when|where|how|why)$",
        ]
        
        # Entity extraction patterns
        self.people_patterns = [
            r"(mom|dad|mother|father|brother|sister|wife|husband|partner|spouse|son|daughter)",
            r"(boss|manager|colleague|coworker|friend|teammate|roommate|neighbor)",
            r"(doctor|dentist|therapist|teacher|professor|coach)",
            r"([A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?",  # Capitalized names
            r"(my\s+)?(boss|manager|friend|partner|wife|husband|mom|dad)",  # With possessive
        ]
        
        self.time_patterns = [
            r"(today|tomorrow|yesterday)",
            r"(this|next|last)\s+(week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(morning|afternoon|evening|night)",
            r"(by|before|after|at|on)\s+(\d+|\w+)",
            r"(\d{1,2}:\d{2}|\d{1,2}\s*[ap]m)",
        ]
        
        self.emotion_patterns = [
            r"(happy|sad|angry|frustrated|excited|anxious|stressed|worried|calm|peaceful|tired|energetic)",
            r"(great|good|bad|terrible|amazing|awful|okay|fine)",
            r"(overwhelmed|confident|nervous|relaxed)",
        ]
    
    def classify(self, message: str) -> MessageIntent:
        """
        Classify a user message into intent and extract entities.
        
        Args:
            message: The user's message text
            
        Returns:
            MessageIntent object with classification results
        """
        message_lower = message.lower()
        
        # Determine primary intent
        primary_intent = self._determine_primary_intent(message_lower)
        
        # Extract secondary intents
        secondary_intents = self._extract_secondary_intents(message_lower, primary_intent)
        
        # Extract entities
        entities = self._extract_entities(message)
        
        # Determine context needed
        context_needed = self._determine_context_needed(primary_intent, entities)
        
        # Determine urgency
        urgency = self._determine_urgency(message_lower, primary_intent)
        
        # Calculate confidence
        confidence = self._calculate_confidence(message_lower, primary_intent)
        
        return MessageIntent(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            entities=entities,
            context_needed=context_needed,
            urgency=urgency,
            confidence=confidence
        )
    
    def _determine_primary_intent(self, message: str) -> str:
        """Determine the primary intent of the message."""
        # Count pattern matches for each intent
        scores = {
            'habit_tracking': sum(1 for p in self.habit_patterns if re.search(p, message, re.IGNORECASE)),
            'commitment_making': sum(1 for p in self.commitment_patterns if re.search(p, message, re.IGNORECASE)),
            'social_reference': sum(1 for p in self.social_patterns if re.search(p, message, re.IGNORECASE)),
            'mood_reflection': sum(1 for p in self.mood_patterns if re.search(p, message, re.IGNORECASE)),
            'information_query': sum(1 for p in self.query_patterns if re.search(p, message, re.IGNORECASE)),
        }
        
        # Check for explicit indicators
        if '?' in message:
            scores['information_query'] += 2
        
        if any(word in message for word in ['remind', 'tomorrow', "i'll", "i will"]):
            scores['commitment_making'] += 1
        
        if any(word in message for word in ['feel', 'feeling', 'mood', 'stressed', 'anxious', 'happy']):
            scores['mood_reflection'] += 1
        
        # Get the intent with highest score
        max_score = max(scores.values())
        if max_score == 0:
            return 'general_chat'
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _extract_secondary_intents(self, message: str, primary_intent: str) -> List[str]:
        """Extract any secondary intents from the message."""
        secondary = []
        
        # Check for combinations
        if primary_intent == 'mood_reflection':
            if any(p for p in self.commitment_patterns if re.search(p, message, re.IGNORECASE)):
                secondary.append('commitment_making')
        
        if primary_intent == 'habit_tracking':
            if any(p for p in self.mood_patterns if re.search(p, message, re.IGNORECASE)):
                secondary.append('mood_reflection')
        
        if primary_intent != 'social_reference':
            if any(p for p in self.social_patterns if re.search(p, message, re.IGNORECASE)):
                secondary.append('social_reference')
        
        return secondary
    
    def _extract_entities(self, message: str) -> Dict[str, List[str]]:
        """Extract entities from the message."""
        entities = {
            'people': [],
            'habits': [],
            'time_references': [],
            'emotions': [],
            'actions': []
        }
        
        # Extract people
        for pattern in self.people_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                person = match.group(0).strip()
                if len(person) > 1 and person not in entities['people']:
                    entities['people'].append(person)
        
        # Extract time references
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                time_ref = match.group(0).strip()
                if time_ref not in entities['time_references']:
                    entities['time_references'].append(time_ref)
        
        # Extract emotions
        for pattern in self.emotion_patterns:
            matches = re.finditer(pattern, message, re.IGNORECASE)
            for match in matches:
                emotion = match.group(0).strip()
                if emotion not in entities['emotions']:
                    entities['emotions'].append(emotion)
        
        # Extract habits (comprehensive list)
        habit_keywords = [
            'workout', 'exercise', 'meditate', 'meditation', 'study', 'read', 'reading',
            'journal', 'journaling', 'walk', 'walking', 'run', 'running', 'yoga',
            'practice', 'code', 'coding', 'work', 'sleep', 'water', 'hydrate',
            'stretch', 'stretching', 'bike', 'biking', 'swim', 'swimming',
            'pray', 'prayer', 'learn', 'learning', 'clean', 'cleaning',
            'cook', 'cooking', 'diet', 'eat', 'eating', 'fast', 'fasting'
        ]
        
        # Look for exact matches and partial matches
        message_words = message.lower().split()
        for habit in habit_keywords:
            if habit in message.lower():
                entities['habits'].append(habit)
        
        # Also check for gerund forms and past tense
        for word in message_words:
            if word.endswith('ing') and len(word) > 4:  # potential gerund
                base_word = word[:-3]  # remove 'ing'
                if base_word in habit_keywords and word not in entities['habits']:
                    entities['habits'].append(word)
            elif word.endswith('ed') and len(word) > 4:  # potential past tense
                base_word = word[:-2]  # remove 'ed'
                if base_word in habit_keywords and word not in entities['habits']:
                    entities['habits'].append(word)
        
        # Extract actions (comprehensive list)
        action_verbs = [
            'call', 'email', 'text', 'message', 'meet', 'finish', 'complete', 'submit',
            'prepare', 'review', 'send', 'write', 'create', 'fix', 'update', 'buy',
            'purchase', 'book', 'schedule', 'cancel', 'reschedule', 'visit', 'go',
            'attend', 'join', 'start', 'begin', 'stop', 'quit', 'pause', 'resume',
            'plan', 'organize', 'clean', 'wash', 'cook', 'make', 'build', 'repair',
            'discuss', 'talk', 'speak', 'listen', 'watch', 'read', 'study', 'learn'
        ]
        
        # Extract actions with context
        for verb in action_verbs:
            if verb in message.lower():
                entities['actions'].append(verb)
        
        # Look for action patterns like "I need to X", "I should X", etc.
        action_patterns = [
            r"I\s+(need|should|have|want|must|will|plan)\s+to\s+(\w+)",
            r"I'll\s+(\w+)",
            r"going\s+to\s+(\w+)",
            r"let\s+me\s+(\w+)"
        ]
        
        for pattern in action_patterns:
            matches = re.finditer(pattern, message.lower())
            for match in matches:
                action = match.group(-1)  # Get the last captured group (the action)
                if action not in entities['actions']:
                    entities['actions'].append(action)
        
        return entities
    
    def _determine_context_needed(self, primary_intent: str, entities: Dict[str, List[str]]) -> List[str]:
        """Determine what context is needed based on intent and entities."""
        context_needed = []
        
        if primary_intent == 'habit_tracking':
            context_needed.extend(['habit_history', 'recent_conversations'])
        
        elif primary_intent == 'commitment_making':
            context_needed.extend(['similar_commitments', 'temporal_context'])
            if entities['people']:
                context_needed.append('person_profile')
        
        elif primary_intent == 'social_reference':
            context_needed.extend(['person_profile', 'recent_conversations'])
        
        elif primary_intent == 'mood_reflection':
            context_needed.extend(['mood_trends', 'recent_conversations'])
        
        elif primary_intent == 'information_query':
            context_needed.extend(['habit_history', 'mood_trends', 'recent_conversations'])
        
        # Always include temporal context if time references exist
        if entities['time_references']:
            if 'temporal_context' not in context_needed:
                context_needed.append('temporal_context')
        
        return context_needed
    
    def _determine_urgency(self, message: str, primary_intent: str) -> str:
        """Determine the urgency level of the message."""
        # High urgency indicators
        high_urgency_words = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 
                             'important', 'deadline', 'today', 'now', 'stressed', 'anxious']
        
        # Low urgency indicators
        low_urgency_words = ['maybe', 'sometime', 'eventually', 'whenever', 'no rush', 
                           'when i can', 'if possible']
        
        high_count = sum(1 for word in high_urgency_words if word in message)
        low_count = sum(1 for word in low_urgency_words if word in message)
        
        if high_count > low_count:
            return 'immediate'
        elif low_count > 0:
            return 'low'
        else:
            return 'normal'
    
    def _calculate_confidence(self, message: str, primary_intent: str) -> float:
        """Calculate confidence score for the classification."""
        # Base confidence on pattern matches
        if primary_intent == 'general_chat':
            return 0.5  # Low confidence for general chat
        
        # Count relevant pattern matches
        pattern_count = 0
        if primary_intent == 'habit_tracking':
            pattern_count = sum(1 for p in self.habit_patterns if re.search(p, message, re.IGNORECASE))
        elif primary_intent == 'commitment_making':
            pattern_count = sum(1 for p in self.commitment_patterns if re.search(p, message, re.IGNORECASE))
        elif primary_intent == 'social_reference':
            pattern_count = sum(1 for p in self.social_patterns if re.search(p, message, re.IGNORECASE))
        elif primary_intent == 'mood_reflection':
            pattern_count = sum(1 for p in self.mood_patterns if re.search(p, message, re.IGNORECASE))
        elif primary_intent == 'information_query':
            pattern_count = sum(1 for p in self.query_patterns if re.search(p, message, re.IGNORECASE))
        
        # Calculate confidence based on pattern matches
        if pattern_count >= 3:
            return 0.95
        elif pattern_count >= 2:
            return 0.85
        elif pattern_count >= 1:
            return 0.75
        else:
            return 0.6


# Global instance for easy importing
intent_classifier = IntentClassifier()