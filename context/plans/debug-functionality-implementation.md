# Debug Functionality Implementation Plan

## Overview
Implement comprehensive debug functionality for the Personal AI Assistant (PAA) that can be activated via `--debug` argument in the startup script. This will provide detailed logging and inspection capabilities across the entire application stack.

## Goals
- Enable detailed logging of HTTP requests/responses
- Track intent classification decisions
- Monitor RAG system context retrieval
- Log LLM API calls and responses
- Monitor action processor operations
- Track vector store operations
- Provide frontend API call logging
- Create debug UI indicators

## Implementation Strategy

### Phase 1: Core Debug Infrastructure

#### 1.1 Environment Variables & Configuration
**Files to modify:**
- `paa-backend/.env`
- `paa-frontend/.env.local`

**Changes:**
```bash
# Backend .env additions
DEBUG_MODE=false
LOG_LEVEL=INFO
DEBUG_HTTP_REQUESTS=false
DEBUG_INTENT_CLASSIFICATION=false
DEBUG_RAG_SYSTEM=false
DEBUG_LLM_CALLS=false
DEBUG_ACTION_PROCESSOR=false
DEBUG_VECTOR_STORE=false

# Frontend .env.local additions
NEXT_PUBLIC_DEBUG_MODE=false
NEXT_PUBLIC_DEBUG_API_CALLS=false
```

#### 1.2 Debug Logger Configuration
**New file:** `paa-backend/debug_logger.py`

Features:
- Centralized debug logging configuration
- Color-coded log levels for terminal output
- Structured logging for different components
- Environment-based log level control
- Optional file output for debug sessions

```python
import logging
import os
from datetime import datetime
from typing import Dict, Any

class DebugLogger:
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.setup_logging()
    
    def setup_logging(self):
        # Configure formatters, handlers, and loggers
        pass
    
    def log_http_request(self, method: str, path: str, body: Dict[Any, Any]):
        # Log incoming HTTP requests
        pass
    
    def log_intent_classification(self, message: str, intent: Dict[str, Any]):
        # Log intent classification results
        pass
    
    # ... other specialized logging methods
```

#### 1.3 Startup Script Enhancement
**File to modify:** `start-dev.sh`

**Changes:**
```bash
#!/bin/bash

# Parse arguments
DEBUG_MODE=false
for arg in "$@"; do
    case $arg in
        --debug)
            DEBUG_MODE=true
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Set environment variables based on debug mode
if [ "$DEBUG_MODE" = true ]; then
    echo "🐛 Starting in DEBUG mode..."
    export DEBUG_MODE=true
    export LOG_LEVEL=DEBUG
    export DEBUG_HTTP_REQUESTS=true
    export DEBUG_INTENT_CLASSIFICATION=true
    export DEBUG_RAG_SYSTEM=true
    export DEBUG_LLM_CALLS=true
    export DEBUG_ACTION_PROCESSOR=true
    export DEBUG_VECTOR_STORE=true
    export NEXT_PUBLIC_DEBUG_MODE=true
    export NEXT_PUBLIC_DEBUG_API_CALLS=true
else
    echo "🚀 Starting in PRODUCTION mode..."
fi

# Rest of startup script remains the same...
```

### Phase 2: Backend Debug Implementation

#### 2.1 HTTP Request/Response Logging
**File to modify:** `paa-backend/main.py`

**Changes:**
- Add debug middleware for request/response logging
- Log request method, path, headers, body
- Log response status, headers, body
- Measure and log response times

```python
from debug_logger import DebugLogger
import time

debug_logger = DebugLogger()

@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    if debug_logger.debug_mode and os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true":
        start_time = time.time()
        
        # Log request
        body = await request.body()
        debug_logger.log_http_request(
            method=request.method,
            path=request.url.path,
            headers=dict(request.headers),
            body=body.decode() if body else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        debug_logger.log_http_response(
            status_code=response.status_code,
            process_time=process_time,
            headers=dict(response.headers)
        )
    else:
        response = await call_next(request)
    
    return response
```

#### 2.2 Intent Classification Debug Logging
**File to modify:** `paa-backend/services/intent_classifier.py`

**Changes:**
```python
from debug_logger import DebugLogger
import os

debug_logger = DebugLogger()

class IntentClassifier:
    def classify_intent(self, message: str) -> MessageIntent:
        # Existing classification logic...
        
        if os.getenv("DEBUG_INTENT_CLASSIFICATION", "false").lower() == "true":
            debug_logger.log_intent_classification(
                message=message,
                intent={
                    "primary_intent": intent.primary_intent,
                    "confidence": intent.confidence,
                    "entities": intent.entities,
                    "reasoning": "Pattern matches and scoring details"
                }
            )
        
        return intent
```

#### 2.3 RAG System Debug Logging
**File to modify:** `paa-backend/services/rag_system.py`

**Changes:**
```python
def retrieve_context(self, intent: MessageIntent, user_id: int) -> EnhancedContext:
    if os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true":
        debug_logger.log_rag_retrieval_start(intent, user_id)
    
    # Existing retrieval logic...
    
    if os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true":
        debug_logger.log_rag_retrieval_result(
            context_sources=["conversations", "habits", "people"],
            similarity_scores=[0.8, 0.7, 0.6],
            retrieved_items=len(context.conversations) + len(context.habits),
            processing_time=processing_time
        )
    
    return context
```

#### 2.4 LLM Processor Debug Logging
**File to modify:** `paa-backend/services/llm_processor.py`

**Changes:**
```python
async def process_message(self, message: str, context: EnhancedContext, intent: MessageIntent) -> StructuredAIResponse:
    if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
        debug_logger.log_llm_call_start(
            message=message,
            context_summary={
                "conversations": len(context.conversations),
                "habits": len(context.habits),
                "people": len(context.people)
            },
            intent=intent.primary_intent
        )
    
    # Build prompt and make API call...
    
    if os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true":
        debug_logger.log_llm_call_result(
            prompt_length=len(prompt),
            response_length=len(response_text),
            api_call_time=api_time,
            tokens_used=tokens_estimate,
            structured_output=structured_response.dict()
        )
    
    return structured_response
```

#### 2.5 Action Processor Debug Logging
**File to modify:** `paa-backend/services/action_processor.py`

**Changes:**
```python
async def process_actions(self, ai_response: StructuredAIResponse, user_id: int) -> Dict[str, Any]:
    if os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true":
        debug_logger.log_action_processing_start(
            commitments_count=len(ai_response.commitments),
            habit_actions_count=len(ai_response.habit_actions),
            people_updates_count=len(ai_response.people_updates),
            scheduled_actions_count=len(ai_response.scheduled_actions)
        )
    
    # Process each type of action...
    
    if os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true":
        debug_logger.log_action_processing_result(
            executed_actions=executed_actions,
            failed_actions=failed_actions,
            database_changes=database_changes
        )
    
    return results
```

#### 2.6 Vector Store Debug Logging
**File to modify:** `paa-backend/services/vector_store.py`

**Changes:**
```python
def search_conversations(self, query: str, user_id: int, limit: int = 5) -> List[Dict]:
    if os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true":
        debug_logger.log_vector_search_start(
            collection="conversations",
            query=query,
            user_id=user_id,
            limit=limit
        )
    
    # Perform search...
    
    if os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true":
        debug_logger.log_vector_search_result(
            results_count=len(results),
            similarity_scores=[r['score'] for r in results],
            search_time=search_time
        )
    
    return results
```

### Phase 3: Frontend Debug Implementation

#### 3.1 API Call Logging Enhancement
**Files to modify:**
- `paa-frontend/lib/api/chat.ts`
- `paa-frontend/lib/api/habits.ts`
- `paa-frontend/lib/api/analytics.ts`
- `paa-frontend/lib/api/people.ts`
- `paa-frontend/lib/api/profile.ts`

**Changes:** Add debug logging wrapper for axios calls:

```typescript
// Create debug wrapper utility
// paa-frontend/lib/debug-utils.ts
export class FrontendDebugLogger {
  private debugMode: boolean;
  
  constructor() {
    this.debugMode = process.env.NEXT_PUBLIC_DEBUG_MODE === 'true';
  }
  
  logApiCall(method: string, url: string, data?: any) {
    if (this.debugMode && process.env.NEXT_PUBLIC_DEBUG_API_CALLS === 'true') {
      console.group(`🔵 API Call: ${method.toUpperCase()} ${url}`);
      console.log('Timestamp:', new Date().toISOString());
      if (data) console.log('Request Data:', data);
      console.groupEnd();
    }
  }
  
  logApiResponse(method: string, url: string, response: any, duration: number) {
    if (this.debugMode && process.env.NEXT_PUBLIC_DEBUG_API_CALLS === 'true') {
      console.group(`🟢 API Response: ${method.toUpperCase()} ${url}`);
      console.log('Duration:', `${duration}ms`);
      console.log('Status:', response.status);
      console.log('Data:', response.data);
      console.groupEnd();
    }
  }
  
  logApiError(method: string, url: string, error: any, duration: number) {
    if (this.debugMode && process.env.NEXT_PUBLIC_DEBUG_API_CALLS === 'true') {
      console.group(`🔴 API Error: ${method.toUpperCase()} ${url}`);
      console.log('Duration:', `${duration}ms`);
      console.log('Error:', error);
      console.groupEnd();
    }
  }
}

export const debugLogger = new FrontendDebugLogger();
```

**Enhanced API calls example (chat.ts):**
```typescript
import { debugLogger } from '../debug-utils';

export const chatApi = {
  sendMessage: async (message: string): Promise<ChatResponse> => {
    const startTime = Date.now();
    const url = '/chat/enhanced';
    
    debugLogger.logApiCall('POST', url, { message });
    
    try {
      const response = await axios.post(url, { message });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse('POST', url, response, duration);
      return response.data;
    } catch (error) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError('POST', url, error, duration);
      throw error;
    }
  },
  
  // Similar enhancements for other methods...
};
```

#### 3.2 Debug Panel Component
**New file:** `paa-frontend/app/components/DebugPanel.tsx`

Features:
- Toggle debug mode on/off
- Real-time display of recent API calls
- System status indicators
- Performance metrics
- Debug log export functionality

```tsx
'use client';

import React, { useState, useEffect } from 'react';
import { debugLogger } from '../../lib/debug-utils';

export default function DebugPanel() {
  const [isVisible, setIsVisible] = useState(false);
  const [debugMode, setDebugMode] = useState(false);
  const [apiCalls, setApiCalls] = useState([]);
  
  // Only show debug panel if environment allows it
  useEffect(() => {
    setDebugMode(process.env.NEXT_PUBLIC_DEBUG_MODE === 'true');
  }, []);
  
  if (!debugMode) return null;
  
  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Debug toggle button */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="bg-purple-600 text-white p-2 rounded-full shadow-lg"
        title="Toggle Debug Panel"
      >
        🐛
      </button>
      
      {/* Debug panel */}
      {isVisible && (
        <div className="absolute bottom-12 right-0 bg-gray-900 text-green-400 p-4 rounded-lg shadow-xl w-96 max-h-96 overflow-y-auto font-mono text-xs">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-white font-bold">Debug Panel</h3>
            <button
              onClick={() => setIsVisible(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          
          {/* System status */}
          <div className="mb-4">
            <h4 className="text-yellow-400 mb-1">System Status</h4>
            <div>Debug Mode: ✅ Active</div>
            <div>API Logging: ✅ Active</div>
          </div>
          
          {/* Recent API calls */}
          <div>
            <h4 className="text-yellow-400 mb-1">Recent API Calls</h4>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {/* API call entries */}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

#### 3.3 Integration with Dashboard Layout
**File to modify:** `paa-frontend/app/dashboard/layout.tsx`

**Changes:**
```tsx
import DebugPanel from '../components/DebugPanel';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Existing layout content */}
      
      {/* Debug panel - only shows in debug mode */}
      <DebugPanel />
    </div>
  );
}
```

### Phase 4: Enhanced Debug Endpoints

#### 4.1 Backend Debug Endpoints
**File to modify:** `paa-backend/main.py`

**New endpoints:**
```python
@app.get("/debug/status")
async def debug_status():
    """Get current debug configuration status"""
    return {
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "debug_features": {
            "http_requests": os.getenv("DEBUG_HTTP_REQUESTS", "false").lower() == "true",
            "intent_classification": os.getenv("DEBUG_INTENT_CLASSIFICATION", "false").lower() == "true",
            "rag_system": os.getenv("DEBUG_RAG_SYSTEM", "false").lower() == "true",
            "llm_calls": os.getenv("DEBUG_LLM_CALLS", "false").lower() == "true",
            "action_processor": os.getenv("DEBUG_ACTION_PROCESSOR", "false").lower() == "true",
            "vector_store": os.getenv("DEBUG_VECTOR_STORE", "false").lower() == "true"
        }
    }

@app.get("/debug/pipeline/last-execution")
async def get_last_pipeline_execution():
    """Get detailed info about the last pipeline execution"""
    # Return cached pipeline execution details
    pass

@app.get("/debug/vector-store/stats")
async def get_vector_store_stats():
    """Get vector store collection statistics"""
    # Return collection counts, recent operations, etc.
    pass
```

#### 4.2 Enhanced Debug API Frontend
**File to enhance:** `paa-frontend/lib/api/debug.ts`

**Additional methods:**
```typescript
class DebugApi {
  // Existing time control methods...
  
  async getDebugStatus(): Promise<DebugStatusResponse> {
    const response = await fetch(`${API_URL}/debug/status`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }
  
  async getLastPipelineExecution(): Promise<PipelineExecutionResponse> {
    const response = await fetch(`${API_URL}/debug/pipeline/last-execution`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }
  
  async getVectorStoreStats(): Promise<VectorStoreStatsResponse> {
    const response = await fetch(`${API_URL}/debug/vector-store/stats`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }
}
```

### Phase 5: Debug Output Enhancement

#### 5.1 Terminal Output Formatting
**Enhance:** `paa-backend/debug_logger.py`

Features:
- Color-coded log output for easy reading
- Structured formatting for different log types
- Progress indicators for long operations
- Summary statistics at the end of operations

#### 5.2 Debug Log File Output
**Optional feature:** Write debug logs to files when in debug mode

```python
class DebugLogger:
    def __init__(self):
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.log_to_file = os.getenv("DEBUG_LOG_TO_FILE", "false").lower() == "true"
        
        if self.log_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file = f"debug_session_{timestamp}.log"
```

## Implementation Timeline

### ✅ Phase 1: Core Infrastructure (COMPLETED)
- [x] Set up debug logger and environment variables
- [x] Modify startup script with --debug argument
- [x] Implement centralized debug logger with color-coded output

**Summary**: Created comprehensive debug infrastructure with environment variable controls, enhanced startup script with `--debug` argument, and implemented centralized `debug_logger.py` with color-coded terminal output and structured logging for all components.

### ✅ Phase 2: Backend Debug Integration (COMPLETED)
- [x] Add HTTP request/response logging middleware
- [x] Add intent classification debug logging
- [x] Implement RAG system debug logging  
- [x] Add LLM processor debug logging
- [x] Add action processor debug logging
- [x] Implement vector store debug logging

**Summary**: Integrated debug logging throughout the entire backend pipeline. Added middleware for HTTP request/response monitoring, detailed logging for intent classification decisions, RAG context retrieval tracking, LLM API call monitoring with token estimates, action processor execution tracking, and comprehensive vector store operation logging with timing and similarity scores.

### ✅ Phase 3: Frontend Debug + API Integration (COMPLETED)
- [x] Create frontend debug utilities and API call logging
- [x] Enhance existing API service files with debug logging
- [x] Add debug endpoints to backend
- [x] Integrate pipeline execution tracking

**Summary**: Implemented comprehensive frontend debug logging system with color-coded console output, enhanced all API service files (chat, habits, analytics, people) with detailed request/response logging, added new debug endpoints for system status and pipeline monitoring, and integrated end-to-end pipeline execution tracking. Frontend now provides rich debugging information in browser console when debug mode is enabled.

## Usage Examples

### Basic Debug Mode
```bash
./start-dev.sh --debug
```

### Expected Debug Output

**Backend Terminal:**
```
🐛 Starting Personal AI Assistant in DEBUG mode...
📊 Debug logging enabled for all components

🚀 Pipeline Execution Started: exec_143052_567890
   User: 1 | Message: "I worked out today"

🎯 Intent Classification:
   Intent: habit_tracking
   Confidence: 0.95
   Entities: {"habits": ["workout"], "time_references": ["today"]}

🔍 RAG Retrieval Started:
   User: 1 | Intent: habit_tracking
✅ RAG Retrieved: 5 items (120ms)
   Sources: conversations, habits
   Avg Similarity: 0.847

🤖 LLM Processing Started:
   Intent: habit_tracking
   Context: {"conversations": 2, "habits": 3, "people": 0}
✅ LLM Response: 245 chars, ~89 tokens (450ms)
   Actions: 0 commitments, 1 habits, 0 people

⚡ Action Processing Started:
   0 commitments, 1 habit actions, 0 people updates
✅ Actions Processed: 1 executed, 0 failed
   DB Changes: 1 habit_logs

🏁 Pipeline Execution Completed: ✅ SUCCESS (1205ms)
```

**Frontend Browser Console:**
```
🐛 Frontend Debug Mode Enabled
Features enabled:
  • API Call Logging: ✅ ON

🚀 AI Pipeline Started
Endpoint: /chat/enhanced
Message: "I worked out today"

🔵 API Call: POST /chat/enhanced
Call ID: api_1640995200000_abc123xyz
Request Data: {message: "I worked out today"}

🟢 API Response: POST /chat/enhanced
Duration: 1205ms
Status: 200
Response Data: {message: "Great job working out! I've logged that for you.", ...}

🏁 AI Pipeline Completed: ✅ SUCCESS (1205ms)
```

### New Debug Endpoints
- `GET /debug/status` - Get debug configuration status
- `GET /debug/pipeline/recent-executions` - View recent pipeline executions
- `GET /debug/vector-store/stats` - Vector database statistics
- `POST /debug/clear-logs` - Clear debug execution history

## Benefits

1. **Development Speed**: Faster debugging and issue resolution
2. **System Understanding**: Clear visibility into AI pipeline operations
3. **Performance Monitoring**: Identify bottlenecks and optimization opportunities
4. **User Support**: Better troubleshooting capabilities
5. **Feature Development**: Easier testing of new AI features

## Security Considerations

- Debug mode disabled by default in production
- Sensitive data (API keys, passwords) never logged
- Debug logs can be configured to exclude personal information
- Debug endpoints protected by authentication
- Environment-based feature toggles

## Testing Strategy

1. **Unit Tests**: Test debug logging functions
2. **Integration Tests**: Verify debug output accuracy
3. **Performance Tests**: Ensure debug mode doesn't significantly impact performance
4. **Security Tests**: Verify no sensitive data leakage in debug logs

This implementation provides comprehensive debugging capabilities while maintaining security and performance standards. The modular approach allows enabling/disabling specific debug features as needed.