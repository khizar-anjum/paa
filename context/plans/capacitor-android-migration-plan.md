# Capacitor.js Android/iOS Migration Plan for PAA

## Overview
This plan outlines the complete process for adding Android and iOS mobile app capabilities to the Personal AI Assistant (PAA) Next.js application using Capacitor.js, with Android as the primary focus. 

**IMPORTANT**: The existing Next.js web application will remain fully functional and unchanged. This plan adds mobile app capabilities alongside the web app, not replacing it.

## Key Principles
- **Web App Preservation**: The existing Next.js web app continues to work exactly as it does now
- **Dual Deployment**: Same codebase serves both web (via `npm run dev/start`) and mobile (via Capacitor)
- **No Breaking Changes**: All current web functionality remains intact
- **Build Separation**: Separate build processes for web and mobile deployments

## Architecture Strategy

### Current State (Unchanged)
- **Web App**: Next.js with SSR/SSG at localhost:3000
- **Backend**: FastAPI at localhost:8000
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with web storage

### Target State (Addition)
- **Web App**: Continues exactly as-is
- **Mobile App**: Static Next.js export wrapped with Capacitor
- **Shared Backend**: Same FastAPI backend serves both web and mobile
- **Unified Codebase**: Single Next.js codebase with conditional mobile adaptations

## Phase 1: Preparation & Analysis (Day 1-2)

### 1.1 Dual Build Strategy
- Keep existing `npm run dev` and `npm run build` for web app
- Add new scripts for mobile builds: `npm run build:mobile`
- Use environment variables to conditionally handle platform differences

### 1.2 Code Organization
```
paa-frontend/
├── package.json          # Add mobile-specific scripts
├── next.config.js        # Keep web config
├── next.config.mobile.js # Add mobile-specific config
├── capacitor.config.json # Mobile app configuration
└── lib/
    ├── api/             # Shared API code
    └── utils/
        └── platform.ts  # Platform detection utilities
```

### 1.3 Platform Detection
```typescript
// lib/utils/platform.ts
export const isMobileApp = () => {
  return typeof window !== 'undefined' && window.Capacitor !== undefined;
};

export const getApiUrl = () => {
  if (isMobileApp()) {
    // For mobile app, use absolute URL
    return process.env.NEXT_PUBLIC_MOBILE_API_URL || 'http://10.0.2.2:8000';
  }
  // For web app, use relative URLs as before
  return '';
};
```

## Phase 2: Next.js Mobile Configuration (Day 3-5)

### 2.1 Separate Build Configurations

#### Web Configuration (next.config.js - UNCHANGED)
```javascript
// Existing web configuration remains exactly as-is
module.exports = {
  // Current web configuration
};
```

#### Mobile Configuration (next.config.mobile.js - NEW)
```javascript
// New mobile-specific configuration
module.exports = {
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  // Mobile-specific environment variables
  env: {
    NEXT_PUBLIC_IS_MOBILE_BUILD: 'true'
  }
};
```

### 2.2 Package.json Scripts
```json
{
  "scripts": {
    // Existing web scripts (unchanged)
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    
    // New mobile scripts
    "build:mobile": "next build --config next.config.mobile.js",
    "cap:sync": "npm run build:mobile && npx cap sync",
    "cap:android": "npm run cap:sync && npx cap open android",
    "cap:ios": "npm run cap:sync && npx cap open ios"
  }
}
```

### 2.3 API Integration Updates
- Create wrapper functions that detect platform and adjust API calls
- Web app continues using relative URLs
- Mobile app uses absolute URLs to backend

```typescript
// lib/api/client.ts
import { isMobileApp, getApiUrl } from '@/lib/utils/platform';

export const apiClient = {
  get: async (path: string) => {
    const baseUrl = getApiUrl();
    const url = `${baseUrl}${path}`;
    
    // Add mobile-specific headers if needed
    const headers = {
      'Content-Type': 'application/json',
      ...(isMobileApp() ? { 'X-Platform': 'mobile' } : {})
    };
    
    return fetch(url, { headers });
  }
  // ... other methods
};
```

## Phase 3: Capacitor Installation & Setup (Day 6-7)

### 3.1 Core Installation
```bash
cd paa-frontend
npm install @capacitor/core @capacitor/cli
npm install @capacitor/android @capacitor/ios
npx cap init "PAA" "com.paa.app"
```

### 3.2 Capacitor Configuration
```json
// capacitor.config.json
{
  "appId": "com.paa.app",
  "appName": "PAA",
  "webDir": "out",
  "server": {
    "androidScheme": "https",
    "cleartext": true, // for local development
    "allowNavigation": ["localhost", "10.0.2.2"] // Android emulator
  },
  "plugins": {
    "SplashScreen": {
      "launchAutoHide": false,
      "backgroundColor": "#ffffff"
    }
  }
}
```

## Phase 4: Android-Specific Setup (Day 8-10)

### 4.1 Android Platform Addition
```bash
npx cap add android
```

### 4.2 Android Development Script
```bash
#!/bin/bash
# start-android-dev.sh

echo "🚀 Starting PAA Android Development Environment"

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "⚠️  Backend not running. Please start the backend first."
    exit 1
fi

# Build Next.js static export for mobile
echo "📦 Building Next.js mobile export..."
cd paa-frontend
npm run build:mobile

# Sync with Capacitor
echo "🔄 Syncing with Capacitor..."
npx cap sync android

# Option 1: Open in Android Studio
echo "📱 Opening Android Studio..."
npx cap open android

# Option 2: Run directly on device/emulator (uncomment if preferred)
# echo "▶️  Running on Android device/emulator..."
# npx cap run android --livereload --external

echo "✅ Android development environment ready!"
echo "📝 Note: Web app remains available at localhost:3000"
```

### 4.3 Android Permissions
```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 4.4 Backend CORS Update
```python
# paa-backend/main.py
# Update CORS to accept mobile app requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Web app (unchanged)
        "capacitor://localhost",  # iOS
        "http://localhost",        # Android
        "https://localhost"        # Android HTTPS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Phase 5: Mobile UI/UX Adaptations (Day 11-13)

### 5.1 Conditional Mobile Enhancements
```typescript
// components/MobileWrapper.tsx
import { isMobileApp } from '@/lib/utils/platform';

export function MobileWrapper({ children }) {
  if (isMobileApp()) {
    return (
      <div className="mobile-app-wrapper">
        {/* Add mobile-specific UI elements */}
        {children}
      </div>
    );
  }
  return children; // Web app renders normally
}
```

### 5.2 Navigation Adjustments
- Web app keeps existing navigation
- Mobile app adds hardware back button handling
- Conditional rendering based on platform

### 5.3 Responsive Improvements
- Touch targets optimized for mobile when detected
- Web app retains current desktop-optimized interactions
- Shared responsive classes with platform-specific overrides

## Phase 6: Native Features Integration (Day 14-16)

### 6.1 Core Capacitor Plugins
```bash
npm install @capacitor/preferences  # Secure storage for mobile
npm install @capacitor/network      # Network status
npm install @capacitor/push-notifications  # Mobile notifications
npm install @capacitor/splash-screen  # App splash screen
npm install @capacitor/status-bar    # Status bar control
```

### 6.2 Platform-Specific Storage
```typescript
// lib/storage.ts
import { isMobileApp } from '@/utils/platform';
import { Preferences } from '@capacitor/preferences';

export const storage = {
  setItem: async (key: string, value: string) => {
    if (isMobileApp()) {
      await Preferences.set({ key, value });
    } else {
      localStorage.setItem(key, value); // Web app unchanged
    }
  },
  
  getItem: async (key: string) => {
    if (isMobileApp()) {
      const { value } = await Preferences.get({ key });
      return value;
    } else {
      return localStorage.getItem(key); // Web app unchanged
    }
  }
};
```

### 6.3 Push Notifications (Mobile Only)
- Configure Firebase Cloud Messaging for Android
- Web app continues without push notifications or uses web push
- Conditional initialization based on platform

## Phase 7: Authentication & Security (Day 17-18)

### 7.1 Unified Auth with Platform Detection
```typescript
// lib/auth.ts
import { storage } from './storage';

export const authService = {
  saveToken: async (token: string) => {
    await storage.setItem('auth_token', token);
  },
  
  getToken: async () => {
    return await storage.getItem('auth_token');
  },
  
  // Works identically for both web and mobile
  login: async (credentials) => {
    const response = await apiClient.post('/login', credentials);
    await authService.saveToken(response.token);
    return response;
  }
};
```

### 7.2 Security Considerations
- Web app: Continues using httpOnly cookies and localStorage
- Mobile app: Uses Capacitor Preferences for secure storage
- Backend: Single auth system serves both platforms

## Phase 8: Build & Deployment Process (Day 19-20)

### 8.1 Development Workflow
```bash
# Web Development (unchanged)
npm run dev  # Runs at localhost:3000

# Mobile Development (new)
./start-android-dev.sh  # Builds and opens Android app
```

### 8.2 Production Builds
```bash
# Web Production (unchanged)
npm run build
npm run start

# Mobile Production (new)
npm run build:mobile
npx cap sync android
cd android && ./gradlew bundleRelease
```

### 8.3 CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy Web and Build Mobile

jobs:
  deploy-web:
    # Existing web deployment unchanged
    
  build-android:
    # New Android build job
    steps:
      - uses: actions/checkout@v2
      - name: Build Mobile Export
        run: npm run build:mobile
      - name: Build Android APK
        run: |
          npx cap sync android
          cd android
          ./gradlew assembleRelease
```

## Phase 9: Testing Strategy (Day 21-22)

### 9.1 Testing Matrix
- **Web App**: Continue existing testing (unchanged)
- **Android App**: Test on multiple devices and API levels
- **Cross-platform**: Ensure feature parity between web and mobile

### 9.2 Test Scenarios
- Web app functionality remains identical
- Mobile app handles network changes gracefully
- Authentication works across both platforms
- Data syncs correctly between web and mobile sessions

## Phase 10: iOS Preparation (Future)

### 10.1 iOS Setup (When Ready)
```bash
npx cap add ios
npx cap sync ios
npx cap open ios
```

### 10.2 iOS Development Script
```bash
#!/bin/bash
# start-ios-dev.sh (future)
# Similar to Android script but for iOS
```

## Implementation Checklist

### Essential Tasks (Preserving Web App)
- [ ] Create next.config.mobile.js (separate from web config)
- [ ] Add platform detection utilities
- [ ] Install Capacitor without affecting web build
- [ ] Create conditional API URL handling
- [ ] Add Android platform
- [ ] Create start-android-dev.sh script
- [ ] Update backend CORS for mobile origins
- [ ] Test web app remains unchanged
- [ ] Test Android app functionality
- [ ] Document dual deployment process

### Build Scripts Verification
- [ ] `npm run dev` still starts web app at localhost:3000
- [ ] `npm run build` still builds web app for production
- [ ] `npm run build:mobile` creates static export for Capacitor
- [ ] `./start-android-dev.sh` launches Android development

## File Structure (Final)
```
paa/
├── paa-frontend/
│   ├── next.config.js           # Web config (unchanged)
│   ├── next.config.mobile.js    # Mobile config (new)
│   ├── capacitor.config.json    # Capacitor config (new)
│   ├── android/                 # Android project (new, generated)
│   ├── ios/                     # iOS project (future, generated)
│   └── lib/
│       └── utils/
│           └── platform.ts      # Platform detection (new)
├── start-android-dev.sh         # Android development script (new)
├── start-ios-dev.sh            # iOS development script (future)
└── paa-backend/
    └── main.py                  # Update CORS only
```

## Key Differences from Web App

| Feature | Web App | Mobile App |
|---------|---------|------------|
| Build Process | `npm run build` (SSR/SSG) | `npm run build:mobile` (static) |
| API URLs | Relative paths | Absolute paths to backend |
| Storage | localStorage | Capacitor Preferences |
| Navigation | Browser routing | Native + browser routing |
| Notifications | Browser notifications (if any) | Push notifications |
| Authentication | Cookies + localStorage | Secure Preferences |
| Deployment | Vercel/hosting service | App stores |

## Success Criteria
- [ ] Web app works exactly as before at localhost:3000
- [ ] Android app runs with all features working
- [ ] Single codebase serves both platforms
- [ ] No breaking changes to existing functionality
- [ ] Clear separation between web and mobile builds
- [ ] Both platforms can run simultaneously in development

## Risk Mitigation

### Critical Safeguards
1. **Separate Build Configs**: Web and mobile builds never interfere
2. **Platform Detection**: Conditional code execution prevents conflicts
3. **Backward Compatibility**: All web-specific code remains untouched
4. **Testing**: Comprehensive testing ensures web app stability

### Rollback Strategy
If issues arise, simply:
1. Don't run mobile build scripts
2. Web app continues working as normal
3. Remove android/ and ios/ folders if needed
4. Capacitor remains as unused dependency

## Timeline Summary
- **Week 1**: Setup and configuration (no web app changes)
- **Week 2**: Mobile adaptations (conditional additions only)
- **Week 3**: Testing both platforms thoroughly
- **Week 4**: Documentation and deployment preparation

## Conclusion
This plan ensures the PAA web application remains fully functional and unchanged while adding native mobile capabilities through Capacitor.js. The dual-platform approach allows serving both web and mobile users from a single codebase with minimal additional complexity.