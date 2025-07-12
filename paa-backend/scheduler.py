from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date, time as time_obj
from database import SessionLocal, Commitment, ProactiveMessage, ScheduledPrompt, User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()

def get_db() -> Session:
    """Get database session for scheduler jobs"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed in the job functions

async def send_proactive_message(user_id: int, content: str, message_type: str, related_commitment_id: int = None):
    """Send a proactive message to the user"""
    db = get_db()
    try:
        # Create proactive message record
        proactive_msg = ProactiveMessage(
            user_id=user_id,
            message_type=message_type,
            content=content,
            related_commitment_id=related_commitment_id,
            sent_at=datetime.utcnow()
        )
        db.add(proactive_msg)
        db.commit()
        
        logger.info(f"Sent proactive message to user {user_id}: {message_type}")
        
        # In a real implementation, you would also:
        # - Send push notification
        # - Add to chat interface
        # - Send email/SMS if configured
        
    except Exception as e:
        logger.error(f"Error sending proactive message: {e}")
        db.rollback()
    finally:
        db.close()

async def check_commitment_reminders():
    """Check for overdue commitments and send reminders"""
    db = get_db()
    try:
        now = datetime.utcnow()
        today = date.today()
        
        # Find overdue commitments that need reminders
        overdue_commitments = db.query(Commitment).filter(
            Commitment.status == "pending",
            Commitment.deadline < today,
            Commitment.reminder_count < 2  # Max 2 reminders to avoid being annoying
        ).all()
        
        for commitment in overdue_commitments:
            # Check if we should send a reminder (not too frequent)
            if commitment.last_reminded_at is None or \
               (now - commitment.last_reminded_at).total_seconds() > 24 * 3600:  # 24 hours
                
                if commitment.reminder_count == 0:
                    # First follow-up: gentle check-in
                    message = f"You mentioned {commitment.task_description}. How did it go?"
                elif commitment.reminder_count == 1:
                    # Second follow-up: encouraging retry
                    message = f"Looks like {commitment.task_description} might have gotten away from you. Want to try again today?"
                
                await send_proactive_message(
                    user_id=commitment.user_id,
                    content=message,
                    message_type="commitment_reminder",
                    related_commitment_id=commitment.id
                )
                
                # Update commitment
                commitment.reminder_count += 1
                commitment.last_reminded_at = now
                db.commit()
                
    except Exception as e:
        logger.error(f"Error checking commitment reminders: {e}")
        db.rollback()
    finally:
        db.close()

async def send_scheduled_prompts():
    """Send scheduled prompts like work check-ins"""
    db = get_db()
    try:
        now = datetime.utcnow()
        current_time = now.time()
        current_day = now.strftime("%A").lower()  # monday, tuesday, etc.
        
        # Find scheduled prompts that should be sent now
        scheduled_prompts = db.query(ScheduledPrompt).filter(
            ScheduledPrompt.is_active == True
        ).all()
        
        for prompt in scheduled_prompts:
            # Check if today is a scheduled day
            if current_day in prompt.schedule_days.lower():
                # Check if it's time to send (within 5 minutes of scheduled time)
                scheduled_time = prompt.schedule_time
                time_diff = abs(
                    (current_time.hour * 60 + current_time.minute) - 
                    (scheduled_time.hour * 60 + scheduled_time.minute)
                )
                
                if time_diff <= 5:  # Within 5 minutes
                    # Check if we already sent today
                    if prompt.last_sent_at is None or \
                       prompt.last_sent_at.date() < now.date():
                        
                        await send_proactive_message(
                            user_id=prompt.user_id,
                            content=prompt.prompt_template,
                            message_type="scheduled_prompt"
                        )
                        
                        # Update last sent time
                        prompt.last_sent_at = now
                        db.commit()
                        
    except Exception as e:
        logger.error(f"Error sending scheduled prompts: {e}")
        db.rollback()
    finally:
        db.close()

async def initialize_default_prompts_for_user(user_id: int):
    """Initialize default scheduled prompts for a new user (async version)"""
    db = get_db()
    try:
        # Check if user already has prompts
        existing_prompts = db.query(ScheduledPrompt).filter(
            ScheduledPrompt.user_id == user_id
        ).first()
        
        if not existing_prompts:
            # Create default work check-in prompt
            work_checkin = ScheduledPrompt(
                user_id=user_id,
                prompt_type="work_checkin",
                schedule_time=time_obj(17, 0),  # 5:00 PM
                schedule_days="monday,tuesday,wednesday,thursday,friday",
                prompt_template="Hope work wrapped up well today! How was it? Want to chat about anything?",
                is_active=True
            )
            
            # Create default weekend reflection prompt
            weekend_reflection = ScheduledPrompt(
                user_id=user_id,
                prompt_type="weekend_reflection",
                schedule_time=time_obj(18, 0),  # 6:00 PM
                schedule_days="sunday",
                prompt_template="How was your weekend? Ready for the week ahead?",
                is_active=True
            )
            
            db.add(work_checkin)
            db.add(weekend_reflection)
            db.commit()
            
            logger.info(f"Initialized default prompts for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error initializing default prompts: {e}")
        db.rollback()
    finally:
        db.close()

def initialize_default_prompts_for_user_sync(user_id: int):
    """Initialize default scheduled prompts for a new user (synchronous version)"""
    db = get_db()
    try:
        # Check if user already has prompts
        existing_prompts = db.query(ScheduledPrompt).filter(
            ScheduledPrompt.user_id == user_id
        ).first()
        
        if not existing_prompts:
            # Create default work check-in prompt
            work_checkin = ScheduledPrompt(
                user_id=user_id,
                prompt_type="work_checkin",
                schedule_time=time_obj(17, 0),  # 5:00 PM
                schedule_days="monday,tuesday,wednesday,thursday,friday",
                prompt_template="Hope work wrapped up well today! How was it? Want to chat about anything?",
                is_active=True
            )
            
            # Create default weekend reflection prompt
            weekend_reflection = ScheduledPrompt(
                user_id=user_id,
                prompt_type="weekend_reflection",
                schedule_time=time_obj(18, 0),  # 6:00 PM
                schedule_days="sunday",
                prompt_template="How was your weekend? Ready for the week ahead?",
                is_active=True
            )
            
            db.add(work_checkin)
            db.add(weekend_reflection)
            db.commit()
            
            logger.info(f"Initialized default prompts for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error initializing default prompts: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    try:
        # Schedule commitment reminder checks every hour
        scheduler.add_job(
            check_commitment_reminders,
            CronTrigger(minute=0),  # Top of every hour
            id="commitment_reminders",
            replace_existing=True
        )
        
        # Schedule prompt checks every 5 minutes
        scheduler.add_job(
            send_scheduled_prompts,
            IntervalTrigger(minutes=5),
            id="scheduled_prompts",
            replace_existing=True
        )
        
        # Only start if not already running
        if not scheduler.running:
            scheduler.start()
            logger.info("Proactive AI scheduler started successfully")
        else:
            logger.info("Proactive AI scheduler already running")
        
    except RuntimeError as e:
        if "no running event loop" in str(e):
            logger.info("Scheduler will start when FastAPI server starts (no event loop yet)")
        else:
            logger.error(f"Runtime error starting scheduler: {e}")
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")

def stop_scheduler():
    """Stop the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Proactive AI scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")

# Expose the scheduler instance for external access
__all__ = ["scheduler", "start_scheduler", "stop_scheduler", "initialize_default_prompts_for_user", "initialize_default_prompts_for_user_sync", "send_proactive_message"]