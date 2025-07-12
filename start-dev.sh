#!/bin/bash

# Personal AI Assistant - Development Startup Script
echo "🚀 Starting Personal AI Assistant Development Environment..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    jobs -p | xargs -r kill
    exit
}

# Set up cleanup trap
trap cleanup SIGINT SIGTERM

# Start Backend Server
echo "📡 Starting Backend Server (FastAPI)..."
cd paa-backend
source venv/bin/activate &
(source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start Frontend Server
echo "🌐 Starting Frontend Server (Next.js)..."
cd paa-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Development environment started!"
echo "📡 Backend API: http://localhost:8000"
echo "🌐 Frontend App: http://localhost:3000"
echo "📋 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for background processes
wait