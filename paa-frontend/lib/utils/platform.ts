/**
 * Platform detection utilities for handling web vs mobile app differences
 * These utilities ensure the web app remains unchanged while adding mobile capabilities
 */

declare global {
  interface Window {
    Capacitor?: any;
  }
}

/**
 * Detects if the app is running as a mobile app (via Capacitor)
 * Returns false for web app, maintaining existing web behavior
 */
export const isMobileApp = (): boolean => {
  if (typeof window === 'undefined') {
    return false; // Server-side rendering
  }
  
  // Check for Capacitor object
  const hasCapacitor = window.Capacitor !== undefined;
  
  // Also check for mobile build environment variable
  const isMobileBuild = process.env.NEXT_PUBLIC_IS_MOBILE_BUILD === 'true';
  
  // Debug logging
  if (typeof window !== 'undefined' && window.console) {
    console.log('Platform Detection:', {
      hasCapacitor,
      isMobileBuild,
      userAgent: navigator.userAgent,
      origin: window.location.origin
    });
  }
  
  return hasCapacitor || isMobileBuild;
};

/**
 * Gets the appropriate API base URL based on platform
 * Web app uses empty string (relative URLs) as before
 * Mobile app uses absolute URL to backend
 */
export const getApiUrl = (): string => {
  const mobile = isMobileApp();
  
  if (mobile) {
    // For mobile app, use absolute URL
    const mobileApiUrl = process.env.NEXT_PUBLIC_MOBILE_API_URL || 'http://192.168.1.216:8000';
    
    // Debug logging
    if (typeof window !== 'undefined' && window.console) {
      console.log('Mobile API URL:', mobileApiUrl);
    }
    
    return mobileApiUrl;
  }
  
  // For web app, use relative URLs as before (no change to existing behavior)
  if (typeof window !== 'undefined' && window.console) {
    console.log('Web API URL: (relative)');
  }
  
  return '';
};

/**
 * Gets the appropriate API URL for a given path
 * Maintains backward compatibility for web app
 */
export const getApiEndpoint = (path: string): string => {
  const baseUrl = getApiUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const fullUrl = `${baseUrl}${normalizedPath}`;
  
  // Debug logging
  if (typeof window !== 'undefined' && window.console) {
    console.log(`API Endpoint for ${path}:`, fullUrl);
  }
  
  return fullUrl;
};

/**
 * Platform-specific feature flags
 */
export const platformFeatures = {
  hasPushNotifications: isMobileApp(),
  hasNativeStorage: isMobileApp(),
  hasHardwareBackButton: isMobileApp(),
  hasBiometricAuth: isMobileApp(),
  hasNativeShare: isMobileApp(),
};

/**
 * Platform info for debugging and analytics
 */
export const getPlatformInfo = () => {
  if (isMobileApp() && typeof window !== 'undefined' && window.Capacitor) {
    return {
      platform: 'mobile',
      isNative: true,
      isWeb: false,
      isAndroid: window.Capacitor.getPlatform?.() === 'android',
      isIOS: window.Capacitor.getPlatform?.() === 'ios',
    };
  }
  
  return {
    platform: 'web',
    isNative: false,
    isWeb: true,
    isAndroid: false,
    isIOS: false,
  };
};