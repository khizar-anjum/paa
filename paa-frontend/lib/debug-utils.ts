/**
 * Frontend Debug Utilities for Personal AI Assistant
 * Provides client-side debug logging for API calls
 */

class FrontendDebugLogger {
  private debugMode: boolean;
  private apiCallsEnabled: boolean;
  
  constructor() {
    this.debugMode = process.env.NEXT_PUBLIC_DEBUG_MODE === 'true';
    this.apiCallsEnabled = process.env.NEXT_PUBLIC_DEBUG_API_CALLS === 'true';
    
    if (this.debugMode) {
      console.log('%c🐛 Frontend Debug Mode Enabled', 'color: #9333ea; font-weight: bold; font-size: 14px;');
      console.log(`%c📊 API Call Logging: ${this.apiCallsEnabled ? '✅ ON' : '❌ OFF'}`, 'color: #06b6d4; font-weight: bold;');
    }
  }
  
  logApiCall(method: string, url: string, data?: any): string {
    if (!this.debugMode || !this.apiCallsEnabled) return '';
    
    const callId = `api_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const timestamp = new Date();
    
    console.group(`🔵 API Call: ${method.toUpperCase()} ${url}`);
    console.log('📅 Timestamp:', timestamp.toISOString());
    console.log('🆔 Call ID:', callId);
    if (data) {
      console.log('📤 Request Data:', data);
    }
    console.groupEnd();
    
    return callId;
  }
  
  logApiResponse(callId: string, method: string, url: string, response: any, duration: number, status: number = 200) {
    if (!this.debugMode || !this.apiCallsEnabled || !callId) return;
    
    const statusColor = status < 400 ? '#10b981' : '#ef4444';
    const durationColor = duration < 1000 ? '#10b981' : duration < 3000 ? '#f59e0b' : '#ef4444';
    
    console.group(`🟢 API Response: ${method.toUpperCase()} ${url}`);
    console.log(`⏱️ Duration: %c${duration}ms%c`, `color: ${durationColor}; font-weight: bold;`, 'color: inherit;');
    console.log(`📊 Status: %c${status}%c`, `color: ${statusColor}; font-weight: bold;`, 'color: inherit;');
    console.log('📥 Response Data:', response);
    console.groupEnd();
  }
  
  logApiError(callId: string, method: string, url: string, error: any, duration: number) {
    if (!this.debugMode || !this.apiCallsEnabled || !callId) return;
    
    console.group(`🔴 API Error: ${method.toUpperCase()} ${url}`);
    console.log(`⏱️ Duration: %c${duration}ms%c`, 'color: #ef4444; font-weight: bold;', 'color: inherit;');
    console.log(`❌ Status: %c${error.response?.status || 'N/A'}%c`, 'color: #ef4444; font-weight: bold;', 'color: inherit;');
    console.log('💥 Error:', error);
    console.groupEnd();
  }
  
  logUserAction(action: string, data?: any) {
    if (!this.debugMode) return;
    
    console.log(`👆 User Action: %c${action}%c`, 'color: #059669; font-weight: bold;', 'color: inherit;');
    if (data) {
      console.log('   Data:', data);
    }
  }
  
  // Performance monitoring
  measurePerformance<T>(name: string, fn: () => T): T {
    if (!this.debugMode) return fn();
    
    const start = performance.now();
    const result = fn();
    const duration = performance.now() - start;
    
    console.log(`⚡ Performance: %c${name}%c took %c${duration.toFixed(2)}ms%c`,
      'color: #f59e0b; font-weight: bold;', 'color: inherit;',
      'color: #10b981; font-weight: bold;', 'color: inherit;'
    );
    
    return result;
  }
}

// Global debug logger instance
export const debugLogger = new FrontendDebugLogger();