# PAA Backend Summary

## Architecture
- **Framework**: FastAPI with async support
- **ORM**: SQLAlchemy with PostgreSQL
- **Authentication**: JWT-based with bearer tokens
- **AI Integration**: LLM-powered natural language processing
- **API Design**: RESTful with Pydantic validation

## Database Models

### Core Models

#### User
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    commitments = relationship("Commitment", back_populates="user")
    people = relationship("Person", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
```

#### Commitment (Unified Model)
```python
class Commitment(Base):
    __tablename__ = "commitments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_description = Column(String, nullable=False)
    original_message = Column(String)  # Source chat message
    
    # Scheduling fields
    deadline = Column(Date)  # For one-time commitments
    recurrence_pattern = Column(String(20), default="none")  # none, daily, weekly, monthly
    recurrence_interval = Column(Integer, default=1)
    recurrence_days = Column(String(50))  # For weekly: "mon,wed,fri"
    recurrence_end_date = Column(Date)
    due_time = Column(Time)  # Optional time for recurring
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, active, completed, dismissed, missed
    completion_count = Column(Integer, default=0)
    last_completed_at = Column(DateTime)
    
    # Metadata
    reminder_settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Computed property
    @property
    def is_recurring(self):
        return self.recurrence_pattern != 'none'
```

#### CommitmentCompletion
```python
class CommitmentCompletion(Base):
    __tablename__ = "commitment_completions"
    
    id = Column(Integer, primary_key=True)
    commitment_id = Column(Integer, ForeignKey('commitments.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    completion_date = Column(Date, nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    skipped = Column(Boolean, default=False)
    notes = Column(String)
```

#### Person
```python
class Person(Base):
    __tablename__ = "people"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    pronouns = Column(String)
    how_you_know_them = Column(String)
    description = Column(Text)  # Markdown supported
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Conversation & Message
```python
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## API Endpoints

### Authentication
- `POST /register` - Create new user account
- `POST /login` - Authenticate and receive JWT token
- `GET /me` - Get current user information

### Commitments
- `GET /commitments` - List with advanced filtering
  - Query params: `status`, `type`, `recurrence`, `due`, `overdue`, `sort_by`, `order`
- `POST /commitments` - Create new commitment
- `GET /commitments/{id}` - Get specific commitment
- `PUT /commitments/{id}` - Update commitment
- `DELETE /commitments/{id}` - Delete commitment
- `POST /commitments/{id}/complete` - Mark complete (handles both types)
- `POST /commitments/{id}/skip` - Skip recurring for today
- `GET /commitments/{id}/completions` - Get completion history

### Analytics
- `GET /analytics/commitments?days={days}` - Commitment analytics
  ```python
  @app.get("/analytics/commitments")
  def get_commitments_analytics(days: int = 30):
      # Returns commitment statistics with daily completion data
      return [
          {
              "commitment_id": id,
              "commitment_name": name,
              "completion_rate": percentage,
              "total_completions": count,
              "is_recurring": boolean,
              "recurrence_pattern": pattern,
              "daily_data": [{"date": date, "completed": count}]
          }
      ]
  ```

- `GET /analytics/overview` - Overall statistics
  ```python
  return {
      "total_commitments": count,
      "recurring_commitments": count,
      "one_time_commitments": count,
      "completed_today": count,
      "completion_rate": percentage,
      "longest_streak": days,
      "total_conversations": count
  }
  ```

- `GET /analytics/mood?days={days}` - Mood analytics (still available but unused in frontend)

### Chat/Conversations
- `GET /conversations` - List user conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}` - Get conversation details
- `POST /conversations/{id}/messages` - Send message
- `GET /conversations/{id}/messages` - Get messages

### People
- `GET /people` - List all people for user
- `POST /people` - Create new person
- `GET /people/{id}` - Get person details
- `PUT /people/{id}` - Update person
- `DELETE /people/{id}` - Delete person

## Services

### ActionProcessor
Handles natural language understanding and intent extraction:

```python
class ActionProcessor:
    def process_message(self, message: str, user_id: int) -> dict:
        # Uses LLM to detect intent and extract entities
        # Supported intents:
        # - create_commitment (with deadline/recurrence detection)
        # - complete_commitment
        # - list_commitments
        # - skip_commitment
        # - update_profile
        # - general_conversation
        
        # Returns structured action data
        return {
            "intent": "create_commitment",
            "entities": {
                "task_description": "...",
                "deadline": "2024-01-15",
                "recurrence_pattern": "daily",
                "due_time": "09:00"
            }
        }
```

### Commitment Logic

#### One-time Commitments
- Created with deadline (optional)
- Status changes: pending → completed/missed
- Single completion changes status permanently

#### Recurring Commitments
- Created with recurrence pattern and optional due_time
- Status remains "active" even after completions
- Each completion creates CommitmentCompletion record
- Supports skipping (creates completion with skipped=True)

#### Completion Handling
```python
@app.post("/commitments/{commitment_id}/complete")
def complete_commitment(commitment_id: int):
    commitment = get_commitment(commitment_id)
    
    if commitment.is_recurring:
        # Create completion record
        completion = CommitmentCompletion(
            commitment_id=commitment_id,
            user_id=current_user.id,
            completion_date=date.today()
        )
        commitment.completion_count += 1
        commitment.last_completed_at = datetime.utcnow()
    else:
        # One-time: just update status
        commitment.status = "completed"
    
    return commitment
```

## Pydantic Schemas

### Commitment Schemas
```python
class CommitmentBase(BaseModel):
    task_description: str
    deadline: Optional[date]
    recurrence_pattern: str = "none"
    recurrence_interval: int = 1
    recurrence_days: Optional[str]
    due_time: Optional[time]
    
class CommitmentCreate(CommitmentBase):
    original_message: Optional[str]
    
class CommitmentUpdate(BaseModel):
    task_description: Optional[str]
    deadline: Optional[date]
    due_time: Optional[time]
    status: Optional[str]
```

### Analytics Schemas
```python
class CommitmentAnalytics(BaseModel):
    commitment_id: int
    commitment_name: str
    completion_rate: float
    total_completions: int
    total_days: int
    is_recurring: bool
    recurrence_pattern: str
    daily_data: List[DailyCompletion]
    
class OverviewAnalytics(BaseModel):
    total_commitments: int
    recurring_commitments: int
    one_time_commitments: int
    completed_today: int
    completion_rate: float
    longest_streak: int
    total_conversations: int
```

### People Schemas
```python
class PersonBase(BaseModel):
    name: str
    pronouns: Optional[str] = None
    how_you_know_them: Optional[str] = None
    description: Optional[str] = None
    
class PersonCreate(PersonBase):
    pass
    
class PersonUpdate(BaseModel):
    name: Optional[str] = None
    pronouns: Optional[str] = None
    how_you_know_them: Optional[str] = None
    description: Optional[str] = None
    
class Person(PersonBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

## Database Migration

### Migration Script (`migrate_habits_to_commitments.py`)
Safe migration from old habits system to unified commitments:

```python
def migrate_habits_to_commitments():
    # 1. Create backup
    backup_database()
    
    # 2. Convert habits to commitments
    for habit in session.query(Habit).all():
        commitment = Commitment(
            user_id=habit.user_id,
            task_description=habit.name,
            recurrence_pattern='daily' if habit.frequency == 'daily' else 'weekly',
            due_time=habit.reminder_time,
            status='active',
            created_at=habit.created_at
        )
        session.add(commitment)
    
    # 3. Convert habit_logs to commitment_completions
    for log in session.query(HabitLog).all():
        completion = CommitmentCompletion(
            commitment_id=mapped_commitment_id,
            user_id=log.user_id,
            completion_date=log.completion_date,
            completed_at=log.completed_at
        )
        session.add(completion)
    
    # 4. Drop old tables (after verification)
    drop_table('habits')
    drop_table('habit_logs')
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@localhost/paa_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
OPENAI_API_KEY=your-api-key  # For LLM integration
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Error Handling
- HTTPException for API errors
- Proper status codes (400, 401, 404, 500)
- Detailed error messages in development
- Generic messages in production

## Security Features
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt for secure password storage
- **User Isolation**: All data properly scoped to authenticated users
- **Input Validation**: Pydantic schemas prevent malformed data
- **SQL Injection Protection**: SQLAlchemy ORM prevents injection attacks

## Performance Optimizations
- **Database Indexing**: Proper indexes on foreign keys and search fields
- **Query Optimization**: Efficient queries with minimal N+1 problems
- **Connection Pooling**: SQLAlchemy connection pool management
- **Async Support**: FastAPI async capabilities for I/O operations

## Testing & Development
- **Health Check**: `GET /health` - Application health status
- **Database Check**: `GET /db-check` - Database connectivity
- **API Documentation**: Auto-generated OpenAPI/Swagger docs at `/docs`
- **Development CORS**: Configured for local frontend development

## Data Relationships
```
User (1) ──────── (M) Commitment
 │                     │
 │                     └── (M) CommitmentCompletion
 │
 ├── (M) Person
 │
 └── (M) Conversation ── (M) Message
```

## Current Status
✅ Unified commitment system implemented  
✅ Chat processing with LLM integration  
✅ Analytics endpoints operational with proper field names  
✅ People management CRUD complete  
✅ JWT authentication working  
✅ Database migration script ready  
✅ All endpoints tested and functional  
✅ Proper error handling and validation  
✅ Security best practices implemented  
✅ API documentation available  
✅ Performance optimizations in place