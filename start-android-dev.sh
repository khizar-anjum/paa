#!/bin/bash

# PAA Android Development Environment Script
# This script builds the mobile version and launches Android development

echo "🚀 Starting PAA Android Development Environment"
echo "================================================"

# Check if backend is running
echo "🔍 Checking backend status..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend not running at localhost:8000"
    echo "Please start the backend first with:"
    echo "  cd paa-backend && source venv/bin/activate && uvicorn main:app --reload"
    exit 1
fi
echo "✅ Backend is running"

# Navigate to frontend directory
cd paa-frontend || exit 1

# Build Next.js static export for mobile
echo ""
echo "📦 Building Next.js mobile export..."
echo "This may take a minute..."
BUILD_TARGET=mobile npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please check the errors above."
    exit 1
fi

# Sync with Capacitor
echo ""
echo "🔄 Syncing with Capacitor..."
npx cap sync android

if [ $? -ne 0 ]; then
    echo "❌ Capacitor sync failed. Please check the errors above."
    exit 1
fi

# Provide options to the user
echo ""
echo "✅ Android development environment ready!"
echo ""
echo "Choose an option:"
echo "1) Open in Android Studio"
echo "2) Run on connected device/emulator with live reload"
echo "3) Run on connected device/emulator (no live reload)"
echo "4) Build APK only"
echo ""
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "📱 Opening Android Studio..."
        npx cap open android
        echo ""
        echo "📝 Instructions:"
        echo "1. Wait for Android Studio to load and sync"
        echo "2. Click the 'Run' button (green play icon) to launch on emulator/device"
        echo "3. The web app remains available at localhost:3000"
        ;;
    2)
        echo "▶️  Starting with live reload..."
        echo "Please enter your computer's IP address (for live reload):"
        read -p "IP Address: " ip_address
        npx cap run android --live-reload --host=$ip_address
        ;;
    3)
        echo "▶️  Running on Android device/emulator..."
        npx cap run android
        ;;
    4)
        echo "🔨 Building APK..."
        cd paa-frontend/android
        ./gradlew assembleDebug
        echo ""
        echo "✅ APK built successfully!"
        echo "📍 Location: paa-frontend/android/app/build/outputs/apk/debug/app-debug.apk"
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "💡 Tips:"
echo "- Web app remains available at http://localhost:3000"
echo "- Backend API is at http://localhost:8000"
echo "- For Android emulator, API is accessible at http://10.0.2.2:8000"
echo "- For physical device, use your computer's IP address"
