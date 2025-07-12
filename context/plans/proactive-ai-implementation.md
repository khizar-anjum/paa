# Proactive AI Implementation Plan

## 🧠 Vision: From Reactive to Proactive AI

Transform the Personal AI Assistant from a reactive chatbot into a genuinely proactive companion that:
- Remembers commitments from conversations and follows up
- Initiates helpful conversations at key moments
- Provides gentle accountability without being annoying
- Learns user patterns to become more effective over time

## 🎯 Core Use Cases

### 1. Commitment Tracking & Follow-up
```
User: "I really need to do laundry today"
AI: [Later] "You mentioned doing laundry today. How did it go?"
AI: [Next day if no response] "Looks like laundry got away from you yesterday. Want to tackle it today?"
```

### 2. Scheduled Proactive Check-ins
```
AI: [5 PM Monday-Friday] "Hope work wrapped up well today! How was it? Want to chat about anything?"
```

## 🏗️ Technical Architecture

### New Database Models
```sql
-- Track user commitments extracted from conversations
CREATE TABLE commitments (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    task_description TEXT,
    original_message TEXT,
    deadline DATE,
    status TEXT DEFAULT 'pending', -- pending, completed, missed, dismissed
    created_from_conversation_id INTEGER,
    last_reminded_at TIMESTAMP,
    reminder_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (created_from_conversation_id) REFERENCES conversations(id)
);

-- Proactive messages sent to users
CREATE TABLE proactive_messages (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    message_type TEXT, -- commitment_reminder, scheduled_prompt, escalation
    content TEXT,
    related_commitment_id INTEGER,
    scheduled_for TIMESTAMP,
    sent_at TIMESTAMP,
    user_responded BOOLEAN DEFAULT FALSE,
    response_content TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (related_commitment_id) REFERENCES commitments(id)
);

-- Scheduled recurring prompts (like 5 PM work check-ins)
CREATE TABLE scheduled_prompts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    prompt_type TEXT, -- work_checkin, morning_motivation, evening_reflection
    schedule_time TIME,
    schedule_days TEXT, -- "monday,tuesday,wednesday,thursday,friday"
    prompt_template TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_sent_at TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Background Scheduler Framework
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(CronTrigger(minute=0))  # Every hour
async def check_commitments():
    # Find overdue commitments
    # Send reminder messages
    # Handle escalation logic

@scheduler.scheduled_job(CronTrigger(hour=17, minute=0))  # 5 PM daily
async def work_checkin():
    # Send "How was work?" prompts to weekday users
    
scheduler.start()
```

## 📋 Implementation Phases

### **Phase 1: Foundation & Infrastructure** (2-3 hours) ✅ COMPLETED

#### Backend Changes ✅
1. **Add APScheduler Dependencies** ✅
   ```bash
   pip install apscheduler
   ```

2. **Create New Database Models** ✅
   - Added `Commitment`, `ProactiveMessage`, `ScheduledPrompt` models to `database.py`
   - Added corresponding Pydantic schemas to `schemas.py`

3. **Background Job Framework** ✅
   - Created `scheduler.py` module with job functions
   - Initialized scheduler in `main.py` with graceful shutdown
   - Added default prompt initialization for new users

4. **New API Endpoints** ✅
   ```python
   # Commitment management
   GET /commitments - Get user's commitments ✅
   POST /commitments/{commitment_id}/complete - Mark commitment as done ✅
   POST /commitments/{commitment_id}/dismiss - Dismiss reminder ✅
   POST /commitments/{commitment_id}/postpone - Reschedule commitment ✅
   
   # Proactive messages
   GET /proactive-messages - Get pending messages for user ✅
   POST /proactive-messages/{message_id}/acknowledge - Mark message as read ✅
   
   # Scheduled prompts
   GET /scheduled-prompts - Get user's prompt preferences ✅
   PUT /scheduled-prompts/{prompt_id} - Update prompt settings ✅
   ```

#### Frontend Changes ✅
1. **Proactive Message Display** ✅
   - Added visual indicators in `PersistentChatPanel.tsx` for AI-initiated messages
   - Different styling for proactive vs reactive messages (yellow background with clock icon)
   - Action buttons for commitment responses (Done, Postpone, Dismiss)
   - Created `lib/api/proactive.ts` for API integration

2. **Settings Page** (Deferred to later phases)
   - Basic toggle for enabling/disabling proactive features

### **Phase 2: Natural Language Commitment Detection** (2-3 hours)

#### Backend Implementation
1. **Commitment Parser Service**
   ```python
   # services/commitment_parser.py
   import re
   from datetime import datetime, timedelta
   
   commitment_patterns = [
       r"I'll\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+)",
       r"I\s+need\s+to\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+)",
       r"I\s+should\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+)",
       r"I'm\s+going\s+to\s+(.+?)\s+(today|tomorrow|this\s+\w+|by\s+\w+)",
       r"(.+?)\s+needs?\s+to\s+be\s+done\s+(today|tomorrow|this\s+\w+|by\s+\w+)"
   ]
   
   def extract_commitments(message: str) -> List[Dict]:
       # Parse message for commitments
       # Extract task description and deadline
       # Return structured commitment data
   ```

2. **Time Parsing Logic**
   ```python
   def parse_deadline(time_phrase: str) -> datetime:
       # "today" -> end of today
       # "tomorrow" -> end of tomorrow  
       # "this weekend" -> end of Sunday
       # "by Friday" -> end of Friday
   ```

3. **Integration with Chat Endpoint**
   - Modify `/chat` endpoint to detect commitments in user messages
   - Automatically create `Commitment` records
   - Schedule follow-up reminders

#### Frontend Updates
1. **Commitment Acknowledgment UI**
   - Quick action buttons in chat for commitment responses
   - "Mark as Done", "Postpone", "Dismiss" options
   - Smooth animations for user feedback

### **Phase 3: Scheduled Prompts System** (1-2 hours)

#### Backend Implementation
1. **Default Scheduled Prompts**
   ```python
   default_prompts = [
       {
           "prompt_type": "work_checkin",
           "schedule_time": "17:00",
           "schedule_days": "monday,tuesday,wednesday,thursday,friday",
           "prompt_template": "Hope work wrapped up well today! How was it? Want to chat about anything?"
       },
       {
           "prompt_type": "weekend_reflection",
           "schedule_time": "18:00", 
           "schedule_days": "sunday",
           "prompt_template": "How was your weekend? Ready for the week ahead?"
       }
   ]
   ```

2. **Prompt Scheduling Logic**
   ```python
   async def send_scheduled_prompts():
       current_time = datetime.now()
       due_prompts = get_due_scheduled_prompts(current_time)
       
       for prompt in due_prompts:
           await send_proactive_message(
               user_id=prompt.user_id,
               content=prompt.prompt_template,
               message_type="scheduled_prompt"
           )
   ```

#### Frontend Updates
1. **Prompt Management Settings**
   - Toggle prompts on/off
   - Customize timing (future enhancement)
   - Preview prompt templates

### **Phase 4: Persistence & Escalation Logic** (2-3 hours)

#### Backend Implementation
1. **Follow-up Intelligence**
   ```python
   async def handle_commitment_followup(commitment: Commitment):
       if commitment.is_overdue() and not commitment.user_responded:
           if commitment.reminder_count == 0:
               # First follow-up: gentle check-in
               message = f"You mentioned {commitment.task_description}. How did it go?"
           elif commitment.reminder_count == 1:
               # Second follow-up: encouraging retry
               message = f"Looks like {commitment.task_description} might have gotten away from you. Want to try again today?"
           else:
               # Cap at 2 reminders to avoid being annoying
               return
               
           await send_proactive_message(
               user_id=commitment.user_id,
               content=message,
               message_type="commitment_reminder",
               related_commitment_id=commitment.id
           )
           
           commitment.reminder_count += 1
           commitment.last_reminded_at = datetime.now()
   ```

2. **User Response Handling**
   ```python
   async def process_commitment_response(message: str, commitment_id: int):
       # Parse responses like "done", "finished it", "I'll do it tomorrow"
       # Update commitment status accordingly
       # Reschedule if postponed
   ```

#### Frontend Implementation
1. **Enhanced Message Actions**
   - Context-aware quick responses
   - Smart postponement options ("Tomorrow", "This weekend", "Next week")
   - Completion confirmation with celebration animations

### **Phase 5: Advanced Proactivity** (1-2 hours)

#### Backend Implementation
1. **Smart Timing Logic**
   ```python
   def should_send_message(user_id: int, message_type: str) -> bool:
       # Check user's activity patterns
       # Respect quiet hours
       # Avoid overwhelming with too many messages
       # Consider response history
   ```

2. **User Preference Learning**
   ```python
   async def learn_user_patterns(user_id: int):
       # Analyze response times
       # Identify preferred communication windows
       # Adjust scheduling accordingly
   ```

#### Frontend Implementation
1. **Advanced Settings**
   - Quiet hours configuration
   - Message frequency preferences
   - Proactivity intensity levels (gentle, normal, persistent)

2. **Analytics Integration**
   - Track proactive message effectiveness
   - Show completion rates for different reminder types
   - User engagement metrics

## 🔄 Example User Flows

### **Commitment Flow Example**
```
Time: 2:00 PM
User: "Ugh, I really need to do laundry today"
AI: "Got it! I'll check in later to see how the laundry goes."
[System: Creates commitment with deadline = end of today]

Time: 8:00 PM (Background job runs)
AI: "Hey! You mentioned doing laundry today. How did it go?"

User: "Oh thanks for reminding me! Just finished it 👍"
[System: Marks commitment as completed]

Alternative: No response by 9:00 AM next day
AI: "Looks like the laundry might have gotten away from you yesterday 😅 Want to tackle it today?"
[System: Creates new commitment for today]
```

### **Work Check-in Flow Example**
```
Time: 5:00 PM (Monday-Friday)
AI: "Hope work wrapped up well today! How was it? Want to chat about anything?"

User: "It was pretty stressful, had a difficult client meeting"
AI: "That sounds challenging. Want to talk about what made it difficult? Sometimes it helps to process these things."

[Conversation continues naturally based on user's response]
```

## 🛠️ Technical Considerations

### **Performance & Scalability**
- Background jobs run efficiently with APScheduler
- Database queries optimized with proper indexing
- Rate limiting for proactive messages to prevent spam

### **User Experience**
- Clear visual distinction between proactive and reactive messages
- Easy opt-out mechanisms for users who find it overwhelming
- Gentle, encouraging tone in all proactive communications

### **Privacy & Security**
- All proactive features respect existing user authentication
- Commitment data is user-scoped and secure
- No external notifications without explicit user consent

## 🎯 Success Metrics

### **Phase 1 Success Criteria**
- [x] Background scheduler running without errors
- [x] New database models created and functional
- [x] Basic proactive message display in chat

### **Phase 2 Success Criteria**  
- [x] Commitment detection working for common patterns
- [x] Automatic reminder scheduling functional
- [x] User can acknowledge/dismiss commitments

### **Phase 3 Success Criteria**
- [ ] 5 PM work check-ins working Monday-Friday
- [ ] Users can enable/disable scheduled prompts
- [ ] Prompts appear naturally in chat flow

### **Phase 4 Success Criteria**
- [ ] Follow-up logic working with 24-48 hour delays
- [ ] Maximum 2 reminders per commitment to avoid annoyance
- [ ] User responses properly update commitment status

### **Phase 5 Success Criteria**
- [ ] Smart timing prevents message overload
- [ ] User preferences learned and respected
- [ ] Advanced settings functional

## 🚀 Implementation Timeline

**Total Estimated Time: 8-11 hours**

- **Phase 1**: 2-3 hours (Foundation)
- **Phase 2**: 2-3 hours (NLP & Commitment Detection)  
- **Phase 3**: 1-2 hours (Scheduled Prompts)
- **Phase 4**: 2-3 hours (Follow-up Logic)
- **Phase 5**: 1-2 hours (Advanced Features)

Each phase builds on the previous one, ensuring we have a working system at every step. The implementation can be demo-ready after Phase 3, with Phases 4-5 adding sophistication.

## 🎉 Expected Impact

This implementation will transform the Personal AI Assistant from a passive tool into an active companion that:

1. **Remembers what matters** - Never lets important commitments slip through the cracks
2. **Initiates meaningful conversations** - Creates natural touchpoints for support
3. **Provides gentle accountability** - Helps users follow through without being pushy
4. **Learns and adapts** - Becomes more helpful over time based on user patterns

The result will be a truly revolutionary AI assistant that proactively supports users in achieving their goals and maintaining better life management habits.