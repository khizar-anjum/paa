# Proactive AI Assistant (PAA) - Backend Summary

## Overview
FastAPI-based REST API providing authentication, habit tracking, people management, user profiles, AI chat, daily mood check-ins, and comprehensive analytics. Built with SQLAlchemy ORM, JWT authentication, and Anthropic AI integration. Fully functional MVP ready for hackathon demo.

## Tech Stack
- **Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with bcrypt password hashing
- **AI Integration**: Anthropic Claude API with fallback demo responses
- **Validation**: Pydantic schemas

## File Structure

### Core Files
- `main.py` - FastAPI application with all endpoints (550+ lines)
- `database.py` - SQLAlchemy models and database config (7 models)
- `auth.py` - JWT authentication and password management
- `schemas.py` - Pydantic request/response validation
- `requirements.txt` - Python dependencies
- `.env` - Environment configuration
- `paa.db` - SQLite database file

## Database Models

### User Model (`database.py`)
```python
- id: Primary key
- username: Unique username
- email: User email
- hashed_password: Bcrypt hashed password
- created_at: Account creation timestamp
```

### Habit Model (`database.py`)
```python
- id: Primary key
- user_id: Foreign key to User
- name: Habit name
- description: Optional description
- frequency: Daily frequency goal
- reminder_time: Optional reminder time
- is_active: Boolean status (soft delete)
- created_at: Creation timestamp
```

### HabitLog Model (`database.py`)
```python
- id: Primary key
- habit_id: Foreign key to Habit
- completed_at: Completion timestamp
```

### Conversation Model (`database.py`)
```python
- id: Primary key
- user_id: Foreign key to User
- message: User's message
- response: AI's response
- timestamp: Conversation timestamp
```

### DailyCheckIn Model (`database.py`)
```python
- id: Primary key
- user_id: Foreign key to User
- mood: Integer mood score (1-5)
- notes: Optional text notes
- timestamp: Check-in timestamp
```

### Person Model (`database.py`)
```python
- id: Primary key
- user_id: Foreign key to User
- name: Person's name
- how_you_know_them: Relationship context
- pronouns: Person's pronouns
- description: Markdown-compatible description
- created_at: Creation timestamp
- updated_at: Last update timestamp
```

### UserProfile Model (`database.py`)
```python
- id: Primary key
- user_id: Foreign key to User (unique - one profile per user)
- name: User's name
- how_you_know_them: User's background
- pronouns: User's pronouns
- description: Markdown-compatible about section
- created_at: Creation timestamp
- updated_at: Last update timestamp
```

## API Endpoints

### Authentication Endpoints
- `GET /` - Root endpoint (health check)
- `POST /register` - User registration
- `POST /token` - User login (returns JWT token)
- `GET /users/me` - Get current authenticated user

### Habit Management
- `GET /habits` - Get user's active habits with stats (streak, completion status)
- `POST /habits` - Create new habit
- `PUT /habits/{habit_id}` - Update existing habit
- `DELETE /habits/{habit_id}` - Soft delete habit
- `POST /habits/{habit_id}/complete` - Mark habit as completed for today
- `GET /habits/{habit_id}/stats` - Get detailed habit statistics

### AI Chat System
- `POST /chat` - Context-aware AI conversation endpoint
  - Uses conversation history, habit data, and mood context
  - Integrates with Anthropic Claude API
  - Fallback demo responses when API unavailable
- `GET /chat/history` - Get conversation history

### Daily Check-ins
- `POST /checkin/daily` - Record daily mood check-in with notes

### People Management
- `GET /people` - Get user's people with name sorting
- `POST /people` - Create new person
- `GET /people/{person_id}` - Get specific person details
- `PUT /people/{person_id}` - Update existing person
- `DELETE /people/{person_id}` - Delete person

### User Profile
- `GET /profile` - Get user's profile
- `POST /profile` - Create user profile (one per user)
- `PUT /profile` - Update user profile

### Analytics Endpoints
- `GET /analytics/habits` - Habit completion analytics with time range
- `GET /analytics/mood` - Mood trend analytics with daily data
- `GET /analytics/overview` - Dashboard overview statistics

## Advanced Features

### Context-Aware AI Chat
The chat endpoint provides rich context to the AI:
- **Habit Context**: Current habits, completion status, streaks
- **Mood Context**: Recent mood check-ins and notes
- **Conversation History**: Recent chat exchanges
- **Personalized Responses**: Based on user's specific situation

### Analytics System
Comprehensive analytics with time-range filtering:
- **Habit Analytics**: Completion rates, streaks, daily data
- **Mood Analytics**: Trend analysis, averages, daily tracking
- **Overview Statistics**: Real-time dashboard data

### Smart Date Handling
- SQLite-compatible date queries using `func.date()`
- Proper timezone handling for daily operations
- Accurate "today" filtering for check-ins and habits

## Authentication System (`auth.py`)

### Features
- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: 7-day expiration
- **OAuth2 Bearer**: Standard token-based auth
- **Secure Validation**: Token verification and user lookup

### Functions
- `verify_password()` - Check password against hash
- `get_password_hash()` - Hash password with bcrypt
- `create_access_token()` - Generate JWT token
- `get_current_user()` - Validate token and return user

## Pydantic Schemas (`schemas.py`)

### User Schemas
- `UserBase` - Common user fields
- `UserCreate` - Registration data
- `User` - Complete user response

### Habit Schemas
- `HabitBase` - Common habit fields
- `HabitCreate` - Habit creation data
- `Habit` - Complete habit response with stats

### Chat Schemas
- `ChatMessage` - Chat input
- `ChatResponse` - Chat output with context
- `ChatHistory` - Conversation history item

### Check-in Schemas
- `DailyCheckInCreate` - Check-in input (mood + notes)
- `DailyCheckIn` - Check-in response

### Person Schemas
- `PersonBase` - Common person fields
- `PersonCreate` - Person creation data
- `PersonUpdate` - Person update data
- `Person` - Complete person response

### UserProfile Schemas
- `UserProfileBase` - Common profile fields
- `UserProfileCreate` - Profile creation data
- `UserProfileUpdate` - Profile update data (all fields optional)
- `UserProfile` - Complete profile response

### Analytics Schemas
- `HabitAnalytics` - Detailed habit statistics
- `MoodAnalytics` - Mood trend data
- `OverviewAnalytics` - Dashboard overview data

## Database Relationships

```
User (1) ←→ (many) Habit
User (1) ←→ (many) Conversation
User (1) ←→ (many) DailyCheckIn
User (1) ←→ (many) Person
User (1) ←→ (1) UserProfile
Habit (1) ←→ (many) HabitLog
```

## External Integrations

### Database
- **SQLite**: Local database file (`paa.db`)
- **SQLAlchemy**: ORM with session management
- **Auto-creation**: Tables created on startup

### AI Service
- **Anthropic**: Claude AI API client with full context
- **Fallback System**: Demo responses when API unavailable
- **Context Integration**: Habits, moods, and conversation history

### Frontend Integration
- **CORS**: Enabled for Next.js frontend (port 3000)
- **JWT**: Secure token-based authentication
- **JSON**: RESTful JSON API responses

## Security Features

### Authentication
- JWT tokens with 7-day expiration
- Bcrypt password hashing with salt
- OAuth2 bearer token scheme
- Protected endpoint dependencies

### Data Protection
- User-scoped data access (all queries filtered by user_id)
- Foreign key constraints
- Input validation via Pydantic
- Environment variable configuration

## Implementation Status

### Fully Implemented ✅
- **Authentication**: Complete user registration and login system
- **Habit Management**: Full CRUD with completion tracking and streaks
- **People Management**: Full CRUD for relationship management with markdown support
- **User Profiles**: Personal profile system reusing Person schema structure
- **AI Chat**: Context-aware conversations with history
- **Daily Check-ins**: Mood tracking with notes
- **Analytics**: Comprehensive habit and mood analytics
- **Database**: All 7 models and relationships
- **API**: All planned endpoints functional

### Key Fixes Applied ✅
- **Mood Query Fix**: Corrected SQLite date filtering using `func.date()`
- **Context-Aware Chat**: AI now uses full user context
- **Analytics Integration**: Real-time data for dashboard
- **Demo Fallbacks**: Graceful handling when external APIs unavailable

## Dependencies (`requirements.txt`)

### Core Framework
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server

### Database
- `sqlalchemy` - ORM
- `sqlite` - Database (built into Python)

### Authentication
- `python-jose[cryptography]` - JWT handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data

### AI Integration
- `anthropic` - Claude AI client

### Configuration
- `python-dotenv` - Environment variables

## Environment Configuration
- `DATABASE_URL` - Database connection string (defaults to SQLite)
- `SECRET_KEY` - JWT signing key
- `ANTHROPIC_API_KEY` - AI service key (optional with fallbacks)

## API Flow
1. **Request** → FastAPI endpoint (`main.py`)
2. **Auth** → JWT validation (`auth.py`)
3. **Validation** → Pydantic schemas (`schemas.py`)
4. **Database** → SQLAlchemy models (`database.py`)
5. **Response** → JSON via schemas

## Production Readiness
- **MVP Complete**: All core features implemented and tested
- **Error Handling**: Comprehensive try-catch with proper HTTP codes
- **Data Integrity**: Foreign key constraints and validation
- **Scalable Architecture**: Ready for additional features
- **Demo Ready**: Fully functional for hackathon presentation

## Development Notes
- Solid foundation for proactive AI assistant
- Expandable architecture with clean separation
- All planned Phase 4 and Phase 5 features implemented
- Suitable for MVP/hackathon demo
- Ready for production deployment