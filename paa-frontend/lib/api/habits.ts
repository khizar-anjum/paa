import axios from 'axios';
import { debugLogger } from '../debug-utils';

export interface Habit {
  id: number;
  name: string;
  frequency: string;
  reminder_time: string | null;
  created_at: string;
  is_active: number;
  completed_today: boolean;
  current_streak: number;
}

export interface CreateHabitData {
  name: string;
  frequency: string;
  reminder_time?: string;
}

export const habitsApi = {
  getAll: async (): Promise<Habit[]> => {
    const startTime = Date.now();
    const url = '/habits';
    
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

  create: async (data: CreateHabitData): Promise<Habit> => {
    const startTime = Date.now();
    const url = '/habits';
    
    const callId = debugLogger.logApiCall('POST', url, data);
    
    try {
      const response = await axios.post(url, data);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  complete: async (habitId: number) => {
    const startTime = Date.now();
    const url = `/habits/${habitId}/complete`;
    
    const callId = debugLogger.logApiCall('POST', url, { habitId });
    
    try {
      const response = await axios.post(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  update: async (habitId: number, data: CreateHabitData): Promise<Habit> => {
    const startTime = Date.now();
    const url = `/habits/${habitId}`;
    
    const callId = debugLogger.logApiCall('PUT', url, { habitId, ...data });
    
    try {
      const response = await axios.put(url, data);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'PUT', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'PUT', url, error, duration);
      throw error;
    }
  },

  delete: async (habitId: number) => {
    const startTime = Date.now();
    const url = `/habits/${habitId}`;
    
    const callId = debugLogger.logApiCall('DELETE', url, { habitId });
    
    try {
      const response = await axios.delete(url);
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'DELETE', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'DELETE', url, error, duration);
      throw error;
    }
  },

  getStats: async (habitId: number) => {
    const startTime = Date.now();
    const url = `/habits/${habitId}/stats`;
    
    const callId = debugLogger.logApiCall('GET', url, { habitId });
    
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