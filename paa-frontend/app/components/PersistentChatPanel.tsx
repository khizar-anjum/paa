'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Brain, User, Clock, CheckCircle, X, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import { chatApi, ChatHistory } from '@/lib/api/chat';
import { proactiveApi, ProactiveMessage, Commitment } from '@/lib/api/proactive';

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

  const handleCommitmentAction = async (commitmentId: number, action: 'complete' | 'dismiss' | 'postpone') => {
    try {
      switch (action) {
        case 'complete':
          await proactiveApi.completeCommitment(commitmentId);
          toast.success('Commitment marked as completed!');
          break;
        case 'dismiss':
          await proactiveApi.dismissCommitment(commitmentId);
          toast.success('Commitment dismissed');
          break;
        case 'postpone':
          const tomorrow = new Date();
          tomorrow.setDate(tomorrow.getDate() + 1);
          await proactiveApi.postponeCommitment(commitmentId, tomorrow.toISOString().split('T')[0]);
          toast.success('Commitment postponed to tomorrow');
          break;
      }
      // Reload data to update UI
      loadProactiveData();
    } catch (error) {
      toast.error(`Failed to ${action} commitment`);
    }
  };

  const findCommitmentForMessage = (message: ProactiveMessage): Commitment | undefined => {
    if (message.related_commitment_id) {
      return commitments.find(c => c.id === message.related_commitment_id);
    }
    return undefined;
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
        {/* Show proactive messages first */}
        {proactiveMessages.filter(pm => !pm.user_responded).map((proactiveMsg) => {
          const relatedCommitment = findCommitmentForMessage(proactiveMsg);
          return (
            <div key={`proactive-${proactiveMsg.id}`} className="space-y-3">
              {/* Proactive AI message */}
              <div className="flex justify-start">
                <div className="max-w-[85%] bg-yellow-50 border border-yellow-200 text-gray-900 rounded-lg p-3">
                  <div className="flex items-center mb-1">
                    <Clock className="h-3 w-3 mr-1 text-yellow-600" />
                    <span className="text-xs text-yellow-600 font-medium">Proactive Message</span>
                    {proactiveMsg.sent_at && (
                      <span className="text-xs text-gray-500 ml-2">{formatTime(proactiveMsg.sent_at)}</span>
                    )}
                  </div>
                  <p className="text-sm whitespace-pre-wrap mb-2">{proactiveMsg.content}</p>
                  
                  {/* Action buttons for commitment reminders */}
                  {proactiveMsg.message_type === 'commitment_reminder' && relatedCommitment && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      <button
                        onClick={() => handleCommitmentAction(relatedCommitment.id, 'complete')}
                        className="flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-md text-xs hover:bg-green-200 transition-colors"
                      >
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Done
                      </button>
                      <button
                        onClick={() => handleCommitmentAction(relatedCommitment.id, 'postpone')}
                        className="flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-md text-xs hover:bg-blue-200 transition-colors"
                      >
                        <Calendar className="h-3 w-3 mr-1" />
                        Tomorrow
                      </button>
                      <button
                        onClick={() => handleCommitmentAction(relatedCommitment.id, 'dismiss')}
                        className="flex items-center px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-xs hover:bg-gray-200 transition-colors"
                      >
                        <X className="h-3 w-3 mr-1" />
                        Dismiss
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Regular chat messages */}
        {messages.length === 0 && proactiveMessages.filter(pm => !pm.user_responded).length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-base mb-2">👋 Hi there!</p>
            <p className="text-sm">I&apos;m here to help you with your habits and goals. What&apos;s on your mind?</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="space-y-3">
              {/* User message */}
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-blue-600 text-white rounded-lg p-3">
                  <div className="flex items-center mb-1">
                    <User className="h-3 w-3 mr-1" />
                    <span className="text-xs opacity-75">{formatTime(msg.timestamp)}</span>
                  </div>
                  <p className="text-sm">{msg.message}</p>
                </div>
              </div>

              {/* AI response */}
              <div className="flex justify-start">
                <div className="max-w-[85%] bg-gray-100 text-gray-900 rounded-lg p-3">
                  <div className="flex items-center mb-1">
                    <Brain className="h-3 w-3 mr-1 text-blue-600" />
                    <span className="text-xs text-gray-500">{formatTime(msg.timestamp)}</span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap">{msg.response}</p>
                </div>
              </div>
            </div>
          ))
        )}
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