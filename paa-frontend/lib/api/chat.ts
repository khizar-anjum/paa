import axios from 'axios';
import { debugLogger } from '../debug-utils';

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
    const startTime = Date.now();
    const url = '/chat/enhanced';
    const requestData = { message };
    
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

  getHistory: async (limit: number = 20): Promise<ChatHistory[]> => {
    const startTime = Date.now();
    const url = `/chat/history?limit=${limit}`;
    
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