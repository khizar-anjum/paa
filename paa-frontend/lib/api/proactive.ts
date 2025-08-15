import axios from 'axios';
import { debugLogger } from '../debug-utils';
import { getApiUrl } from '@/lib/utils/platform';

const getApiUrlForProactive = () => {
  const mobileUrl = getApiUrl();
  return mobileUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export interface ProactiveMessage {
  id: number;
  user_id: number;
  message_type: string;
  content: string;
  related_commitment_id?: number;
  session_id?: string;
  scheduled_for?: string;
  sent_at?: string;
  user_responded: boolean;
  response_content?: string;
}

export interface Commitment {
  id: number;
  user_id: number;
  task_description: string;
  original_message?: string;
  deadline?: string;
  status: string;
  created_from_conversation_id?: number;
  last_reminded_at?: string;
  reminder_count: number;
  created_at: string;
}

export interface ScheduledPrompt {
  id: number;
  user_id: number;
  prompt_type: string;
  schedule_time: string;
  schedule_days: string;
  prompt_template: string;
  is_active: boolean;
  last_sent_at?: string;
  created_at: string;
}

// Function to get auth token from localStorage
const getAuthToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

// Create axios instance with auth headers
const api = axios.create({
  baseURL: getApiUrlForProactive(),
});

api.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const proactiveApi = {
  // Proactive messages
  getProactiveMessages: async (): Promise<ProactiveMessage[]> => {
    const startTime = Date.now();
    const url = '/proactive-messages';
    
    const callId = debugLogger.logApiCall('GET', url);
    
    try {
      const response = await api.get(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'GET', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'GET', url, error, duration);
      throw error;
    }
  },

  acknowledgeProactiveMessage: async (messageId: number, responseContent: string): Promise<void> => {
    const startTime = Date.now();
    const url = `/proactive-messages/${messageId}/acknowledge`;
    const requestData = { messageId, response_content: responseContent };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const response = await api.post(url, {
        response_content: responseContent
      });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  // Commitments
  getCommitments: async (): Promise<Commitment[]> => {
    const startTime = Date.now();
    const url = '/commitments';
    
    const callId = debugLogger.logApiCall('GET', url);
    
    try {
      const response = await api.get(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'GET', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'GET', url, error, duration);
      throw error;
    }
  },

  completeCommitment: async (commitmentId: number): Promise<void> => {
    const startTime = Date.now();
    const url = `/commitments/${commitmentId}/complete`;
    const requestData = { commitmentId };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const response = await api.post(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  dismissCommitment: async (commitmentId: number): Promise<void> => {
    const startTime = Date.now();
    const url = `/commitments/${commitmentId}/dismiss`;
    const requestData = { commitmentId };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const response = await api.post(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  postponeCommitment: async (commitmentId: number, newDeadline?: string): Promise<void> => {
    const startTime = Date.now();
    const url = `/commitments/${commitmentId}/postpone`;
    const requestData = { commitmentId, deadline: newDeadline };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const response = await api.post(url, {
        deadline: newDeadline
      });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  // Scheduled prompts
  getScheduledPrompts: async (): Promise<ScheduledPrompt[]> => {
    const startTime = Date.now();
    const url = '/scheduled-prompts';
    
    const callId = debugLogger.logApiCall('GET', url);
    
    try {
      const response = await api.get(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'GET', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'GET', url, error, duration);
      throw error;
    }
  },

  updateScheduledPrompt: async (promptId: number, updates: Partial<ScheduledPrompt>): Promise<ScheduledPrompt> => {
    const startTime = Date.now();
    const url = `/scheduled-prompts/${promptId}`;
    const requestData = { promptId, ...updates };
    
    const callId = debugLogger.logApiCall('PUT', url, requestData);
    
    try {
      const response = await api.put(url, updates);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'PUT', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'PUT', url, error, duration);
      throw error;
    }
  },
};