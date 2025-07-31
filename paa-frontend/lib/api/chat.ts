import axios from 'axios';
import { debugLogger } from '../debug-utils';

export interface ChatMessage {
  message: string;
  session_id?: string;
}

export interface ChatMessageEnhanced {
  message: string;
  session_id: string;
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
  session_id: string;
  session_name: string;
}

export const chatApi = {
  sendMessage: async (message: string, sessionId: string): Promise<ChatResponse> => {
    const startTime = Date.now();
    const url = '/chat/enhanced';
    const requestData = { message, session_id: sessionId };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const response = await axios.post(url, requestData);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  getHistory: async (sessionId: string, limit: number = 50): Promise<ChatHistory[]> => {
    const startTime = Date.now();
    const url = `/chat/history/${sessionId}?limit=${limit}`;
    
    const callId = debugLogger.logApiCall('GET', url);
    
    try {
      const response = await axios.get(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'GET', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'GET', url, error, duration);
      throw error;
    }
  },
};