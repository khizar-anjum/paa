"""
Habit Matching and Normalization Service
Prevents duplicate habit creation by matching similar habit names.
"""

import re
from typing import List, Optional, Tuple
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
import database as models


class HabitMatcher:
    """Service to match and normalize similar habit names"""

    def __init__(self):
        # Common words to remove when normalizing
        self.stop_words = {
            'i', 'my', 'the', 'a', 'an', 'do', 'did', 'doing', 
            'have', 'had', 'has', 'take', 'took', 'taking',
            'go', 'went', 'going', 'get', 'got', 'getting',
            'make', 'made', 'making', 'some', 'today', 'yesterday'
        }
        
        # Common habit verbs and their normalized forms
        self.verb_normalizations = {
            'exercised': 'exercise',
            'worked out': 'workout',
            'did laundry': 'laundry',
            'do laundry': 'laundry', 
            'meditated': 'meditate',
            'went for a walk': 'walk',
            'took a walk': 'walk',
            'cooked': 'cook',
            'cleaned': 'clean',
            'studied': 'study',
            'read': 'reading',
            'drank water': 'drink water',
            'played games': 'gaming',
            'play games': 'gaming'
        }

    def normalize_habit_name(self, habit_name: str) -> str:
        """
        Normalize a habit name for better matching.
        
        Args:
            habit_name: Raw habit name from user input
            
        Returns:
            Normalized habit name
        """
        # Convert to lowercase
        normalized = habit_name.lower().strip()
        
        # Check for direct verb normalizations first
        for pattern, replacement in self.verb_normalizations.items():
            if pattern in normalized:
                normalized = normalized.replace(pattern, replacement)
        
        # Remove punctuation except spaces and hyphens
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        
        # Split into words and remove stop words
        words = normalized.split()
        filtered_words = [word for word in words if word not in self.stop_words]
        
        # If we removed all words, keep the original
        if not filtered_words:
            return habit_name.lower().strip()
        
        # Rejoin words
        normalized = ' '.join(filtered_words)
        
        # Handle common patterns
        normalized = self._apply_pattern_normalizations(normalized, habit_name)
        
        return normalized.strip()

    def _apply_pattern_normalizations(self, text: str, original_text: str) -> str:
        """Apply common pattern normalizations"""
        
        # Gaming patterns - match various forms
        gaming_patterns = [
            ('gaming evening after work', 'gaming'),
            ('gaming evening', 'gaming'),
            ('games evening after work', 'gaming'),
            ('games evening', 'gaming'),
            ('games after work', 'gaming')
        ]
        
        for pattern, replacement in gaming_patterns:
            if pattern in text:
                return replacement
        
        # General games -> gaming
        if 'games' in text:
            text = text.replace('games', 'gaming')
            
        # Cooking patterns
        cooking_patterns = [
            ('self cook meals', 'cooking'),
            ('cooked meals', 'cooking'),
            ('cook meals', 'cooking'),
            ('self cooked', 'cooking')
        ]
        
        for pattern, replacement in cooking_patterns:
            if pattern in text:
                return replacement
            
        # "therapy chat" -> "therapy"
        if 'therapy' in text and 'chat' in text:
            text = 'therapy'
            
        # Remove redundant words
        text = re.sub(r'\b(daily|regularly|usually|always|after|work|evening|morning|in|the)\b', '', text).strip()
        text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
        
        # If we're left with just empty/meaningless words, return original pattern
        if not text or text in ['in', 'the', 'a', 'an']:
            # Fallback to simpler pattern detection
            if 'gaming' in original_text or 'games' in original_text:
                return 'gaming'
        
        return text

    def find_similar_habit(
        self, 
        habit_name: str, 
        user_id: int, 
        db: Session,
        similarity_threshold: float = 0.7
    ) -> Optional[models.Habit]:
        """
        Find a similar existing habit for the user.
        
        Args:
            habit_name: The habit name to search for
            user_id: User ID to scope the search
            db: Database session
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            Similar habit if found, None otherwise
        """
        # Normalize the input habit name
        normalized_input = self.normalize_habit_name(habit_name)
        
        # Get all active habits for the user
        existing_habits = db.query(models.Habit).filter(
            models.Habit.user_id == user_id,
            models.Habit.is_active == 1
        ).all()
        
        best_match = None
        best_similarity = 0.0
        
        for habit in existing_habits:
            # Normalize existing habit name
            normalized_existing = self.normalize_habit_name(habit.name)
            
            # Calculate similarity
            similarity = self._calculate_similarity(normalized_input, normalized_existing)
            
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = habit
        
        return best_match

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two normalized habit names.
        
        Uses multiple similarity measures for better accuracy.
        """
        # Exact match
        if text1 == text2:
            return 1.0
        
        # Check if one is contained in the other
        if text1 in text2 or text2 in text1:
            return 0.9
        
        # Sequence matcher similarity
        seq_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if words1 and words2:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            word_similarity = intersection / union if union > 0 else 0.0
        else:
            word_similarity = 0.0
        
        # Take the maximum of both similarities
        return max(seq_similarity, word_similarity)

    def suggest_habit_name(self, raw_input: str) -> str:
        """
        Suggest a clean habit name from raw user input.
        
        Args:
            raw_input: Raw habit identifier from user
            
        Returns:
            Suggested clean habit name
        """
        normalized = self.normalize_habit_name(raw_input)
        
        # Apply some final cleanup for better readability
        suggested = normalized.replace('-', ' ').strip()
        
        # Capitalize first letter of each word for display
        return ' '.join(word.capitalize() for word in suggested.split())


# Global instance
habit_matcher = HabitMatcher()