# Personal AI Assistant (PAA) - Frontend Summary

## Overview
Next.js 15.3.5 application with TypeScript, providing a modern interface for a Personal AI Assistant focused on habit tracking and goal achievement. Built with App Router architecture and Tailwind CSS.

## Tech Stack
- **Framework**: Next.js 15.3.5 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 3.3.0
- **State Management**: React Context API
- **HTTP Client**: Axios 1.6.0
- **Icons**: Lucide React 0.400.0
- **Notifications**: Sonner 1.4.0

## Directory Structure

### Root Configuration
- `package.json` - Dependencies and scripts
- `next.config.js` - Next.js configuration
- `tsconfig.json` - TypeScript config with path mapping
- `tailwind.config.ts` - Tailwind CSS configuration
- `middleware.ts` - Route protection middleware

### App Directory (`/app/`)
- `layout.tsx` - Root layout with auth provider
- `page.tsx` - Landing page with hero section
- `globals.css` - Tailwind imports

#### Authentication Pages
- `login/page.tsx` - User login form
- `register/page.tsx` - User registration form

#### Dashboard Section
- `dashboard/layout.tsx` - Dashboard layout with sidebar
- `dashboard/page.tsx` - Main dashboard overview

### Library (`/lib/`)
- `auth-context.tsx` - Authentication context provider

## Routing Structure

### Public Routes
- `/` - Landing page
- `/login` - User authentication
- `/register` - New user registration

### Protected Routes (Dashboard)
- `/dashboard` - Main dashboard
- `/dashboard/habits` - Habit management (planned)
- `/dashboard/chat` - AI chat interface (planned)
- `/dashboard/analytics` - Progress analytics (planned)
- `/dashboard/checkin` - Daily mood check-in (planned)

## Key Components

### Authentication System
**File**: `lib/auth-context.tsx`
- JWT-based authentication with local storage
- Cookie support for middleware protection
- Automatic session management
- API integration with backend

**Features**:
- Login/register/logout functionality
- Token persistence in localStorage and cookies
- User state management
- Automatic redirection based on auth status

### Route Protection
**File**: `middleware.ts`
- Protects dashboard routes from unauthenticated access
- Redirects authenticated users away from auth pages
- Cookie-based authentication checks

### Dashboard Layout
**File**: `dashboard/layout.tsx`
- Sidebar navigation with user info
- Logout functionality
- Responsive design

## API Integration
- **Base URL**: Configurable via `NEXT_PUBLIC_API_URL`
- **Authentication**: Bearer token in headers
- **Endpoints**:
  - `POST /register` - User registration
  - `POST /token` - User login
  - `GET /users/me` - Current user profile

## UI/UX Design
- **Color Scheme**: Blue primary with gray accents
- **Typography**: Inter font
- **Icons**: Lucide React (Brain, Home, Target, etc.)
- **Layout**: Responsive grid system
- **Notifications**: Toast messages via Sonner

## Current Implementation Status

### Completed Features
- ✅ Complete authentication system
- ✅ Protected routing with middleware
- ✅ Dashboard layout and navigation
- ✅ Landing page and auth pages
- ✅ User session management

### Planned Features (Routes Exist)
- ⏳ Habit tracking system
- ⏳ AI chat interface
- ⏳ Analytics dashboard
- ⏳ Daily mood check-in
- ⏳ React Query integration

## File Connections
1. `app/layout.tsx` → wraps app with `AuthProvider`
2. `middleware.ts` → uses cookies set by `AuthProvider`
3. `dashboard/layout.tsx` → uses `useAuth` hook for user data
4. All pages → use `useAuth` hook for auth state
5. `auth-context.tsx` → manages all API communications

## Security Features
- Route protection via middleware
- Secure token storage and cleanup
- CSRF protection with cookies
- Input validation and error handling

## Development Notes
- Well-structured for expansion
- Follows Next.js best practices
- TypeScript throughout for type safety
- Ready for additional feature implementation