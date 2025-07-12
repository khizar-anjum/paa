import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Import the time service for fake time support
def get_time_service():
    """Lazy import to avoid circular imports"""
    from .time_service import time_service
    return time_service

logger = logging.getLogger(__name__)

class CommitmentParser:
    """
    Natural language commitment detection service.
    Parses user messages to extract commitments and deadlines.
    """
    
    def __init__(self):
        # Commitment detection patterns with capture groups
        self.commitment_patterns = [
            # "I'll do X today/tomorrow/etc"
            r"I'll\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "I need to do X today/tomorrow/etc"
            r"I\s+need\s+to\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "I should do X today/tomorrow/etc"
            r"I\s+should\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "I'm going to do X today/tomorrow/etc"
            r"I'm\s+going\s+to\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "X needs to be done today/tomorrow/etc"
            r"(.+?)\s+needs?\s+to\s+be\s+done\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "I have to do X today/tomorrow/etc"
            r"I\s+have\s+to\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "I really need to X today/tomorrow/etc"
            r"I\s+really\s+need\s+to\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
            
            # "I must do X today/tomorrow/etc"
            r"I\s+must\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+|this\s+weekend)",
        ]
        
        # Compile patterns for better performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.commitment_patterns]
    
    def extract_commitments(self, message: str) -> List[Dict]:
        """
        Extract commitments from a user message.
        
        Args:
            message: The user's message text
            
        Returns:
            List of commitment dictionaries with task_description and deadline
        """
        commitments = []
        
        for pattern in self.compiled_patterns:
            matches = pattern.finditer(message)
            
            for match in matches:
                task_description = match.group(1).strip()
                time_phrase = match.group(2).strip()
                
                # Clean up task description
                task_description = self._clean_task_description(task_description)
                
                # Skip if task is too short or generic
                if (len(task_description) < 3 or 
                    task_description.lower() in ['it', 'this', 'that', 'do it', 'do this', 'do that', 'something', 'do something']):
                    continue
                
                # Parse the deadline
                deadline = self._parse_deadline(time_phrase)
                
                if deadline:
                    commitment = {
                        'task_description': task_description,
                        'original_message': message,
                        'deadline': deadline,
                        'time_phrase': time_phrase
                    }
                    commitments.append(commitment)
                    logger.info(f"Detected commitment: {task_description} by {time_phrase}")
        
        # Remove duplicates based on task description
        unique_commitments = []
        seen_tasks = set()
        
        for commitment in commitments:
            task_lower = commitment['task_description'].lower()
            if task_lower not in seen_tasks:
                seen_tasks.add(task_lower)
                unique_commitments.append(commitment)
        
        return unique_commitments
    
    def _clean_task_description(self, task: str) -> str:
        """Clean and normalize task descriptions."""
        # Remove common prefixes/suffixes
        task = re.sub(r'^(to\s+|the\s+)', '', task, flags=re.IGNORECASE)
        task = re.sub(r'\s+(though|but|however)$', '', task, flags=re.IGNORECASE)
        
        # Capitalize first letter
        if task:
            task = task[0].upper() + task[1:]
        
        return task.strip()
    
    def _parse_deadline(self, time_phrase: str) -> Optional[datetime]:
        """
        Parse natural language time phrases into datetime objects.
        
        Args:
            time_phrase: Natural language time description
            
        Returns:
            datetime object for the deadline, or None if unparseable
        """
        now = get_time_service().now()
        time_phrase_lower = time_phrase.lower().strip()
        
        try:
            if time_phrase_lower == "today":
                # End of today (11:59 PM)
                return now.replace(hour=23, minute=59, second=59, microsecond=0)
            
            elif time_phrase_lower == "tomorrow":
                # End of tomorrow
                tomorrow = now + timedelta(days=1)
                return tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)
            
            elif time_phrase_lower == "this weekend":
                # End of upcoming Sunday
                days_until_sunday = (6 - now.weekday()) % 7
                if days_until_sunday == 0 and now.hour >= 18:  # If it's Sunday evening
                    days_until_sunday = 7  # Next Sunday
                sunday = now + timedelta(days=days_until_sunday)
                return sunday.replace(hour=23, minute=59, second=59, microsecond=0)
            
            elif time_phrase_lower.startswith("this "):
                # "this week", "this month", etc.
                period = time_phrase_lower[5:]
                
                if period == "week":
                    # End of this Sunday
                    days_until_sunday = (6 - now.weekday()) % 7
                    if days_until_sunday == 0:
                        days_until_sunday = 7
                    sunday = now + timedelta(days=days_until_sunday)
                    return sunday.replace(hour=23, minute=59, second=59, microsecond=0)
                
                elif period in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    return self._get_next_weekday(period)
            
            elif time_phrase_lower.startswith("by "):
                # "by Friday", "by next week", etc.
                target = time_phrase_lower[3:]
                
                if target in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    return self._get_next_weekday(target)
                
                elif target == "next week":
                    # End of next Sunday
                    days_until_next_sunday = (6 - now.weekday()) % 7 + 7
                    next_sunday = now + timedelta(days=days_until_next_sunday)
                    return next_sunday.replace(hour=23, minute=59, second=59, microsecond=0)
        
        except Exception as e:
            logger.error(f"Error parsing time phrase '{time_phrase}': {e}")
        
        # Default: end of today if we can't parse
        return get_time_service().now().replace(hour=23, minute=59, second=59, microsecond=0)
    
    def _get_next_weekday(self, weekday_name: str) -> datetime:
        """Get the next occurrence of a specific weekday."""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekdays.get(weekday_name.lower())
        if target_weekday is None:
            return get_time_service().now().replace(hour=23, minute=59, second=59, microsecond=0)
        
        now = get_time_service().now()
        current_weekday = now.weekday()
        
        # Calculate days until target weekday
        days_ahead = target_weekday - current_weekday
        
        # If target day is today but it's late in the day, use next week
        if days_ahead == 0 and now.hour >= 18:
            days_ahead = 7
        elif days_ahead <= 0:
            days_ahead += 7
        
        target_date = now + timedelta(days=days_ahead)
        return target_date.replace(hour=23, minute=59, second=59, microsecond=0)

# Global instance for easy importing
commitment_parser = CommitmentParser()