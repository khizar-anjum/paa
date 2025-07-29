"""
NLP-based Intent Classification Service using spaCy
More robust and accurate than regex-based approach.
"""

import spacy
from spacy.matcher import Matcher
from typing import Dict, List, Optional, Tuple
from schemas.ai_responses import MessageIntent
from debug_logger import debug_logger
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class NLPIntentClassifier:
    """
    Uses spaCy NLP for robust intent classification and entity extraction.
    Much more accurate than regex patterns.
    """
    
    def __init__(self):
        # Load English language model
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)
        
        # Define intent examples for semantic similarity
        self.intent_examples = {
            'habit_tracking': [
                "I worked out today",
                "I meditated this morning", 
                "I usually drink coffee every morning",
                "I always go for a walk after work",
                "I drink milk everyday",
                "I exercise regularly",
                "I have a daily routine of reading",
                "I typically eat breakfast at 8am",
                "I normally take vitamins",
                "I completed my morning workout"
            ],
            'commitment_making': [
                "I'll call mom tomorrow",
                "I need to finish the report by Friday",
                "Remind me to buy groceries",
                "I should exercise tomorrow",
                "I will meditate tonight",
                "I must complete this task",
                "I plan to visit the doctor",
                "I promise to clean the house"
            ],
            'mood_reflection': [
                "I'm feeling stressed about work",
                "I feel happy today",
                "I'm anxious about the meeting",
                "Feeling overwhelmed lately",
                "I'm in a good mood",
                "I feel tired and drained",
                "I'm excited about the weekend",
                "Feeling a bit down today"
            ],
            'social_reference': [
                "John mentioned a great book",
                "I talked to Sarah about the project",
                "My mom called me yesterday",
                "I met with my colleague",
                "My friend recommended this restaurant",
                "I discussed plans with my partner",
                "My boss asked me to finish this",
                "I spoke with the doctor"
            ],
            'information_query': [
                "How many times did I exercise this week?",
                "What's my meditation streak?",
                "Show me my progress",
                "When did I last call mom?",
                "How often do I work out?",
                "What are my habit statistics?",
                "Tell me about my mood trends",
                "Did I complete my goals yesterday?"
            ]
        }
        
        # Pre-compute embeddings for intent examples
        self.intent_embeddings = {}
        for intent, examples in self.intent_examples.items():
            embeddings = []
            for example in examples:
                doc = self.nlp(example)
                if doc.vector.any():  # Check if vector exists
                    embeddings.append(doc.vector)
            if embeddings:
                # Average embedding for this intent
                self.intent_embeddings[intent] = np.mean(embeddings, axis=0)
        
        # Setup spaCy patterns for better entity extraction
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup spaCy patterns for entity extraction"""
        
        # Habit patterns - looking for linguistic structures
        habit_patterns = [
            # "I usually/always/typically [VERB] [OBJECT] [FREQUENCY]"
            [{"LOWER": "i"}, {"LOWER": {"IN": ["usually", "always", "typically", "normally", "regularly", "often"]}}, 
             {"POS": "VERB"}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "*"}],
            
            # "drink/eat/take [OBJECT] everyday/daily"
            [{"LOWER": {"IN": ["drink", "eat", "take", "have"]}}, {"POS": {"IN": ["NOUN", "PROPN"]}, "OP": "+"}, 
             {"LOWER": {"IN": ["everyday", "daily", "regularly"]}}],
            
            # Past tense habit completion: "I [VERB]ed today/this morning"
            [{"LOWER": "i"}, {"TAG": "VBD"}, {"LOWER": {"IN": ["today", "yesterday", "this"]}, "OP": "?"}],
        ]
        
        # Time reference patterns
        time_patterns = [
            [{"LOWER": {"IN": ["today", "tomorrow", "yesterday"]}}],
            [{"LOWER": {"IN": ["this", "next", "last"]}}, {"LOWER": {"IN": ["week", "month", "year", "morning", "evening"]}}],
            [{"LOWER": {"IN": ["after", "before", "during"]}}, {"POS": "NOUN"}],
        ]
        
        # Add patterns to matcher
        self.matcher.add("HABIT_PATTERN", habit_patterns)
        self.matcher.add("TIME_PATTERN", time_patterns)
    
    def classify(self, message: str) -> MessageIntent:
        """
        Classify message using NLP approach.
        
        Args:
            message: The user's message text
            
        Returns:
            MessageIntent with accurate classification
        """
        doc = self.nlp(message)
        
        # 1. Determine primary intent using semantic similarity
        primary_intent, confidence = self._classify_intent_semantic(doc)
        
        # 2. Extract entities using spaCy NER + custom patterns
        entities = self._extract_entities_nlp(doc)
        
        # 3. Extract secondary intents
        secondary_intents = self._extract_secondary_intents(doc, primary_intent)
        
        # 4. Determine context needed
        context_needed = self._determine_context_needed(primary_intent, entities)
        
        # 5. Assess urgency
        urgency = self._assess_urgency(doc, primary_intent)
        
        result = MessageIntent(
            primary_intent=primary_intent,
            secondary_intents=secondary_intents,
            confidence=confidence,
            entities=entities,
            context_needed=context_needed,
            urgency=urgency
        )
        
        # Debug logging
        if debug_logger.debug_mode:
            debug_logger.log_intent_classification(
                message=message,
                intent_result={
                    "primary_intent": primary_intent,
                    "secondary_intents": secondary_intents,
                    "confidence": confidence,
                    "entities": entities,
                    "context_needed": context_needed,
                    "urgency": urgency
                }
            )
        
        return result
    
    def _classify_intent_semantic(self, doc) -> Tuple[str, float]:
        """Classify intent using semantic similarity to examples"""
        if not doc.vector.any():
            return 'general_chat', 0.5
        
        message_vector = doc.vector
        similarities = {}
        
        # Calculate similarity to each intent
        for intent, intent_vector in self.intent_embeddings.items():
            similarity = cosine_similarity(
                message_vector.reshape(1, -1), 
                intent_vector.reshape(1, -1)
            )[0][0]
            similarities[intent] = similarity
        
        # Also check for linguistic patterns
        pattern_scores = self._get_pattern_scores(doc)
        
        # Combine semantic similarity with pattern matching
        final_scores = {}
        for intent in similarities:
            semantic_score = similarities[intent]
            pattern_score = pattern_scores.get(intent, 0)
            # Weight semantic similarity higher, but boost with patterns
            final_scores[intent] = semantic_score + (pattern_score * 0.3)
        
        # Get best intent
        best_intent = max(final_scores.items(), key=lambda x: x[1])
        intent, confidence = best_intent
        
        # Minimum confidence threshold
        if confidence < 0.4:
            return 'general_chat', 0.5
        
        return intent, min(confidence, 1.0)
    
    def _get_pattern_scores(self, doc) -> Dict[str, float]:
        """Get pattern-based scores for intents"""
        scores = {intent: 0 for intent in self.intent_examples.keys()}
        text = doc.text.lower()
        
        # Habit tracking patterns
        habit_indicators = ['usually', 'always', 'everyday', 'daily', 'regularly', 'typically', 'normally']
        if any(indicator in text for indicator in habit_indicators):
            scores['habit_tracking'] += 1.0
        
        # Look for habit verbs + frequency
        habit_verbs = ['drink', 'eat', 'take', 'exercise', 'meditate', 'work out', 'practice']
        frequency_words = ['everyday', 'daily', 'regularly', 'usually', 'always']
        if (any(verb in text for verb in habit_verbs) and 
            any(freq in text for freq in frequency_words)):
            scores['habit_tracking'] += 1.5
        
        # Commitment patterns
        if any(phrase in text for phrase in ["i'll", "i will", "i need to", "i should", "remind me"]):
            scores['commitment_making'] += 1.0
        
        # Mood patterns
        if any(word in text for word in ['feel', 'feeling', 'mood', 'stressed', 'happy', 'sad', 'anxious']):
            scores['mood_reflection'] += 1.0
        
        # Question patterns
        if '?' in text or text.startswith(('how', 'what', 'when', 'where', 'why', 'did i', 'have i')):
            scores['information_query'] += 1.0
        
        return scores
    
    def _extract_entities_nlp(self, doc) -> Dict[str, List[str]]:
        """Extract entities using spaCy NER and custom patterns"""
        entities = {
            'people': [],
            'habits': [],
            'time_references': [],
            'emotions': [],
            'actions': []
        }
        
        # 1. Use spaCy's built-in NER for people
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entities['people'].append(ent.text)
        
        # 2. Extract time references using NER and patterns
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                entities['time_references'].append(ent.text)
        
        # Also check our custom time patterns
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            if label == "TIME_PATTERN":
                time_ref = doc[start:end].text
                if time_ref not in entities['time_references']:
                    entities['time_references'].append(time_ref)
        
        # 3. Extract emotions using lexicon
        emotion_words = ['happy', 'sad', 'angry', 'frustrated', 'excited', 'anxious', 
                        'stressed', 'worried', 'calm', 'peaceful', 'tired', 'energetic',
                        'great', 'good', 'bad', 'terrible', 'amazing', 'awful', 'okay', 'fine']
        
        for token in doc:
            if token.lemma_.lower() in emotion_words:
                entities['emotions'].append(token.text)
        
        # 4. Extract habit-related content using linguistic analysis
        habits = self._extract_habits_nlp(doc)
        entities['habits'].extend(habits)
        
        # 5. Extract actions (verbs that indicate tasks/actions)
        action_verbs = ['call', 'email', 'text', 'meet', 'finish', 'complete', 'buy', 
                       'visit', 'schedule', 'book', 'prepare', 'review', 'write', 'create']
        
        for token in doc:
            if token.lemma_.lower() in action_verbs and token.pos_ == "VERB":
                entities['actions'].append(token.lemma_)
        
        return entities
    
    def _extract_habits_nlp(self, doc) -> List[str]:
        """Extract habits using linguistic analysis"""
        habits = []
        
        # Look for common habit structures
        for i, token in enumerate(doc):
            # Pattern: "drink/eat/take + object"
            if token.lemma_.lower() in ['drink', 'eat', 'take', 'have'] and token.pos_ == "VERB":
                # Look for the object
                objects = []
                for child in token.children:
                    if child.pos_ in ["NOUN", "PROPN"] and child.dep_ == "dobj":
                        objects.append(child.text)
                
                if objects:
                    habit_phrase = f"{token.lemma_} {' '.join(objects)}"
                    habits.append(habit_phrase)
                else:
                    habits.append(token.lemma_)
            
            # Pattern: "work out", "wake up"
            elif token.lemma_.lower() in ['work', 'wake'] and i + 1 < len(doc):
                next_token = doc[i + 1]
                if next_token.lemma_.lower() in ['out', 'up']:
                    habits.append(f"{token.lemma_} {next_token.lemma_}")
        
        # Look for explicit habit words
        habit_words = ['exercise', 'meditate', 'yoga', 'run', 'walk', 'study', 'read', 
                      'journal', 'sleep', 'stretch', 'swim', 'bike', 'cook', 'clean']
        
        for token in doc:
            if token.lemma_.lower() in habit_words:
                habits.append(token.lemma_)
        
        return list(set(habits))  # Remove duplicates
    
    def _extract_secondary_intents(self, doc, primary_intent: str) -> List[str]:
        """Extract secondary intents based on content analysis"""
        secondary = []
        text = doc.text.lower()
        
        # If primary is mood, check for commitments
        if primary_intent == 'mood_reflection':
            if any(phrase in text for phrase in ["i'll", "i should", "i need to"]):
                secondary.append('commitment_making')
        
        # If primary is habit, check for mood
        if primary_intent == 'habit_tracking':
            if any(word in text for word in ['feel', 'feeling', 'stressed', 'happy', 'tired']):
                secondary.append('mood_reflection')
        
        # Check for social references in any message
        if primary_intent != 'social_reference':
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    secondary.append('social_reference')
                    break
        
        return secondary
    
    def _determine_context_needed(self, primary_intent: str, entities: Dict[str, List[str]]) -> List[str]:
        """Determine what context is needed"""
        context_needed = []
        
        if primary_intent == 'habit_tracking':
            context_needed.extend(['habit_history', 'recent_conversations'])
        
        if primary_intent == 'information_query':
            context_needed.extend(['recent_conversations', 'habit_history', 'mood_trends', 'similar_commitments'])
        
        if primary_intent == 'commitment_making':
            context_needed.extend(['similar_commitments', 'recent_conversations'])
        
        if primary_intent == 'mood_reflection':
            context_needed.extend(['mood_trends', 'recent_conversations'])
        
        if primary_intent == 'social_reference' or entities.get('people'):
            context_needed.append('person_profile')
        
        if entities.get('time_references'):
            context_needed.append('temporal_context')
        
        return context_needed
    
    def _assess_urgency(self, doc, primary_intent: str) -> str:
        """Assess urgency of the message"""
        text = doc.text.lower()
        
        # High urgency indicators
        urgent_words = ['urgent', 'asap', 'immediately', 'emergency', 'help', 'crisis']
        if any(word in text for word in urgent_words):
            return 'high'
        
        # Time-based urgency
        if any(phrase in text for phrase in ['today', 'now', 'right now', 'this morning']):
            return 'medium'
        
        # Mood-based urgency
        if primary_intent == 'mood_reflection':
            negative_emotions = ['stressed', 'anxious', 'overwhelmed', 'panic', 'crisis']
            if any(emotion in text for emotion in negative_emotions):
                return 'medium'
        
        return 'low'


# Create global instance
nlp_intent_classifier = NLPIntentClassifier()