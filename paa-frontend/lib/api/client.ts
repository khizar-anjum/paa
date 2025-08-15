/**
 * API client wrapper that handles platform-specific differences
 * Maintains existing web app behavior while adding mobile support
 */

import { isMobileApp, getApiEndpoint } from '@/lib/utils/platform';

interface RequestOptions extends RequestInit {
  token?: string;
}

/**
 * Platform-aware API client
 * Web app continues using relative URLs as before
 * Mobile app uses absolute URLs to backend
 */
export const apiClient = {
  /**
   * GET request with platform detection
   */
  get: async (path: string, options: RequestOptions = {}) => {
    const url = getApiEndpoint(path);
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.token ? { 'Authorization': `Bearer ${options.token}` } : {}),
      ...(isMobileApp() ? { 'X-Platform': 'mobile' } : {}),
      ...options.headers,
    };
    
    const response = await fetch(url, {
      ...options,
      method: 'GET',
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },
  
  /**
   * POST request with platform detection
   */
  post: async (path: string, body?: any, options: RequestOptions = {}) => {
    const url = getApiEndpoint(path);
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.token ? { 'Authorization': `Bearer ${options.token}` } : {}),
      ...(isMobileApp() ? { 'X-Platform': 'mobile' } : {}),
      ...options.headers,
    };
    
    const response = await fetch(url, {
      ...options,
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },
  
  /**
   * PUT request with platform detection
   */
  put: async (path: string, body?: any, options: RequestOptions = {}) => {
    const url = getApiEndpoint(path);
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.token ? { 'Authorization': `Bearer ${options.token}` } : {}),
      ...(isMobileApp() ? { 'X-Platform': 'mobile' } : {}),
      ...options.headers,
    };
    
    const response = await fetch(url, {
      ...options,
      method: 'PUT',
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },
  
  /**
   * DELETE request with platform detection
   */
  delete: async (path: string, options: RequestOptions = {}) => {
    const url = getApiEndpoint(path);
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.token ? { 'Authorization': `Bearer ${options.token}` } : {}),
      ...(isMobileApp() ? { 'X-Platform': 'mobile' } : {}),
      ...options.headers,
    };
    
    const response = await fetch(url, {
      ...options,
      method: 'DELETE',
      headers,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    // DELETE might not return a body
    const text = await response.text();
    return text ? JSON.parse(text) : null;
  },
};

/**
 * Helper function to get auth token (platform-aware)
 * This will be enhanced in later phases to use Capacitor Preferences for mobile
 */
export const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  
  // For now, both platforms use localStorage
  // This will be updated in Phase 6 to use Capacitor Preferences for mobile
  return localStorage.getItem('token');
};

/**
 * Helper function to save auth token (platform-aware)
 * This will be enhanced in later phases to use Capacitor Preferences for mobile
 */
export const saveAuthToken = (token: string): void => {
  if (typeof window === 'undefined') return;
  
  // For now, both platforms use localStorage
  // This will be updated in Phase 6 to use Capacitor Preferences for mobile
  localStorage.setItem('token', token);
};

/**
 * Helper function to clear auth token (platform-aware)
 */
export const clearAuthToken = (): void => {
  if (typeof window === 'undefined') return;
  
  // For now, both platforms use localStorage
  // This will be updated in Phase 6 to use Capacitor Preferences for mobile
  localStorage.removeItem('token');
};