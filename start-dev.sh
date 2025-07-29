#!/bin/bash

# Personal AI Assistant - Development Startup Script

# Parse arguments
DEBUG_MODE=false
for arg in "$@"; do
    case $arg in
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --debug    Enable comprehensive debug logging"
            echo "  --help     Show this help message"
            echo ""
            echo "Debug mode enables:"
            echo "  • HTTP request/response logging"
            echo "  • Intent classification details"
            echo "  • RAG system context retrieval"
            echo "  • LLM API call monitoring"
            echo "  • Action processor operations"
            echo "  • Vector store operations"
            echo "  • Frontend API call logging"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set environment variables based on debug mode
if [ "$DEBUG_MODE" = true ]; then
    echo "🐛 Starting Personal AI Assistant in DEBUG mode..."
    echo "📊 Debug logging enabled for all components"
    
    # Backend debug environment variables
    export DEBUG_MODE=true
    export LOG_LEVEL=DEBUG
    export DEBUG_HTTP_REQUESTS=true
    export DEBUG_INTENT_CLASSIFICATION=true
    export DEBUG_RAG_SYSTEM=true
    export DEBUG_LLM_CALLS=true
    export DEBUG_ACTION_PROCESSOR=true
    export DEBUG_VECTOR_STORE=true
    export DEBUG_LOG_TO_FILE=false
    
    # Frontend debug environment variables
    export NEXT_PUBLIC_DEBUG_MODE=true
    export NEXT_PUBLIC_DEBUG_API_CALLS=true
else
    echo "🚀 Starting Personal AI Assistant in PRODUCTION mode..."
    
    # Ensure debug mode is off
    export DEBUG_MODE=false
    export NEXT_PUBLIC_DEBUG_MODE=false
fi

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