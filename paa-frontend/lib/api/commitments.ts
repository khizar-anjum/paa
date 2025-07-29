import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface Commitment {
  id: number;
  user_id: number;
  task_description: string;
  original_message?: string;
  deadline?: string;
  status: 'pending' | 'completed' | 'missed' | 'dismissed';
  created_from_conversation_id?: number;
  last_reminded_at?: string;
  reminder_count: number;
  created_at: string;
}

export interface CommitmentUpdate {
  status?: string;
  deadline?: string;
}

export interface CommitmentFilters {
  status?: string;
  overdue?: boolean;
  sort_by?: 'created_at' | 'deadline';
  order?: 'asc' | 'desc';
}

export interface ProactiveMessage {
  id: number;
  user_id: number;
  message_type: string;
  content: string;
  related_commitment_id?: number;
  scheduled_for?: string;
  sent_at?: string;
  user_responded: boolean;
  response_content?: string;
}

// Helper function to get auth token
const getAuthToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('token');
  }
  return null;
};

// Helper function to create axios config with auth
const getConfig = () => {
  const token = getAuthToken();
  return {
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    },
  };
};

// API Functions
export const commitmentAPI = {
  // Get all commitments with optional filters
  async getCommitments(filters?: CommitmentFilters): Promise<Commitment[]> {
    try {
      const params = new URLSearchParams();
      
      if (filters?.status) params.append('status', filters.status);
      if (filters?.overdue !== undefined) params.append('overdue', filters.overdue.toString());
      if (filters?.sort_by) params.append('sort_by', filters.sort_by);
      if (filters?.order) params.append('order', filters.order);
      
      const queryString = params.toString();
      const url = `${API_BASE_URL}/commitments${queryString ? `?${queryString}` : ''}`;
      
      const response = await axios.get(url, getConfig());
      return response.data;
    } catch (error) {
      console.error('Error fetching commitments:', error);
      throw error;
    }
  },

  // Update a commitment
  async updateCommitment(id: number, updates: CommitmentUpdate): Promise<Commitment> {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/commitments/${id}`,
        updates,
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error updating commitment:', error);
      throw error;
    }
  },

  // Complete a commitment
  async completeCommitment(id: number): Promise<{ message: string }> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/commitments/${id}/complete`,
        {},
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error completing commitment:', error);
      throw error;
    }
  },

  // Dismiss a commitment
  async dismissCommitment(id: number): Promise<{ message: string }> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/commitments/${id}/dismiss`,
        {},
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error dismissing commitment:', error);
      throw error;
    }
  },

  // Postpone a commitment
  async postponeCommitment(id: number, newDeadline: string): Promise<{ message: string }> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/commitments/${id}/postpone`,
        { deadline: newDeadline },
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error postponing commitment:', error);
      throw error;
    }
  },

  // Delete a commitment
  async deleteCommitment(id: number): Promise<{ message: string }> {
    try {
      const response = await axios.delete(
        `${API_BASE_URL}/commitments/${id}`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error deleting commitment:', error);
      throw error;
    }
  },

  // Get reminders for a specific commitment
  async getCommitmentReminders(id: number): Promise<ProactiveMessage[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/commitments/${id}/reminders`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching commitment reminders:', error);
      throw error;
    }
  },
};

// Utility functions
export const commitmentUtils = {
  // Check if a commitment is overdue
  isOverdue(commitment: Commitment): boolean {
    if (!commitment.deadline || commitment.status !== 'pending') return false;
    const deadline = new Date(commitment.deadline);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return deadline < today;
  },

  // Check if a commitment is due today
  isDueToday(commitment: Commitment): boolean {
    if (!commitment.deadline || commitment.status !== 'pending') return false;
    const deadline = new Date(commitment.deadline);
    const today = new Date();
    return deadline.toDateString() === today.toDateString();
  },

  // Get days until deadline (negative if overdue)
  getDaysUntilDeadline(commitment: Commitment): number | null {
    if (!commitment.deadline) return null;
    const deadline = new Date(commitment.deadline);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    deadline.setHours(0, 0, 0, 0);
    const diffTime = deadline.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  },

  // Format deadline for display
  formatDeadline(commitment: Commitment): string {
    if (!commitment.deadline) return 'No deadline';
    
    const deadline = new Date(commitment.deadline);
    const today = new Date();
    const daysUntil = commitmentUtils.getDaysUntilDeadline(commitment);
    
    if (daysUntil === null) return 'No deadline';
    if (daysUntil === 0) return 'Due today';
    if (daysUntil === 1) return 'Due tomorrow';
    if (daysUntil === -1) return '1 day overdue';
    if (daysUntil < 0) return `${Math.abs(daysUntil)} days overdue`;
    if (daysUntil <= 7) return `Due in ${daysUntil} days`;
    
    // For longer periods, show the actual date
    return deadline.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: deadline.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
    });
  },

  // Get status color class
  getStatusColor(commitment: Commitment): string {
    if (commitmentUtils.isOverdue(commitment)) return 'text-red-600 bg-red-50 border-red-200';
    if (commitmentUtils.isDueToday(commitment)) return 'text-amber-600 bg-amber-50 border-amber-200';
    
    switch (commitment.status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'dismissed':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'missed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'pending':
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  },

  // Get commitment priority (for sorting)
  getPriority(commitment: Commitment): number {
    if (commitmentUtils.isOverdue(commitment)) return 1; // Highest priority
    if (commitmentUtils.isDueToday(commitment)) return 2;
    if (commitment.status === 'pending') return 3;
    return 4; // Completed/dismissed have lowest priority
  }
};