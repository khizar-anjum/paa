import axios from 'axios';
import { debugLogger } from '../debug-utils';

export interface CommitmentAnalytics {
  commitment_id: number;
  commitment_name: string;
  completion_rate: number;
  total_completions: number;
  total_days: number;
  recurrence_pattern: string;
  is_recurring: boolean;
  daily_data: Array<{
    date: string;
    completed: number;
  }>;
}

// Keep old interface for backward compatibility during transition
export interface HabitAnalytics extends CommitmentAnalytics {
  habit_id: number;
  habit_name: string;
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
  total_commitments: number;
  recurring_commitments: number;
  one_time_commitments: number;
  completed_today: number;
  completion_rate: number;
  current_mood: number | null;
  longest_streak: number;
  total_conversations: number;
  // Keep old field for backward compatibility
  total_habits?: number;
}

export const analyticsApi = {
  // New unified commitments analytics
  getCommitmentsAnalytics: async (days: number = 30): Promise<CommitmentAnalytics[]> => {
    const startTime = Date.now();
    const url = `/analytics/commitments?days=${days}`;
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

  // Keep old habits analytics for backward compatibility
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