import axios from 'axios';
import { debugLogger } from '../debug-utils';

export interface HabitAnalytics {
  habit_id: number;
  habit_name: string;
  completion_rate: number;
  total_completions: number;
  total_days: number;
  daily_data: Array<{
    date: string;
    completed: number;
  }>;
}

export interface MoodAnalytics {
  average_mood: number | null;
  total_checkins: number;
  daily_moods: Array<{
    date: string;
    mood: number | null;
    notes: string | null;
  }>;
}

export interface OverviewAnalytics {
  total_habits: number;
  completed_today: number;
  completion_rate: number;
  current_mood: number | null;
  longest_streak: number;
  total_conversations: number;
}

export const analyticsApi = {
  getHabitsAnalytics: async (days: number = 30): Promise<HabitAnalytics[]> => {
    const startTime = Date.now();
    const url = `/analytics/habits?days=${days}`;
    const requestData = { days };
    
    const callId = debugLogger.logApiCall('GET', url, requestData);
    
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

  getMoodAnalytics: async (days: number = 30): Promise<MoodAnalytics> => {
    const startTime = Date.now();
    const url = `/analytics/mood?days=${days}`;
    const requestData = { days };
    
    const callId = debugLogger.logApiCall('GET', url, requestData);
    
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

  getOverview: async (): Promise<OverviewAnalytics> => {
    const startTime = Date.now();
    const url = '/analytics/overview';
    
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