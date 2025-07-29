import axios from 'axios';
import { debugLogger } from '../debug-utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface UserProfile {
  id: number;
  name: string;
  how_you_know_them?: string;
  pronouns?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfileCreate {
  name: string;
  how_you_know_them?: string;
  pronouns?: string;
  description?: string;
}

export interface UserProfileUpdate {
  name?: string;
  how_you_know_them?: string;
  pronouns?: string;
  description?: string;
}

// API functions
export const profileApi = {
  async get(): Promise<UserProfile> {
    const startTime = Date.now();
    const url = `${API_URL}/profile`;
    
    const callId = debugLogger.logApiCall('GET', url);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'GET', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'GET', url, error, duration);
      throw error;
    }
  },

  async create(profile: UserProfileCreate): Promise<UserProfile> {
    const startTime = Date.now();
    const url = `${API_URL}/profile`;
    const requestData = { ...profile };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(url, profile, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'POST', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'POST', url, error, duration);
      throw error;
    }
  },

  async update(profile: UserProfileUpdate): Promise<UserProfile> {
    const startTime = Date.now();
    const url = `${API_URL}/profile`;
    const requestData = { ...profile };
    
    const callId = debugLogger.logApiCall('PUT', url, requestData);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(url, profile, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'PUT', url, response.data, duration, response.status);
      return response.data;
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'PUT', url, error, duration);
      throw error;
    }
  }
};