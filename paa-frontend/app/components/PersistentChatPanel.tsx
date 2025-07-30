'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Brain, User } from 'lucide-react';
import { toast } from 'sonner';
import { chatApi, ChatHistory } from '@/lib/api/chat';
import { proactiveApi, ProactiveMessage, Commitment } from '@/lib/api/proactive';
import { dataUpdateEvents, DATA_EVENTS } from '@/lib/events/dataUpdateEvents';

export function PersistentChatPanel() {
  const [messages, setMessages] = useState<ChatHistory[]>([]);
  const [proactiveMessages, setProactiveMessages] = useState<ProactiveMessage[]>([]);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadChatHistory();
    loadProactiveData();
    
    // Set up interval to refresh proactive messages every 10 seconds
    const proactiveInterval = setInterval(loadProactiveData, 10000);
    
    return () => {
      clearInterval(proactiveInterval);
    };
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

  const loadProactiveData = async () => {
    try {
      const [proactiveData, commitmentsData] = await Promise.all([
        proactiveApi.getProactiveMessages(),
        proactiveApi.getCommitments()
      ]);
      console.log('Loaded proactive data:', { 
        proactiveMessages: proactiveData.length, 
        commitments: commitmentsData.length 
      });
      setProactiveMessages(proactiveData);
      setCommitments(commitmentsData);
    } catch (error) {
      console.error('Failed to load proactive data:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    // Since we have date separators, just show the time
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
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
      
      // Emit update events to refresh other components
      // Since we don't know what was updated, emit all relevant events
      dataUpdateEvents.emitMultiple([
        DATA_EVENTS.COMMITMENT_UPDATED,
        DATA_EVENTS.HABIT_UPDATED,
        DATA_EVENTS.PROFILE_UPDATED,
        DATA_EVENTS.CHECKIN_UPDATED
      ]);
      
      // Also reload proactive data to reflect any new commitments/messages
      loadProactiveData();
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
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center">
          <Brain className="h-6 w-6 text-blue-600 mr-2" />
          <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
        </div>
        <p className="text-sm text-gray-500 mt-1">Your proactive and persistent companion</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Combine all messages (proactive and regular) into a single timeline */}
        {(() => {
          // Create a combined array of messages with their types and timestamps
          const allMessages: Array<{
            type: 'proactive' | 'chat';
            message: ProactiveMessage | ChatHistory;
            timestamp: string;
          }> = [];

          // Add proactive messages that haven't been responded to
          proactiveMessages.filter(pm => !pm.user_responded).forEach(pm => {
            allMessages.push({
              type: 'proactive',
              message: pm,
              timestamp: pm.sent_at || new Date().toISOString()
            });
          });

          // Add regular chat messages
          messages.forEach(msg => {
            allMessages.push({
              type: 'chat',
              message: msg,
              timestamp: msg.timestamp
            });
          });

          // Sort by timestamp
          allMessages.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

          if (allMessages.length === 0) {
            return (
              <div className="text-center text-gray-500 mt-8">
                <p className="text-base mb-2">👋 Hi there!</p>
                <p className="text-sm">I&apos;m here to help you with your habits and goals. What&apos;s on your mind?</p>
              </div>
            );
          }

          return allMessages.map((item, index) => {
            // Check if we need to show a date separator
            const showDateSeparator = index === 0 || 
              new Date(item.timestamp).toDateString() !== 
              new Date(allMessages[index - 1].timestamp).toDateString();
            
            const dateSeparator = showDateSeparator ? (
              <div key={`date-${item.timestamp}`} className="flex items-center justify-center my-4">
                <div className="flex-grow border-t border-gray-200"></div>
                <span className="px-3 text-xs text-gray-500 bg-gray-50">
                  {(() => {
                    const date = new Date(item.timestamp);
                    const now = new Date();
                    const isToday = date.toDateString() === now.toDateString();
                    const yesterday = new Date(now);
                    yesterday.setDate(yesterday.getDate() - 1);
                    const isYesterday = date.toDateString() === yesterday.toDateString();
                    
                    if (isToday) return 'Today';
                    if (isYesterday) return 'Yesterday';
                    return date.toLocaleDateString('en-US', { 
                      month: 'long', 
                      day: 'numeric',
                      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
                    });
                  })()}
                </span>
                <div className="flex-grow border-t border-gray-200"></div>
              </div>
            ) : null;
            
            const messageElement = (() => {
              if (item.type === 'proactive') {
                const proactiveMsg = item.message as ProactiveMessage;
                return (
                  <div key={`proactive-${proactiveMsg.id}`} className="flex justify-start">
                    <div className="max-w-[85%] bg-gray-100 text-gray-900 rounded-lg p-3">
                      <div className="flex items-center mb-1">
                        <Brain className="h-3 w-3 mr-1 text-blue-600" />
                        <span className="text-xs text-gray-500">{formatTime(proactiveMsg.sent_at || new Date().toISOString())}</span>
                      </div>
                      <p className="text-sm whitespace-pre-wrap">{proactiveMsg.content}</p>
                    </div>
                  </div>
                );
              } else {
                const chatMsg = item.message as ChatHistory;
                return (
                  <div key={chatMsg.id} className="space-y-3">
                    {/* User message */}
                    <div className="flex justify-end">
                      <div className="max-w-[85%] bg-blue-600 text-white rounded-lg p-3">
                        <div className="flex items-center mb-1">
                          <User className="h-3 w-3 mr-1" />
                          <span className="text-xs opacity-75">{formatTime(chatMsg.timestamp)}</span>
                        </div>
                        <p className="text-sm">{chatMsg.message}</p>
                      </div>
                    </div>

                    {/* AI response */}
                    <div className="flex justify-start">
                      <div className="max-w-[85%] bg-gray-100 text-gray-900 rounded-lg p-3">
                        <div className="flex items-center mb-1">
                          <Brain className="h-3 w-3 mr-1 text-blue-600" />
                          <span className="text-xs text-gray-500">{formatTime(chatMsg.timestamp)}</span>
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{chatMsg.response}</p>
                      </div>
                    </div>
                  </div>
                );
              }
            })();
            
            return (
              <React.Fragment key={`msg-group-${index}`}>
                {dateSeparator}
                {messageElement}
              </React.Fragment>
            );
          });
        })()}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Message your AI assistant..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSending}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isSending}
            className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}