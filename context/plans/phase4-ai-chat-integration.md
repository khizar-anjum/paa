# Phase 4: AI Chat Integration (1 hour)

## Overview
Integrate Claude/OpenAI API for intelligent conversations with context awareness about user's habits and progress.

## Step-by-Step Implementation

### 1. Backend AI Integration (20 mins)

Update `main.py` with enhanced chat functionality:

```python
# Add to imports
import json
from typing import List, Optional

# Update the chat endpoint with real AI integration
@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    message: schemas.ChatMessage,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get user context
        habits = db.query(models.Habit).filter(
            models.Habit.user_id == current_user.id,
            models.Habit.is_active == 1
        ).all()
        
        # Get recent check-ins
        recent_checkins = db.query(models.DailyCheckIn).filter(
            models.DailyCheckIn.user_id == current_user.id
        ).order_by(models.DailyCheckIn.timestamp.desc()).limit(5).all()
        
        # Get recent conversations for context
        recent_convos = db.query(models.Conversation).filter(
            models.Conversation.user_id == current_user.id
        ).order_by(models.Conversation.timestamp.desc()).limit(5).all()
        
        # Build context
        habit_context = []
        for habit in habits:
            # Check completion status
            today_start = datetime.combine(date.today(), datetime.min.time())
            completed_today = db.query(models.HabitLog).filter(
                models.HabitLog.habit_id == habit.id,
                models.HabitLog.completed_at >= today_start
            ).first() is not None
            
            habit_context.append({
                "name": habit.name,
                "frequency": habit.frequency,
                "completed_today": completed_today,
                "reminder_time": habit.reminder_time
            })
        
        mood_context = []
        for checkin in recent_checkins:
            mood_context.append({
                "date": checkin.timestamp.strftime("%Y-%m-%d"),
                "mood": checkin.mood,
                "notes": checkin.notes
            })
        
        conversation_history = []
        for convo in reversed(recent_convos):  # Oldest first
            conversation_history.append(f"User: {convo.message}")
            conversation_history.append(f"Assistant: {convo.response}")
        
        # Create system prompt
        system_prompt = f"""You are a friendly, supportive personal AI assistant helping {current_user.username} with their habits and personal development.

Current habits:
{json.dumps(habit_context, indent=2)}

Recent mood check-ins:
{json.dumps(mood_context, indent=2)}

Recent conversation history:
{chr(10).join(conversation_history[-10:])}  # Last 5 exchanges

Guidelines:
1. Be encouraging and supportive
2. Reference their specific habits when relevant
3. Acknowledge their mood and progress
4. Provide actionable advice
5. Keep responses concise but warm
6. If they haven't completed habits today, gently encourage them
7. Celebrate their successes and streaks"""

        # Call AI API
        if anthropic_client and os.getenv("ANTHROPIC_API_KEY"):
            # Use Claude
            response = anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast model for chat
                max_tokens=500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": message.message}
                ]
            )
            response_text = response.content[0].text
        else:
            # Fallback response for demo without API key
            response_text = generate_demo_response(message.message, habit_context, mood_context)
        
        # Save conversation
        conversation = models.Conversation(
            user_id=current_user.id,
            message=message.message,
            response=response_text
        )
        db.add(conversation)
        db.commit()
        
        return schemas.ChatResponse(
            message=message.message,
            response=response_text,
            timestamp=conversation.timestamp
        )
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        # Fallback response
        response_text = "I'm here to help! Tell me about your day or ask me anything about your habits."
        
        conversation = models.Conversation(
            user_id=current_user.id,
            message=message.message,
            response=response_text
        )
        db.add(conversation)
        db.commit()
        
        return schemas.ChatResponse(
            message=message.message,
            response=response_text,
            timestamp=conversation.timestamp
        )

def generate_demo_response(message: str, habits: List[dict], moods: List[dict]) -> str:
    """Generate a demo response when no AI API is available"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['habit', 'track', 'progress']):
        if habits:
            completed = sum(1 for h in habits if h['completed_today'])
            total = len(habits)
            return f"You're tracking {total} habits! You've completed {completed} out of {total} today. Keep up the great work! 🌟"
        else:
            return "I notice you haven't set up any habits yet. Would you like to start with something simple like daily meditation or drinking more water?"
    
    elif any(word in message_lower for word in ['feel', 'mood', 'today']):
        if moods and moods[0]['mood']:
            mood_score = moods[0]['mood']
            if mood_score >= 4:
                return "I'm glad you're feeling good! What's been going well for you today?"
            else:
                return "I hear you. Some days are tougher than others. What can I do to support you right now?"
        else:
            return "How are you feeling today? I'm here to listen and support you."
    
    elif any(word in message_lower for word in ['help', 'what can you']):
        return "I can help you track habits, check in on your mood, provide motivation, and offer advice on building better routines. What would you like to focus on?"
    
    else:
        return f"I understand you're asking about '{message}'. I'm here to support your personal growth journey. Feel free to ask me about your habits, mood, or anything else on your mind!"

# Get chat history endpoint
@app.get("/chat/history")
def get_chat_history(
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).order_by(models.Conversation.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": conv.id,
            "message": conv.message,
            "response": conv.response,
            "timestamp": conv.timestamp
        }
        for conv in reversed(conversations)  # Return in chronological order
    ]
```

### 2. Frontend Chat Service (10 mins)

Create `lib/api/chat.ts`:
```typescript
import axios from 'axios';

export interface ChatMessage {
  message: string;
}

export interface ChatResponse {
  message: string;
  response: string;
  timestamp: string;
}

export interface ChatHistory {
  id: number;
  message: string;
  response: string;
  timestamp: string;
}

export const chatApi = {
  sendMessage: async (message: string): Promise<ChatResponse> => {
    const response = await axios.post('/chat', { message });
    return response.data;
  },

  getHistory: async (limit: number = 20): Promise<ChatHistory[]> => {
    const response = await axios.get(`/chat/history?limit=${limit}`);
    return response.data;
  },
};
```

### 3. Chat Components (20 mins)

Create `app/components/ChatMessage.tsx`:
```tsx
'use client';

import { Brain, User } from 'lucide-react';

interface ChatMessageProps {
  message: string;
  response: string;
  timestamp: string;
}

export function ChatMessage({ message, response, timestamp }: ChatMessageProps) {
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  return (
    <div className="space-y-4">
      {/* User message */}
      <div className="flex justify-end">
        <div className="max-w-[70%] bg-blue-600 text-white rounded-lg p-3">
          <div className="flex items-center mb-1">
            <User className="h-4 w-4 mr-2" />
            <span className="text-xs opacity-75">{formatTime(timestamp)}</span>
          </div>
          <p className="text-sm">{message}</p>
        </div>
      </div>

      {/* AI response */}
      <div className="flex justify-start">
        <div className="max-w-[70%] bg-gray-100 text-gray-900 rounded-lg p-3">
          <div className="flex items-center mb-1">
            <Brain className="h-4 w-4 mr-2 text-blue-600" />
            <span className="text-xs text-gray-500">{formatTime(timestamp)}</span>
          </div>
          <p className="text-sm whitespace-pre-wrap">{response}</p>
        </div>
      </div>
    </div>
  );
}
```

### 4. Chat Page (10 mins)

Create `app/dashboard/chat/page.tsx`:
```tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { chatApi, ChatHistory } from '@/lib/api/chat';
import { ChatMessage } from '@/app/components/ChatMessage';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatHistory[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadChatHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatHistory = async () => {
    setIsLoading(true);
    try {
      const history = await chatApi.getHistory();
      setMessages(history);
    } catch (error) {
      toast.error('Failed to load chat history');
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async () => {
    if (!input.trim() || isSending) return;

    const userMessage = input.trim();
    setInput('');
    setIsSending(true);

    // Add temporary message
    const tempMessage: ChatHistory = {
      id: Date.now(),
      message: userMessage,
      response: '...',
      timestamp: new Date().toISOString(),
    };
    setMessages([...messages, tempMessage]);

    try {
      const response = await chatApi.sendMessage(userMessage);
      // Replace temporary message with actual response
      setMessages(prev => 
        prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, response: response.response, timestamp: response.timestamp }
            : msg
        )
      );
    } catch (error) {
      toast.error('Failed to send message');
      // Remove temporary message on error
      setMessages(prev => prev.filter(msg => msg.id !== tempMessage.id));
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">AI Assistant</h1>
        <p className="text-gray-600 mt-2">Chat with your personal AI assistant</p>
      </div>

      <div className="flex-1 bg-white rounded-lg shadow-md flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              <p className="text-lg mb-2">No messages yet</p>
              <p className="text-sm">Start a conversation with your AI assistant!</p>
            </div>
          ) : (
            messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg.message}
                response={msg.response}
                timestamp={msg.timestamp}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 5. Quick Chat Widget for Dashboard (10 mins)

Create `app/components/QuickChat.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { MessageSquare, Send, X } from 'lucide-react';
import { chatApi } from '@/lib/api/chat';
import { toast } from 'sonner';

export function QuickChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!message.trim()) return;

    setIsLoading(true);
    setResponse('');

    try {
      const result = await chatApi.sendMessage(message);
      setResponse(result.response);
      setMessage('');
    } catch (error) {
      toast.error('Failed to get response');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white rounded-full p-4 shadow-lg hover:bg-blue-700 transition-colors"
      >
        <MessageSquare className="h-6 w-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 bg-white rounded-lg shadow-xl">
      <div className="flex items-center justify-between p-4 border-b">
        <h3 className="font-semibold">Quick Chat</h3>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="p-4 h-64 overflow-y-auto">
        {response ? (
          <div className="bg-gray-100 rounded-lg p-3">
            <p className="text-sm">{response}</p>
          </div>
        ) : (
          <p className="text-gray-500 text-center mt-8">
            Ask me anything about your habits or how you're doing!
          </p>
        )}
      </div>

      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a quick question..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!message.trim() || isLoading}
            className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
```

Add QuickChat to dashboard layout in `app/dashboard/layout.tsx`:
```tsx
// Add to imports
import { QuickChat } from '@/app/components/QuickChat';

// Add before closing div in the layout
<QuickChat />
```

## Testing AI Chat

1. Navigate to http://localhost:3000/dashboard/chat
2. Send a message asking about your habits
3. Ask how you're doing
4. Try the quick chat widget on any dashboard page
5. Check that context is maintained across messages

## Demo Responses (No API Key)

If you don't have an API key, the system will provide contextual demo responses:
- Questions about habits show habit summary
- Mood questions acknowledge recent check-ins
- General questions provide helpful guidance

## Troubleshooting

1. **API Key issues**: Check .env file and restart backend
2. **Context not working**: Verify database queries return data
3. **Chat history**: Check timestamp handling and ordering

## Next Steps
- Phase 5: Daily check-in and analytics
- Add typing indicators
- Implement message reactions