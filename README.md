# Ally - Your Proactive AI Assistant 🤖

Meet Ally, a revolutionary proactive AI assistant that actively helps you build better habits, track your mood, and achieve your goals. Unlike traditional apps that wait for you to engage, Ally actively reaches out with personalized reminders and insights.

![Proactive AI Assistant](https://img.shields.io/badge/Status-MVP%20Ready-brightgreen) ![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%2B%20Next.js-blue) ![License](https://img.shields.io/badge/License-MIT-orange)

## 🌟 What Makes Ally Different

**Proactive, Not Reactive**: Ally doesn't wait for you to open the app. She intelligently reaches out based on your patterns and needs.

**Always Present**: Ally is always visible alongside your activities - a true digital companion.

**Context-Aware**: Ally remembers your habits, understands your mood patterns, and provides personalized guidance based on your unique situation.

## ✨ Key Features

- **🎯 Smart Habit Tracking**: Create habits with intelligent reminders and streak tracking
- **💬 Chat with Ally**: Always-visible AI assistant that knows your context
- **😊 Daily Mood Check-ins**: Track emotional wellness with smart once-daily prompts
- **📊 Real-time Analytics**: Visualize your progress with beautiful charts
- **👥 People Management**: Keep track of important relationships
- **👤 Personal Profile**: Maintain your personal context so Ally can better assist you

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/paa.git
   cd paa
   ```

2. **Quick Start (Recommended)**
   ```bash
   # Make the script executable (first time only)
   chmod +x start-dev.sh
   
   # Run both servers with one command
   ./start-dev.sh
   ```
   This will automatically start both the backend and frontend servers.

3. **Manual Setup** (Alternative)
   
   **Backend Setup:**
   ```bash
   cd paa-backend
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Create .env file
   echo "SECRET_KEY=your-secret-key-here" > .env
   echo "ANTHROPIC_API_KEY=your-anthropic-api-key-here" >> .env
   
   # Run the backend server
   uvicorn main:app --reload --port 8000
   ```

   **Frontend Setup** (in a new terminal):
   ```bash
   cd paa-frontend
   
   # Install dependencies
   npm install
   
   # Run the development server
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API docs: http://localhost:8000/docs

## 🎯 Getting Started

1. **Create an Account**: Visit http://localhost:3000/register to sign up
2. **Complete Your Profile**: Add personal context to help Ally understand you better
3. **Add Your First Habit**: Start with one simple daily habit
4. **Chat with Ally**: She's always there in the right panel, ready to help
5. **Track Your Mood**: Complete daily check-ins to monitor emotional wellness
6. **View Analytics**: See your progress visualized in real-time

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **AI**: Anthropic Claude API
- **Authentication**: JWT with secure token management

## 📱 Features Walkthrough

### Habit Management
Create habits with customizable frequencies and reminder times. Track your streaks and see completion rates at a glance.

### Chat with Ally
Ally is your persistent AI assistant who:
- Knows your habits and current progress
- Understands your mood patterns
- Provides personalized encouragement and advice
- Remembers past conversations for context

### Daily Check-ins
Smart mood tracking that:
- Prompts once daily (respects your time)
- Uses emoji-based 1-5 scale
- Allows optional notes
- Feeds into AI context for better support

### Analytics Dashboard
Real-time insights including:
- Habit completion rates
- Mood trends over time
- Personal statistics
- Progress visualization

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-api-key-here  # Optional - has fallback
DATABASE_URL=sqlite:///./paa.db      # Default SQLite
```

**Frontend**
The frontend automatically connects to the backend at http://localhost:8000

## 🤝 Contributing

We welcome contributions! Please feel free to submit issues and pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for hackathon demonstration
- Inspired by the need for proactive AI assistants
- Designed for busy individuals who need intelligent life management

---

**Remember**: Ally is more than an app - she's your proactive AI assistant for personal growth! 🌱
