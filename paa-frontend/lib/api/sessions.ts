import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Session {
  id: string;
  name: string;
  created_at: string;
  last_message_at?: string;
  message_count: number;
  is_active: boolean;
}

export interface SessionCreate {
  name: string;
}

export interface SessionUpdate {
  name?: string;
  is_active?: boolean;
}

export const sessionAPI = {
  // Create a new session
  create: async (data: SessionCreate): Promise<Session> => {
    const response = await api.post('/sessions', data);
    return response.data;
  },

  // Create a new session with auto-generated name
  createAuto: async (): Promise<Session> => {
    const response = await api.post('/sessions/auto');
    return response.data;
  },

  // Generate name for a session based on its content
  generateName: async (sessionId: string): Promise<{ message: string; name: string }> => {
    const response = await api.put(`/sessions/${sessionId}/generate-name`);
    return response.data;
  },

  // Get all sessions for current user
  list: async (): Promise<Session[]> => {
    const response = await api.get('/sessions');
    return response.data;
  },

  // Update a session
  update: async (sessionId: string, data: SessionUpdate): Promise<Session> => {
    const response = await api.put(`/sessions/${sessionId}`, data);
    return response.data;
  },

  // Delete a session
  delete: async (sessionId: string): Promise<void> => {
    await api.delete(`/sessions/${sessionId}`);
  }
};