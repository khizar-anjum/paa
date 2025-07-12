from datetime import datetime, timedelta
import threading
from typing import Optional

class TimeService:
    """
    Centralized time service that can switch between real time and accelerated fake time.
    
    When fake time is enabled:
    - Each real second = time_multiplier fake minutes
    - Default: 1 real second = 10 fake minutes (600x speed)
    - All app components should use time_service.now() instead of datetime.now()
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._use_fake_time = False
        self._fake_start_time: Optional[datetime] = None
        self._real_start_time: Optional[datetime] = None
        self._time_multiplier = 600  # 1 real second = 10 fake minutes by default
        
    def _real_now(self) -> datetime:
        """Always get real time (never fake time)"""
        return datetime.now()
    
    def _calculate_fake_time(self) -> datetime:
        """Calculate fake time without acquiring lock (internal use only)"""
        if not self._use_fake_time:
            return self._real_now()
        
        if self._real_start_time is None or self._fake_start_time is None:
            return self._real_now()
        
        # Calculate elapsed real time
        real_elapsed_seconds = (self._real_now() - self._real_start_time).total_seconds()
        
        # Convert to fake time using multiplier
        fake_elapsed_seconds = real_elapsed_seconds * self._time_multiplier
        fake_elapsed = timedelta(seconds=fake_elapsed_seconds)
        
        return self._fake_start_time + fake_elapsed
    
    def now(self) -> datetime:
        """
        Get current time (real or fake depending on mode).
        
        Returns:
            datetime: Current time in the active time system
        """
        with self._lock:
            return self._calculate_fake_time()
    
    def start_fake_time(self, fake_start_time: Optional[datetime] = None, time_multiplier: int = 600) -> dict:
        """
        Start fake time system.
        
        Args:
            fake_start_time: Starting point for fake time (default: current real time)
            time_multiplier: How many fake seconds per real second (default: 600 = 10 minutes per second)
            
        Returns:
            dict: Status information about the started fake time system
        """
        with self._lock:
            real_now = self._real_now()
            self._real_start_time = real_now
            self._fake_start_time = fake_start_time or real_now
            self._time_multiplier = time_multiplier
            self._use_fake_time = True  # Set this AFTER setting the times
            
            return {
                "status": "fake_time_started",
                "real_start_time": self._real_start_time.isoformat(),
                "fake_start_time": self._fake_start_time.isoformat(),
                "time_multiplier": self._time_multiplier,
                "fake_minutes_per_real_second": self._time_multiplier / 60,
                "current_fake_time": self._calculate_fake_time().isoformat()
            }
    
    def stop_fake_time(self) -> dict:
        """
        Stop fake time and return to real time.
        
        Returns:
            dict: Status information
        """
        with self._lock:
            final_fake_time = self._calculate_fake_time() if self._use_fake_time else self._real_now()
            
            self._use_fake_time = False
            self._fake_start_time = None
            self._real_start_time = None
            
            return {
                "status": "fake_time_stopped",
                "final_fake_time": final_fake_time.isoformat(),
                "current_real_time": self._real_now().isoformat()
            }
    
    def set_multiplier(self, new_multiplier: int) -> dict:
        """
        Change the time acceleration multiplier while fake time is running.
        
        Args:
            new_multiplier: New multiplier value (fake seconds per real second)
            
        Returns:
            dict: Status information
        """
        with self._lock:
            if not self._use_fake_time:
                return {
                    "status": "error",
                    "message": "Fake time is not currently running"
                }
            
            # Capture current fake time
            current_fake = self._calculate_fake_time()
            
            # Reset start times to current moment with new multiplier
            self._real_start_time = self._real_now()
            self._fake_start_time = current_fake
            self._time_multiplier = new_multiplier
            
            return {
                "status": "multiplier_updated",
                "new_multiplier": self._time_multiplier,
                "fake_minutes_per_real_second": self._time_multiplier / 60,
                "continuation_point": current_fake.isoformat()
            }
    
    def jump_to_time(self, target_fake_time: datetime) -> dict:
        """
        Jump fake time to a specific datetime.
        
        Args:
            target_fake_time: The fake time to jump to
            
        Returns:
            dict: Status information
        """
        with self._lock:
            if not self._use_fake_time:
                return {
                    "status": "error", 
                    "message": "Fake time is not currently running"
                }
            
            # Reset start times to jump to target
            self._real_start_time = self._real_now()
            self._fake_start_time = target_fake_time
            
            return {
                "status": "time_jumped",
                "target_time": target_fake_time.isoformat(),
                "current_fake_time": self._calculate_fake_time().isoformat()
            }
    
    def get_status(self) -> dict:
        """
        Get current status of the time service.
        
        Returns:
            dict: Complete status information
        """
        with self._lock:
            current_fake_time = self._calculate_fake_time()
            status = {
                "using_fake_time": self._use_fake_time,
                "current_time": current_fake_time.isoformat(),
                "real_time": self._real_now().isoformat()
            }
            
            if self._use_fake_time:
                status.update({
                    "fake_start_time": self._fake_start_time.isoformat() if self._fake_start_time else None,
                    "real_start_time": self._real_start_time.isoformat() if self._real_start_time else None,
                    "time_multiplier": self._time_multiplier,
                    "fake_minutes_per_real_second": self._time_multiplier / 60,
                    "real_elapsed_seconds": (self._real_now() - self._real_start_time).total_seconds() if self._real_start_time else 0,
                    "fake_elapsed_time": (current_fake_time - self._fake_start_time).total_seconds() / 60 if self._fake_start_time else 0  # in minutes
                })
            
            return status
    
    @property
    def is_fake_time_active(self) -> bool:
        """Check if fake time is currently active."""
        with self._lock:
            return self._use_fake_time
    
    @property 
    def time_multiplier(self) -> int:
        """Get current time multiplier."""
        with self._lock:
            return self._time_multiplier

# Global instance for easy importing
time_service = TimeService()