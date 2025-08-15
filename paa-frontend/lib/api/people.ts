import axios from 'axios';
import { debugLogger } from '../debug-utils';
import { getApiUrl } from '@/lib/utils/platform';

const getApiUrlForPeople = () => {
  const mobileUrl = getApiUrl();
  return mobileUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

// Types
export interface Person {
  id: number;
  name: string;
  how_you_know_them?: string;
  pronouns?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface PersonCreate {
  name: string;
  how_you_know_them?: string;
  pronouns?: string;
  description?: string;
}

export interface PersonUpdate {
  name?: string;
  how_you_know_them?: string;
  pronouns?: string;
  description?: string;
}

// API functions
export const peopleApi = {
  async getAll(): Promise<Person[]> {
    const startTime = Date.now();
    const url = `${getApiUrlForPeople()}/people`;
    
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

  async getById(id: number): Promise<Person> {
    const startTime = Date.now();
    const url = `${getApiUrlForPeople()}/people/${id}`;
    const requestData = { id };
    
    const callId = debugLogger.logApiCall('GET', url, requestData);
    
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

  async create(person: PersonCreate): Promise<Person> {
    const startTime = Date.now();
    const url = `${getApiUrlForPeople()}/people`;
    const requestData = { ...person };
    
    const callId = debugLogger.logApiCall('POST', url, requestData);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(url, person, {
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

  async update(id: number, person: PersonUpdate): Promise<Person> {
    const startTime = Date.now();
    const url = `${getApiUrlForPeople()}/people/${id}`;
    const requestData = { id, ...person };
    
    const callId = debugLogger.logApiCall('PUT', url, requestData);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(url, person, {
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
  },

  async delete(id: number): Promise<void> {
    const startTime = Date.now();
    const url = `${getApiUrlForPeople()}/people/${id}`;
    const requestData = { id };
    
    const callId = debugLogger.logApiCall('DELETE', url, requestData);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.delete(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const duration = Date.now() - startTime;
      
      debugLogger.logApiResponse(callId, 'DELETE', url, response.data, duration, response.status);
    } catch (error: any) {
      const duration = Date.now() - startTime;
      debugLogger.logApiError(callId, 'DELETE', url, error, duration);
      throw error;
    }
  }
};