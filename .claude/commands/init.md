# Personal AI Assistant (PAA) - Project Initialization

## Project Overview
You are working with a **Personal AI Assistant (PAA)** that is **proactive and persistent**. This is a full-stack application designed to help users manage their daily habits, track their mood, and receive intelligent assistance from an AI companion.

## Core Concept
The Personal AI Assistant is designed to:
- Proactively engage with users (not wait for prompts)
- Persist in following up even when users don't respond immediately
- Understand busy people need intelligent, contextual assistance
- Maintain deep understanding of user's life through habits, mood, and conversations

## Required Reading
Before proceeding with any development tasks, you MUST read these documents:

1. **context/summaries/project-summary.md** - Complete project overview
2. **context/summaries/frontend-summary.md** - Frontend codebase details
3. **context/summaries/backend-summary.md** - Backend API and database structure
4. **context/designs/personal-ai-assistant-design.md** - Original comprehensive design vision

## Technical Architecture
- **Backend**: FastAPI with SQLAlchemy ORM, SQLite database, JWT authentication
- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, Split-screen persistent chat
- **AI Integration**: Anthropic Claude API for context-aware conversations
- **Real-time Features**: Live analytics, immediate habit updates, proactive messaging

## Key Features
1. **User Authentication** - Secure JWT-based login/register system
2. **Habit Tracking** - Full CRUD operations with streak tracking and completion analytics
3. **AI Chat** - Context-aware conversations with persistent interface (55% of screen)
4. **Daily Check-ins** - Smart mood tracking with 5-point emoji scale
5. **Analytics Dashboard** - Real-time charts showing habits and mood trends
6. **People Management** - Track relationships with markdown-supported profiles
7. **User Profiles** - Personal profile system with markdown support
8. **Proactive Features** - Time-based scheduling and commitment tracking

## Project Structure
```
paa/
├── paa-backend/         # FastAPI backend
│   ├── main.py         # All API endpoints
│   ├── database.py     # SQLAlchemy models
│   ├── auth.py         # JWT authentication
│   ├── schemas.py      # Pydantic validation
│   └── services/       # Proactive features
├── paa-frontend/        # Next.js frontend
│   ├── app/            # App router pages
│   ├── components/     # React components
│   └── lib/            # API services
└── context/            # Documentation
    ├── designs/        # Architecture docs
    ├── summaries/      # Codebase summaries
    └── plans/          # Implementation guides
```

## Development Guidelines
- **Code Quality**: Follow existing patterns and conventions in the codebase
- **Security**: All data is user-scoped with proper authentication
- **User Experience**: Maintain the innovative split-screen chat interface
- **Real-time Updates**: Ensure immediate UI updates after user actions
- **Error Handling**: Comprehensive error states with user-friendly messages

## Implementation Resources
- Detailed implementation plans exist in the `context/plans/` directory
- Reference these only when specifically requested by the user
- The codebase is production-ready with all core features implemented

## Important Notes
- The backend server runs on port 8000 and frontend on port 3000
- Python virtual environment is located at `paa-backend/venv`
- All features are fully functional and tested
- Focus on maintaining the proactive, persistent AI assistant concept

## AFTER READING THE REQUIRED DOCUMENTS, WAIT FOR USER COMMAND. DO NOT PROCEED WITH ANY ACTIONS UNTIL INSTRUCTED!