import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class ScheduledJob:
    """Represents a scheduled job with fake-time awareness"""
    id: str
    func: Callable
    interval_minutes: int  # How often to run in fake time
    last_run_fake_time: Optional[datetime] = None
    is_active: bool = True

class FakeTimeScheduler:
    """
    Scheduler that respects fake time acceleration.
    
    Instead of using real cron jobs, this scheduler:
    1. Runs a background task every real second
    2. Checks if any jobs should run based on fake time
    3. Executes jobs when their fake time interval has passed
    """
    
    def __init__(self):
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._lock = Lock()
        
    def add_job(self, job_id: str, func: Callable, interval_minutes: int):
        """
        Add a job to run every interval_minutes in fake time.
        
        Args:
            job_id: Unique identifier for the job
            func: Async function to call
            interval_minutes: How often to run in fake time minutes
        """
        with self._lock:
            job = ScheduledJob(
                id=job_id,
                func=func,
                interval_minutes=interval_minutes
            )
            self._jobs[job_id] = job
            logger.info(f"Added fake-time job: {job_id} (every {interval_minutes} fake minutes)")
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler"""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.info(f"Removed job: {job_id}")
    
    async def start(self):
        """Start the fake-time scheduler"""
        if self._running:
            logger.info("Fake-time scheduler already running")
            return
            
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Fake-time scheduler started")
    
    async def stop(self):
        """Stop the fake-time scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Fake-time scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop that runs every real second"""
        from .time_service import time_service
        
        while self._running:
            try:
                current_fake_time = time_service.now()
                
                # Check each job to see if it should run
                with self._lock:
                    jobs_to_run = []
                    
                    for job in self._jobs.values():
                        if not job.is_active:
                            continue
                            
                        should_run = False
                        
                        if job.last_run_fake_time is None:
                            # First run
                            should_run = True
                        else:
                            # Check if enough fake time has passed
                            time_since_last_run = current_fake_time - job.last_run_fake_time
                            if time_since_last_run.total_seconds() >= job.interval_minutes * 60:
                                should_run = True
                        
                        if should_run:
                            jobs_to_run.append(job)
                            job.last_run_fake_time = current_fake_time
                
                # Run jobs outside the lock to avoid blocking
                for job in jobs_to_run:
                    try:
                        logger.info(f"Running fake-time job: {job.id} at fake time {current_fake_time}")
                        await job.func()
                    except Exception as e:
                        logger.error(f"Error running job {job.id}: {e}")
                
                # Sleep for 1 real second before checking again
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(1.0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        from .time_service import time_service
        
        with self._lock:
            return {
                "running": self._running,
                "current_fake_time": time_service.now().isoformat(),
                "jobs": [
                    {
                        "id": job.id,
                        "interval_minutes": job.interval_minutes,
                        "last_run_fake_time": job.last_run_fake_time.isoformat() if job.last_run_fake_time else None,
                        "is_active": job.is_active
                    }
                    for job in self._jobs.values()
                ]
            }

# Global instance
fake_time_scheduler = FakeTimeScheduler()