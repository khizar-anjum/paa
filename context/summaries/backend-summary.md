# PAA Backend Summary

## Architecture
- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: PostgreSQL
- **Authentication**: JWT-based user authentication
- **AI Integration**: LLM-powered natural language processing

## Core Models

### Commitment (Unified Model)
```python
class Commitment(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_description = Column(String, nullable=False)
    original_message = Column(String)  # From chat interface
    
    # Unified scheduling
    deadline = Column(Date)  # For one-time commitments
    recurrence_pattern = Column(String(20), default="none")  # none, daily, weekly, monthly
    recurrence_interval = Column(Integer, default=1)
    recurrence_days = Column(String(50))  # For weekly: "mon,wed,fri"
    recurrence_end_date = Column(Date)
    due_time = Column(Time)  # For recurring commitments
    
    # Status and completion tracking
    status = Column(String(20), default="pending")  # pending, active, completed, dismissed, missed
    completion_count = Column(Integer, default=0)
    last_completed_at = Column(DateTime)
    
    # Metadata
    reminder_settings = Column(JSON)
    reminder_count = Column(Integer, default=0)
    last_reminded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### CommitmentCompletion (Tracking Individual Completions)
```python
class CommitmentCompletion(Base):
    id = Column(Integer, primary_key=True)
    commitment_id = Column(Integer, ForeignKey('commitments.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    completion_date = Column(Date, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    skipped = Column(Boolean, default=False)
    notes = Column(String)
```

## API Endpoints

### Commitment Management
- `GET /commitments` - List commitments with filtering
  - Query params: `status`, `type` (one_time/recurring), `recurrence`, `due`, `overdue`, `sort_by`, `order`
- `POST /commitments` - Create new commitment
- `GET /commitments/{id}` - Get specific commitment
- `PUT /commitments/{id}` - Update commitment
- `DELETE /commitments/{id}` - Delete commitment
- `POST /commitments/{id}/complete` - Mark commitment complete (handles both one-time and recurring)
- `POST /commitments/{id}/skip` - Skip recurring commitment for today
- `GET /commitments/{id}/completions` - Get completion history for recurring commitments

### Analytics
- `GET /analytics/commitments` - Commitment completion analytics
- `GET /analytics/overview` - Overall statistics and metrics
- `GET /analytics/mood` - Mood tracking analytics

### Chat & Conversations
- `GET /conversations` - List user conversations
- `POST /conversations` - Create new conversation
- `POST /conversations/{id}/messages` - Send message to conversation
- `GET /conversations/{id}/messages` - Get conversation messages

## Key Services

### Action Processor
Handles LLM-based intent detection and commitment creation from natural language:
```python
class ActionProcessor:
    def process_message(self, message: str, user_id: int)
    # Detects intents: create_commitment, complete_commitment, etc.
    # Extracts commitment details from natural language
    # Creates appropriate database records
```

### Commitment Logic
- **One-time commitments**: Simple completion changes status to "completed"
- **Recurring commitments**: Completion creates CommitmentCompletion record, commitment stays "active"
- **Skip functionality**: Creates completion record with `skipped=True`
- **Overdue detection**: Automatic status updates based on deadlines

## Database Migration

### Migration Script: `migrate_habits_to_commitments.py`
- **Safe Migration**: Creates backups before making changes
- **Data Preservation**: Converts all habit records to recurring commitments
- **Completion History**: Migrates habit_logs to commitment_completions
- **Cleanup**: Removes old habit tables after successful migration

```python
# Key migration logic:
for habit in habits:
    commitment = models.Commitment(
        user_id=habit.user_id,
        task_description=habit.name,
        recurrence_pattern='daily' if habit.frequency == 'daily' else 'weekly',
        due_time=habit.reminder_time,
        status='active',
        completion_count=habit_log_count,
        created_at=habit.created_at
    )
```

## Authentication & Users
- JWT token-based authentication
- User model with profile information
- Session management for chat conversations
- Protected routes requiring authentication

## Configuration & Deployment
- Environment-based configuration
- Database connection pooling
- CORS configuration for frontend integration
- Error handling and logging

## API Schemas (Pydantic)
- `CommitmentBase`, `CommitmentCreate`, `CommitmentUpdate`
- `CommitmentCompletion`, `CommitmentCompletionCreate`
- `ConversationMessage`, `ChatResponse`
- `AnalyticsResponse`, `OverviewAnalytics`

## Key Features
1. **Unified System**: Single model handling both one-time and recurring commitments
2. **LLM Integration**: Natural language understanding for commitment creation
3. **Flexible Recurrence**: Supports daily, weekly, monthly patterns with custom intervals
4. **Completion Tracking**: Individual completion records for recurring commitments
5. **Analytics**: Comprehensive statistics and trend analysis
6. **Chat Interface**: Conversational commitment management
7. **Time Support**: Optional due times for recurring commitments

## Recent Changes
- Removed separate habits system entirely
- Enhanced commitment model with recurrence fields
- Added commitment completion tracking table
- Updated all endpoints to use unified commitment system
- Improved analytics to handle both commitment types
- Added time field support in API schemas