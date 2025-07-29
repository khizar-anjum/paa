const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface TimeStatus {
  using_fake_time: boolean;
  current_time: string;
  real_time: string;
  fake_start_time?: string;
  real_start_time?: string;
  time_multiplier?: number;
  fake_minutes_per_real_second?: number;
  real_elapsed_seconds?: number;
  fake_elapsed_time?: number;
}

export interface SchedulerStatus {
  running: boolean;
  current_fake_time: string;
  jobs: Array<{
    id: string;
    interval_minutes: number;
    last_run_fake_time?: string;
    is_active: boolean;
  }>;
}

export interface TimeStatusResponse {
  success: boolean;
  time_service: TimeStatus;
  fake_scheduler: SchedulerStatus;
}

export interface TimeControlResponse {
  success: boolean;
  message: string;
  [key: string]: any;
}

class DebugApi {
  private getAuthHeaders() {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  async getTimeStatus(): Promise<TimeStatusResponse> {
    const response = await fetch(`${API_URL}/debug/time/status`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }

  async startFakeTime(timeMultiplier: number = 600, fakeStartTime?: string): Promise<TimeControlResponse> {
    const body: any = { time_multiplier: timeMultiplier };
    if (fakeStartTime) {
      body.fake_start_time = fakeStartTime;
    }

    const response = await fetch(`${API_URL}/debug/time/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify(body),
    });
    return response.json();
  }

  async stopFakeTime(): Promise<TimeControlResponse> {
    const response = await fetch(`${API_URL}/debug/time/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
    });
    return response.json();
  }

  async setTimeMultiplier(multiplier: number): Promise<TimeControlResponse> {
    const response = await fetch(`${API_URL}/debug/time/set-multiplier`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify({ multiplier }),
    });
    return response.json();
  }

  async jumpToTime(targetTime: string): Promise<TimeControlResponse> {
    const response = await fetch(`${API_URL}/debug/time/jump`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify({ target_time: targetTime }),
    });
    return response.json();
  }

  // New debug endpoints
  async getDebugStatus(): Promise<any> {
    const response = await fetch(`${API_URL}/debug/status`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }

  async getRecentPipelineExecutions(): Promise<any> {
    const response = await fetch(`${API_URL}/debug/pipeline/recent-executions`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }

  async getVectorStoreStats(): Promise<any> {
    const response = await fetch(`${API_URL}/debug/vector-store/stats`, {
      headers: this.getAuthHeaders(),
    });
    return response.json();
  }

  async clearDebugLogs(): Promise<any> {
    const response = await fetch(`${API_URL}/debug/clear-logs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
    });
    return response.json();
  }
}

export const debugApi = new DebugApi();