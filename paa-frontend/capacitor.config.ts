import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.paa.app',
  appName: 'PAA',
  webDir: 'out',
  server: {
    androidScheme: 'http',  // Use HTTP instead of HTTPS
    cleartext: true,         // Allow cleartext traffic
    allowNavigation: ['*']   // Allow all navigation for development
  },
  android: {
    allowMixedContent: true  // Allow mixed content on Android
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: false,
      backgroundColor: '#ffffff',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true
    }
  }
};

export default config;
