# Personal AI Assistant (PAA) - Backend Summary

## Overview
FastAPI-based REST API providing authentication, habit tracking, AI chat, and mood check-in functionality. Built with SQLAlchemy ORM, JWT authentication, and Anthropic AI integration.

## Tech Stack
- **Framework**: FastAPI
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with bcrypt password hashing
- **AI Integration**: Anthropic Claude API
- **Validation**: Pydantic schemas

## File Structure

### Core Files
- `main.py` - FastAPI application with all endpoints
- `database.py` - SQLAlchemy models and database config
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
- is_active: Boolean status
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

## API Endpoints

### Authentication Endpoints
- `GET /` - Root endpoint (health check)
- `POST /register` - User registration
- `POST /token` - User login (returns JWT token)
- `GET /users/me` - Get current authenticated user

### Habit Management
- `GET /habits` - Get user's active habits
- `POST /habits` - Create new habit

### AI Chat
- `POST /chat` - AI conversation endpoint

### Daily Check-ins
- `POST /checkin/daily` - Record daily mood check-in

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
- `Habit` - Complete habit response

### Chat Schemas
- `ChatMessage` - Chat input
- `ChatResponse` - Chat output

### Check-in Schemas
- `DailyCheckInCreate` - Check-in input
- `DailyCheckIn` - Check-in response

### Analytics Schemas (Defined, Not Implemented)
- `HabitAnalytics` - Habit statistics
- `MoodAnalytics` - Mood trends

## Database Relationships

```
User (1) ←→ (many) Habit
User (1) ←→ (many) Conversation
User (1) ←→ (many) DailyCheckIn
Habit (1) ←→ (many) HabitLog
```

## External Integrations

### Database
- **SQLite**: Local database file (`paa.db`)
- **SQLAlchemy**: ORM with session management
- **Auto-creation**: Tables created on startup

### AI Service
- **Anthropic**: Claude AI API client
- **Integration**: Chat endpoint uses Claude for responses
- **Context**: Basic user context in conversations

### Frontend Integration
- **CORS**: Enabled for Next.js frontend (port 3000)
- **JWT**: Secure token-based authentication
- **JSON**: RESTful JSON API responses

## Security Features

### Authentication
- JWT tokens with expiration
- Bcrypt password hashing
- OAuth2 bearer token scheme
- Protected endpoint dependencies

### Data Protection
- User-scoped data access
- Foreign key constraints
- Input validation via Pydantic
- Environment variable configuration

## Current Implementation Status

### Fully Implemented ✅
- User registration and authentication
- JWT token system
- Habit creation and retrieval
- Basic AI chat functionality
- Daily mood check-ins
- Database models and relationships
- CORS configuration

### Partially Implemented ⚠️
- AI chat (basic response, limited Anthropic integration)
- Analytics schemas (defined but no endpoints)

### Missing Features ⏳
- Habit completion logging endpoints
- Advanced analytics and reporting
- Habit streak calculations
- Notification system
- Enhanced AI personalization
- Data export/import

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
- `pydantic-settings` - Settings management

### Additional
- `schedule` - Task scheduling (imported, not used)

## Environment Configuration
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT signing key
- `ANTHROPIC_API_KEY` - AI service key

## API Flow
1. **Request** → FastAPI endpoint (`main.py`)
2. **Auth** → JWT validation (`auth.py`)
3. **Validation** → Pydantic schemas (`schemas.py`)
4. **Database** → SQLAlchemy models (`database.py`)
5. **Response** → JSON via schemas

## Development Notes
- Solid foundation for personal AI assistant
- Expandable architecture
- Ready for additional features
- Suitable for MVP/hackathon demo