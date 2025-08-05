'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Brain, User, History, Plus, Menu } from 'lucide-react';
import { toast } from 'sonner';
import { chatApi, ChatHistory } from '@/lib/api/chat';
import { proactiveApi, ProactiveMessage, Commitment } from '@/lib/api/proactive';
import { sessionAPI, Session } from '@/lib/api/sessions';
import { dataUpdateEvents, DATA_EVENTS } from '@/lib/events/dataUpdateEvents';

interface PersistentChatPanelProps {
  onOpenSidebar?: () => void;
}

export function PersistentChatPanel({ onOpenSidebar }: PersistentChatPanelProps) {
  const [messages, setMessages] = useState<ChatHistory[]>([]);
  const [proactiveMessages, setProactiveMessages] = useState<ProactiveMessage[]>([]);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [currentSessionName, setCurrentSessionName] = useState<string>('');
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    initializeSession();
    loadProactiveData();
    
    // Set up interval to refresh proactive messages every 10 seconds
    const proactiveInterval = setInterval(loadProactiveData, 10000);
    
    return () => {
      clearInterval(proactiveInterval);
    };
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      loadChatHistory(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeSession = async () => {
    try {
      // Load existing sessions first
      const allSessions = await sessionAPI.list();
      setSessions(allSessions);
      
      // If there's an active session, use it
      if (allSessions.length > 0) {
        setCurrentSessionId(allSessions[0].id);
        setCurrentSessionName(allSessions[0].name);
      } else {
        // Create first session automatically
        const newSession = await sessionAPI.createAuto();
        setSessions([newSession]);
        setCurrentSessionId(newSession.id);
        setCurrentSessionName(newSession.name);
      }
    } catch (error) {
      console.error('Failed to initialize session:', error);
      toast.error('Failed to initialize chat session');
    }
  };

  const createNewSession = async () => {
    if (isCreatingSession) return;
    
    setIsCreatingSession(true);
    try {
      const newSession = await sessionAPI.createAuto();
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setCurrentSessionName(newSession.name);
      toast.success('New chat session created');
    } catch (error) {
      console.error('Failed to create session:', error);
      toast.error('Failed to create new session');
    } finally {
      setIsCreatingSession(false);
    }
  };

  const switchToSession = (session: Session) => {
    setCurrentSessionId(session.id);
    setCurrentSessionName(session.name);
    setShowHistoryPanel(false);
  };

  const loadSessions = async () => {
    try {
      const allSessions = await sessionAPI.list();
      // Sort by created_at descending (newest first)
      const sortedSessions = allSessions.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setSessions(sortedSessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const loadChatHistory = async (sessionId: string) => {
    setIsLoading(true);
    try {
      const history = await chatApi.getHistory(sessionId);
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

  const generateSessionNameAfterMessage = async (sessionId: string) => {
    try {
      // Only generate name if session is still "New Chat"
      const currentSession = sessions.find(s => s.id === sessionId);
      if (currentSession && currentSession.name === "New Chat") {
        const result = await sessionAPI.generateName(sessionId);
        setCurrentSessionName(result.name);
        setSessions(prev => prev.map(s => 
          s.id === sessionId ? { ...s, name: result.name } : s
        ));
      }
    } catch (error) {
      console.error('Failed to generate session name:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isSending || !currentSessionId) return;

    const userMessage = input.trim();
    setInput('');
    setIsSending(true);

    // Add temporary message
    const tempMessage: ChatHistory = {
      id: Date.now(),
      message: userMessage,
      response: '...',
      timestamp: new Date().toISOString(),
      session_id: currentSessionId,
      session_name: currentSessionName
    };
    setMessages([...messages, tempMessage]);

    try {
      const response = await chatApi.sendMessage(userMessage, currentSessionId);
      // Replace temporary message with actual response
      setMessages(prev => 
        prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, response: response.response, timestamp: response.timestamp }
            : msg
        )
      );
      
      // Generate session name after first successful message
      generateSessionNameAfterMessage(currentSessionId);
      
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

  const deleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this chat session? This will delete all messages in it.')) {
      return;
    }

    try {
      await sessionAPI.delete(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If we deleted the current session, switch to another one or create new
      if (currentSessionId === sessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          switchToSession(remainingSessions[0]);
        } else {
          // Create a new session if none exist
          await createNewSession();
        }
      }
      
      toast.success('Session deleted');
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error('Failed to delete session');
    }
  };

  if (isLoading && currentSessionId) {
    return (
      <div className="h-full flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col">
      {/* Header with History and New Chat buttons */}
      <div className="border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-3">
          <div className="flex items-center">
            {/* Hamburger Menu Button - Only show on small screens since ExpandableSidebar handles it on large screens */}
            {onOpenSidebar && (
              <button
                onClick={onOpenSidebar}
                className="lg:hidden p-2 rounded-md hover:bg-gray-100 transition-colors mr-3"
                aria-label="Open navigation menu"
              >
                <Menu className="h-5 w-5 text-gray-600" />
              </button>
            )}
            <Brain className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">AI Assistant</h2>
            {currentSessionName && (
              <span className="ml-3 text-sm text-gray-500">• {currentSessionName}</span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {/* New Session Button */}
            <button
              onClick={createNewSession}
              disabled={isCreatingSession}
              className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              title="Start New Chat"
            >
              {isCreatingSession ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              <span className="text-sm font-medium">New Chat</span>
            </button>
            
            {/* History Button */}
            <button
              onClick={() => {
                if (showHistoryPanel) {
                  setShowHistoryPanel(false);
                } else {
                  setShowHistoryPanel(true);
                  loadSessions();
                }
              }}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors ${
                showHistoryPanel 
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              title="Chat History"
            >
              <History className="h-4 w-4" />
              <span className="text-sm font-medium">History</span>
            </button>
          </div>
        </div>
          
          <p className="text-sm text-gray-500">Your proactive and persistent companion</p>
        </div>
      </div>

      {/* Messages or History Panel */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-4 space-y-4">
        {showHistoryPanel ? (
          // History Panel
          <div className="h-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Chat History</h3>
              <button
                onClick={() => setShowHistoryPanel(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {sessions.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <History className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p>No chat sessions yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-4 rounded-lg border cursor-pointer transition-colors hover:bg-gray-50 ${
                      currentSessionId === session.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200'
                    }`}
                    onClick={() => switchToSession(session)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 truncate">
                          {session.name}
                        </h4>
                        <div className="flex items-center space-x-3 mt-1 text-sm text-gray-500">
                          <span>{session.message_count} messages</span>
                          <span>• {session.last_message_at 
                            ? new Date(session.last_message_at).toLocaleDateString()
                            : new Date(session.created_at).toLocaleDateString()
                          }</span>
                        </div>
                      </div>
                      
                      {currentSessionId === session.id && (
                        <div className="ml-3 text-blue-600">
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      )}
                      
                      {sessions.length > 1 && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSession(session.id);
                          }}
                          className="ml-3 p-1 text-gray-400 hover:text-red-600 transition-colors"
                          title="Delete session"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                
                {/* New Chat button at bottom */}
                <div className="pt-4 border-t border-gray-200">
                  <button
                    onClick={createNewSession}
                    disabled={isCreatingSession}
                    className="flex items-center justify-center space-x-2 w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {isCreatingSession ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )}
                    <span>New Chat</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : !currentSessionId ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-base mb-2">👋 Welcome!</p>
            <p className="text-sm">Create or select a chat session to start our conversation.</p>
          </div>
        ) : (
          <>
            {/* Combine all messages (proactive and regular) into a single timeline */}
            {(() => {
              // Create a combined array of messages with their types and timestamps
              const allMessages: Array<{
                type: 'proactive' | 'chat';
                message: ProactiveMessage | ChatHistory;
                timestamp: string;
              }> = [];

              // Add proactive messages that haven't been responded to and are targeted to current session
              // Note: Only show messages specifically targeted to this session
              proactiveMessages.filter(pm => 
                !pm.user_responded && 
                pm.session_id === currentSessionId
              ).forEach(pm => {
                allMessages.push({
                  type: 'proactive',
                  message: pm,
                  timestamp: pm.sent_at || new Date().toISOString()
                });
              });

              // Add regular chat messages (only for current session)
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
                            <div className="text-sm whitespace-pre-wrap">
                              {chatMsg.response === '...' ? (
                                <div className="flex items-center space-x-1">
                                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                </div>
                              ) : (
                                chatMsg.response
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  }
                })();
                
                return (
                  <React.Fragment key={`fragment-${item.timestamp}-${index}`}>
                    {dateSeparator}
                    {messageElement}
                  </React.Fragment>
                );
              });
            })()}
          </>
        )}
        <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Message Input - Only show when not in history mode */}
      {!showHistoryPanel && (
        <div className="border-t border-gray-200">
          <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex space-x-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message..."
              disabled={isSending || !currentSessionId}
              className="flex-1 resize-none border border-gray-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
              rows={1}
              style={{ minHeight: '44px', maxHeight: '120px' }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 120) + 'px';
              }}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isSending || !currentSessionId}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
            >
              {isSending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </div>
          {!currentSessionId && (
            <p className="text-xs text-gray-500 mt-2">
              No active session - please wait while we initialize...
            </p>
          )}
          </div>
        </div>
      )}

    </div>
  );
}