'use client';

import { useState, useEffect } from 'react';
import { Session, sessionAPI } from '@/lib/api/sessions';
import { Plus, MessageSquare, Edit2, Trash2, MoreVertical } from 'lucide-react';
import { toast } from 'sonner';

interface SessionManagerProps {
  currentSessionId: string | null;
  onSessionChange: (sessionId: string) => void;
  className?: string;
}

export function SessionManager({ 
  currentSessionId, 
  onSessionChange, 
  className = "" 
}: SessionManagerProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showNewSessionInput, setShowNewSessionInput] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editName, setEditName] = useState('');

  const loadSessions = async () => {
    try {
      const data = await sessionAPI.list();
      setSessions(data);
      
      // If no current session is selected, select the most recent one
      if (!currentSessionId && data.length > 0) {
        onSessionChange(data[0].id);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      toast.error('Failed to load chat sessions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const createNewSession = async () => {
    if (!newSessionName.trim()) {
      toast.error('Please enter a session name');
      return;
    }

    try {
      const newSession = await sessionAPI.create({ name: newSessionName.trim() });
      setSessions(prev => [newSession, ...prev]);
      onSessionChange(newSession.id);
      setNewSessionName('');
      setShowNewSessionInput(false);
      setShowDropdown(false);
      toast.success('New chat session created');
    } catch (error) {
      console.error('Failed to create session:', error);
      toast.error('Failed to create session');
    }
  };

  const updateSession = async (sessionId: string, name: string) => {
    try {
      const updatedSession = await sessionAPI.update(sessionId, { name });
      setSessions(prev => prev.map(s => s.id === sessionId ? updatedSession : s));
      setEditingSession(null);
      setEditName('');
      toast.success('Session renamed');
    } catch (error) {
      console.error('Failed to update session:', error);
      toast.error('Failed to rename session');
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this chat session? This will delete all messages in it.')) {
      return;
    }

    try {
      await sessionAPI.delete(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If we deleted the current session, switch to another one
      if (currentSessionId === sessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionId);
        if (remainingSessions.length > 0) {
          onSessionChange(remainingSessions[0].id);
        }
      }
      
      toast.success('Session deleted');
    } catch (error) {
      console.error('Failed to delete session:', error);
      toast.error('Failed to delete session');
    }
  };

  const currentSession = sessions.find(s => s.id === currentSessionId);

  if (isLoading) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <MessageSquare className="h-4 w-4 animate-pulse" />
        <span className="text-sm text-gray-500">Loading...</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Session Selector */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors min-w-0 max-w-48"
        >
          <MessageSquare className="h-4 w-4 text-blue-600 flex-shrink-0" />
          <span className="text-sm font-medium text-gray-900 truncate">
            {currentSession?.name || 'Select Chat'}
          </span>
          <MoreVertical className="h-4 w-4 text-gray-400 flex-shrink-0" />
        </button>
        
        {/* Quick New Chat Button */}
        <button
          onClick={() => setShowNewSessionInput(true)}
          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="New Chat"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      {/* Dropdown Menu */}
      {showDropdown && (
        <div className="absolute top-full left-0 mt-1 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto">
          {/* New Session Input */}
          {showNewSessionInput && (
            <div className="p-3 border-b border-gray-100">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  placeholder="Enter session name..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') createNewSession();
                    if (e.key === 'Escape') {
                      setShowNewSessionInput(false);
                      setNewSessionName('');
                    }
                  }}
                  autoFocus
                />
                <button
                  onClick={createNewSession}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </div>
          )}

          {/* Sessions List */}
          <div className="py-2">
            {sessions.length === 0 ? (
              <div className="px-4 py-6 text-center text-gray-500 text-sm">
                No chat sessions yet. Create your first one!
              </div>
            ) : (
              sessions.map((session) => (
                <div
                  key={session.id}
                  className={`group flex items-center justify-between px-4 py-2 hover:bg-gray-50 cursor-pointer ${
                    currentSessionId === session.id ? 'bg-blue-50 border-r-2 border-blue-600' : ''
                  }`}
                >
                  <div
                    className="flex-1 min-w-0"
                    onClick={() => {
                      onSessionChange(session.id);
                      setShowDropdown(false);
                    }}
                  >
                    {editingSession === session.id ? (
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') updateSession(session.id, editName);
                          if (e.key === 'Escape') setEditingSession(null);
                        }}
                        onBlur={() => updateSession(session.id, editName)}
                        autoFocus
                      />
                    ) : (
                      <div>
                        <div className="font-medium text-gray-900 text-sm truncate">
                          {session.name}
                        </div>
                        <div className="text-xs text-gray-500 flex items-center space-x-2">
                          <span>{session.message_count} messages</span>
                          {session.last_message_at && (
                            <span>• {new Date(session.last_message_at).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Session Actions */}
                  <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingSession(session.id);
                        setEditName(session.name);
                      }}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      title="Rename"
                    >
                      <Edit2 className="h-3 w-3" />
                    </button>
                    {sessions.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600 rounded"
                        title="Delete"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Create New Session Button */}
          {!showNewSessionInput && (
            <div className="border-t border-gray-100 p-2">
              <button
                onClick={() => setShowNewSessionInput(true)}
                className="w-full flex items-center space-x-2 px-3 py-2 text-left text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
              >
                <Plus className="h-4 w-4" />
                <span>New Chat Session</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Backdrop */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
}