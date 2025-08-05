import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface Commitment {
  id: number;
  user_id: number;
  task_description: string;
  original_message?: string;
  deadline?: string;
  status: 'pending' | 'completed' | 'missed' | 'dismissed' | 'active' | 'archived';
  created_from_conversation_id?: number;
  last_reminded_at?: string;
  reminder_count: number;
  created_at: string;
  // New unified system fields
  recurrence_pattern: 'none' | 'daily' | 'weekly' | 'monthly' | 'custom';
  recurrence_interval: number;
  recurrence_days?: string;
  recurrence_end_date?: string;
  due_time?: string;
  completion_count: number;
  last_completed_at?: string;
  reminder_settings?: any;
  // Helper properties
  is_recurring?: boolean;
  completed_today?: boolean;
}

export interface CommitmentUpdate {
  status?: string;
  deadline?: string;
  task_description?: string;
  recurrence_pattern?: 'none' | 'daily' | 'weekly' | 'monthly' | 'custom';
  recurrence_interval?: number;
  recurrence_days?: string;
  recurrence_end_date?: string;
  due_time?: string;
  reminder_settings?: any;
}

export interface CommitmentFilters {
  status?: string;
  overdue?: boolean;
  type?: 'one_time' | 'recurring';
  recurrence?: 'daily' | 'weekly' | 'monthly';
  due?: 'today' | 'tomorrow' | 'overdue';
  sort_by?: 'created_at' | 'deadline';
  order?: 'asc' | 'desc';
}

export interface CommitmentCompletion {
  id: number;
  commitment_id: number;
  user_id: number;
  completed_at: string;
  completion_date: string;
  notes?: string;
  skipped: boolean;
}

export interface CommitmentCompletionCreate {
  notes?: string;
  completion_date?: string;
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
      if (filters?.type) params.append('type', filters.type);
      if (filters?.recurrence) params.append('recurrence', filters.recurrence);
      if (filters?.due) params.append('due', filters.due);
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

  // Complete a commitment (handles both one-time and recurring)
  async completeCommitment(id: number, completionData?: CommitmentCompletionCreate): Promise<{ message: string }> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/commitments/${id}/complete`,
        completionData || {},
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error completing commitment:', error);
      throw error;
    }
  },

  // Skip a recurring commitment for today
  async skipCommitment(id: number, notes?: string): Promise<{ message: string }> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/commitments/${id}/skip`,
        { notes },
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error skipping commitment:', error);
      throw error;
    }
  },

  // Get completions for a recurring commitment
  async getCommitmentCompletions(id: number): Promise<CommitmentCompletion[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/commitments/${id}/completions`,
        getConfig()
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching commitment completions:', error);
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
  // Check if a commitment is recurring
  isRecurring(commitment: Commitment): boolean {
    return commitment.recurrence_pattern !== 'none';
  },

  // Check if a commitment is overdue
  isOverdue(commitment: Commitment): boolean {
    // For recurring commitments, check if it should have been completed today
    if (commitmentUtils.isRecurring(commitment)) {
      return commitment.status === 'active' && !commitment.completed_today;
    }
    // For one-time commitments, check deadline
    if (!commitment.deadline || commitment.status !== 'pending') return false;
    const deadline = new Date(commitment.deadline);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return deadline < today;
  },

  // Check if a commitment is due today
  isDueToday(commitment: Commitment): boolean {
    // For recurring commitments, check if it should be done today
    if (commitmentUtils.isRecurring(commitment)) {
      return commitment.status === 'active' && !commitment.completed_today;
    }
    // For one-time commitments, check deadline
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
    // For recurring commitments, only show time if available
    if (commitmentUtils.isRecurring(commitment)) {
      if (commitment.due_time) {
        return `Due at ${commitment.due_time}`;
      }
      return ''; // Show nothing when no specific time
    }
    
    // For one-time commitments, show deadline
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

  // Format recurrence pattern for display
  formatRecurrence(commitment: Commitment): string {
    if (!commitmentUtils.isRecurring(commitment)) return 'One-time';
    
    const pattern = commitment.recurrence_pattern;
    if (pattern === 'daily') return 'Daily';
    if (pattern === 'weekly') return 'Weekly';
    if (pattern === 'monthly') return 'Monthly';
    return 'Custom';
  },

  // Get completion streak info for recurring commitments
  getStreakInfo(commitment: Commitment): { current: number; total: number } {
    if (!commitmentUtils.isRecurring(commitment)) {
      return { current: 0, total: commitment.completion_count || 0 };
    }
    
    // For now, return basic info - could be enhanced with actual completion data
    return {
      current: commitment.completed_today ? 1 : 0,
      total: commitment.completion_count || 0
    };
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