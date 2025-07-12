# Personal AI Assistant - Hackathon Architecture (MVP)

## Overview
Simplified architecture focused on rapid development and impressive demo capabilities for a hackathon setting.

## Tech Stack (Quick Setup)

### Backend (Single Service)
- **Framework**: FastAPI (Python) - fast to develop, automatic API docs
- **Database**: SQLite - zero config, file-based
- **Auth**: Simple JWT with python-jose - no external services needed
- **AI**: OpenAI API or Anthropic Claude API - instant integration

### Frontend
- **Web Dashboard**: Next.js with Tailwind CSS - full-stack framework, easy deployment
- **Chat Interface**: Embedded in web app initially (can be separated later)

## Simplified Architecture

```
┌─────────────────┐     ┌──────────────────┐
│   Next.js App   │────▶│  FastAPI Backend │
│  (Dashboard +   │     │   (All-in-One)   │
│     Chat)       │     └──────────────────┘
└─────────────────┘              │
                                 ▼
                          ┌─────────────┐
                          │   SQLite    │
                          │  Database   │
                          └─────────────┘
```

## Quick Implementation Plan

### 1. Backend Setup (2-3 hours)

```python
# main.py - Single file to start
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from anthropic import Anthropic

app = FastAPI()

# Simple SQLite setup
DATABASE_URL = "sqlite:///./paa.db"

# Models
class User(BaseModel):
    username: str
    email: str
    password: str

class Habit(BaseModel):
    name: str
    frequency: str
    reminder_time: str

class ChatMessage(BaseModel):
    message: str
    
# Core endpoints
@app.post("/register")
@app.post("/login")
@app.get("/habits")
@app.post("/habits")
@app.post("/chat")
@app.get("/analytics/simple")
@app.post("/checkin/daily")
```

### 2. Database Schema (SQLite)

```sql
-- Minimal tables for demo
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP
);

CREATE TABLE habits (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    name TEXT,
    frequency TEXT,
    reminder_time TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE habit_logs (
    id INTEGER PRIMARY KEY,
    habit_id INTEGER,
    completed_at TIMESTAMP,
    FOREIGN KEY (habit_id) REFERENCES habits(id)
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    message TEXT,
    response TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE daily_checkins (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    mood TEXT,
    notes TEXT,
    timestamp TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3. Frontend Setup (2-3 hours)

```bash
# Quick Next.js setup
npx create-next-app@latest paa-frontend --typescript --tailwind --app
cd paa-frontend
npm install axios recharts lucide-react
```

#### Key Pages:
- `/login` - Simple login form
- `/dashboard` - Main hub with habits, analytics, chat
- `/api/*` - API routes if needed

### 4. MVP Features for Demo

#### A. User Authentication (30 mins)
- Simple email/password registration
- JWT tokens stored in localStorage
- Basic protected routes

#### B. Habit Tracking (1 hour)
- Add habits with daily/weekly frequency
- Simple "Mark as Done" button
- Basic streak counter

#### C. AI Chat (1 hour)
- Embedded chat widget in dashboard
- Claude/OpenAI integration
- Conversation history in sidebar

#### D. Daily Check-in (30 mins)
- Simple modal at login: "How was your day?"
- 1-5 mood scale + optional text
- Store in database

#### E. Basic Analytics (1 hour)
- Habit completion chart (last 7 days)
- Mood trend line
- Simple stats cards

## Deployment for Demo

### Option 1: Local Demo (Easiest)
```bash
# Backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
npm run dev
```

### Option 2: Quick Cloud Deploy
- Backend: Railway.app or Render.com (1-click deploy)
- Frontend: Vercel (auto-deploys from GitHub)
- Database: SQLite file included in backend deployment

### Option 3: Single Machine
- Use Docker Compose for both services
- ngrok for public URL if needed

## Demo Script

1. **Registration Flow** (30 seconds)
   - Quick sign up
   - Show personalized dashboard

2. **Add Habits** (1 minute)
   - Create "Morning Meditation" habit
   - Set reminder for 7 AM
   - Show habit card on dashboard

3. **AI Chat Demo** (2 minutes)
   - "Help me stay motivated with my meditation"
   - Show AI understanding context
   - "What should I focus on today?"

4. **Daily Check-in** (30 seconds)
   - Quick mood selection
   - AI responds based on mood

5. **Analytics** (30 seconds)
   - Show habit completion graph
   - Mood trend over past week

## Code Structure

```
paa-hackathon/
├── backend/
│   ├── main.py          # All backend code
│   ├── requirements.txt # fastapi, sqlalchemy, anthropic
│   └── paa.db          # SQLite database
├── frontend/
│   ├── app/
│   │   ├── login/page.tsx
│   │   ├── dashboard/page.tsx
│   │   └── components/
│   │       ├── ChatWidget.tsx
│   │       ├── HabitCard.tsx
│   │       └── Analytics.tsx
│   └── package.json
└── README.md
```

## Time Allocation (8-10 hours)

1. **Hours 0-2**: Backend setup + Auth
2. **Hours 2-4**: Frontend skeleton + Auth UI
3. **Hours 4-5**: Habit management
4. **Hours 5-6**: AI Chat integration
5. **Hours 6-7**: Daily check-in + Analytics
6. **Hours 7-8**: Polish UI + Bug fixes
7. **Hours 8-10**: Demo prep + Deployment

## Impressive Demo Features

1. **Real-time Updates**: Use React Query for instant UI updates
2. **AI Personality**: Give the AI a friendly name and personality
3. **Beautiful UI**: Use Tailwind UI components for polished look
4. **Mobile Responsive**: Ensure it works on phones for judges
5. **Sample Data**: Pre-populate with realistic habits and history

## Shortcuts for Speed

1. **No Email Verification**: Just store emails
2. **Simple Password**: No complex requirements
3. **In-Memory Scheduler**: Use Python's `schedule` library
4. **Fake Analytics**: Pre-generate some data if needed
5. **Single User Focus**: Perfect the experience for one demo user

## Libraries to Speed Development

### Backend
```txt
fastapi
uvicorn
sqlalchemy
python-jose[cryptography]
anthropic
python-multipart
schedule
```

### Frontend
```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "recharts": "^2.10.0",
    "lucide-react": "^0.300.0",
    "@tanstack/react-query": "^5.0.0",
    "sonner": "^1.2.0"
  }
}
```

This architecture can be built in a day and provides all the core functionality for an impressive hackathon demo!