# PAA Frontend Summary - Chat-First Interface

## Architecture
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript with strict type checking
- **Styling**: Tailwind CSS with custom components
- **UI Library**: Lucide React icons, Sonner for notifications
- **Markdown**: react-markdown with remark-gfm for rich text

## Chat-First Interface Design

### Core Layout System
The application uses a chat-first approach where the chat is always the primary interface:

```typescript
// Dashboard Layout (layout.tsx)
export default function DashboardLayout({ children }) {
  const isOverlayPage = [
    '/dashboard/profile',
    '/dashboard/people',
    '/dashboard/commitments', 
    '/dashboard/analytics'
  ].includes(pathname);

  return (
    <SidebarContext.Provider value={{ openSidebar }}>
      {/* Chat always rendered */}
      <PersistentChatPanel />
      
      {/* Overlays render on top when navigated to */}
      {isOverlayPage && children}
      
      {/* Sidebar available everywhere */}
      <CollapsibleSidebar />
    </SidebarContext.Provider>
  );
}
```

### Navigation Components

#### CollapsibleSidebar.tsx
- **Hamburger Toggle**: Expandable/collapsible menu
- **Navigation Items**:
  - Dashboard (Chat) - Main interface
  - Profile - User profile overlay
  - People - People management overlay
  - Commitments - Commitment management overlay
  - Analytics - Analytics dashboard overlay
  - Settings - Settings overlay
  - Sign Out - Logout action

#### PageOverlay.tsx
Wrapper component for all overlay pages:
```typescript
interface PageOverlayProps {
  title: string;
  children: React.ReactNode;
  onClose?: () => void;
  onOpenSidebar?: () => void;
}
```
- **Consistent Header**: Title and hamburger menu button
- **Blur Background**: Shows chat behind with blur effect
- **Browser History**: Integrates with browser back button

### Context System

#### SidebarContext
Shares sidebar functionality across all pages:
```typescript
const SidebarContext = createContext<{
  openSidebar: () => void;
} | null>(null);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) throw new Error('useSidebar must be used within DashboardLayout');
  return context;
};
```

## Core Components

### Chat System

#### PersistentChatPanel.tsx
The main chat interface that's always visible:
- **Multiple Conversations**: Support for multiple chat sessions
- **Message History**: Persistent conversation storage
- **AI Integration**: Natural language commitment creation
- **Always Active**: Remains functional even when overlays are open

### Commitment Management

#### CommitmentCard.tsx
Unified display for all commitment types:
- **Type Detection**: Automatically determines one-time vs recurring
- **Smart Actions**: Context-aware buttons (Complete, Skip, Edit, Delete)
- **Status Indicators**: Visual badges for different states
- **Information Display**: Consolidated single-line layout with flex-wrap

#### CreateCommitmentModal.tsx
Dynamic creation form:
- **Adaptive Fields**: Shows relevant fields based on type selection
- **Recurrence Options**: Daily, weekly, monthly patterns
- **Time Support**: Optional due times for recurring commitments
- **Validation**: Form validation with error messages

#### EditCommitmentModal.tsx
Context-aware editing:
- **Type-Specific**: Different fields for one-time vs recurring
- **Time Editing**: Support for due_time field updates
- **Status Management**: Update commitment status

#### CommitmentFilters.tsx
Advanced filtering system:
- **Type Filters**: One-time (Target icon) vs Recurring (Repeat icon)
- **Status Filters**: All, Active, Completed, etc.
- **Search**: Text search across commitments
- **Visual Design**: Pill-style toggle buttons

### Analytics Components

#### AnalyticsPage (analytics/page.tsx)
Simplified analytics dashboard:
- **Overview Cards**: 
  - Total Commitments
  - Recurring Commitments
  - One-time Commitments
  - Completion Rate
  - Completed Today
  - Longest Streak
  - Total Conversations
- **Commitment Details Table**: List view with type indicators
- **Time Range Selector**: 7, 30, or 90 day views
- **Removed Elements**: No mood tracking or completion charts

#### AnalyticsChart.tsx
Reusable chart component (currently unused after simplification)

### People Management

#### PeoplePage (people/page.tsx)
Contact management system:
- **Person Cards**: Grid layout with basic info
- **Detail View**: Full person profile with markdown
- **Edit Mode**: In-place editing with save/cancel
- **Delete Option**: Remove people with confirmation
- **Hamburger Menu**: Navigation back to chat

#### CreatePersonModal.tsx
Person creation form with fields for name, pronouns, relationship, and description

## API Integration

### Commitment API (`lib/api/commitments.ts`)
```typescript
export interface Commitment {
  id: number;
  task_description: string;
  original_message?: string;
  deadline?: string;
  recurrence_pattern: 'none' | 'daily' | 'weekly' | 'monthly';
  recurrence_interval: number;
  recurrence_days?: string;
  due_time?: string;
  status: string;
  completion_count: number;
  completed_today?: boolean;
  is_recurring?: boolean;
}

// Key functions
getCommitments(filters?: CommitmentFilters)
createCommitment(data: CommitmentCreate)
updateCommitment(id: number, data: CommitmentUpdate)
completeCommitment(id: number)
skipCommitment(id: number)
deleteCommitment(id: number)
```

### Analytics API (`lib/api/analytics.ts`)
```typescript
export interface OverviewAnalytics {
  total_commitments: number;
  recurring_commitments: number;
  one_time_commitments: number;
  completed_today: number;
  completion_rate: number;
  longest_streak: number;
  total_conversations: number;
}

getCommitmentsAnalytics(days: number)
getOverview()
getMoodAnalytics(days: number) // Still available but unused
```

### People API (`lib/api/people.ts`)
```typescript
export interface Person {
  id: number;
  name: string;
  pronouns?: string;
  how_you_know_them?: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

getAll()
create(data: PersonCreate)
update(id: number, data: PersonUpdate)
delete(id: number)
```

## State Management
- **Local State**: React hooks (useState, useEffect)
- **Context API**: SidebarContext for navigation state
- **No Redux**: Simple prop passing and local state
- **Form State**: Controlled components with validation

## Routing Structure
```
/dashboard              → Redirects to chat
/dashboard/profile      → Profile overlay
/dashboard/people       → People overlay
/dashboard/commitments  → Commitments overlay
/dashboard/analytics    → Analytics overlay
/dashboard/settings     → Settings overlay (TBD)
```

## Recent Updates

### Phase 4 Implementation
1. **Navigation Flow**: Complete overlay system with browser history
2. **Hamburger Menus**: Added to all overlay pages
3. **Sidebar Context**: Shared navigation state
4. **Commitments Integration**: Added to overlay system
5. **Analytics Simplification**: Removed charts and mood tracking

### Bug Fixes
- Fixed missing hamburger menus on overlay pages
- Resolved backend endpoint 404 errors
- Fixed field name mismatches (habit_name → commitment_name)
- Corrected Next.js build errors
- Fixed React controlled component warnings

## UI/UX Patterns

### Overlay Behavior
- **Blur Background**: Chat visible but blurred behind overlays
- **Full Height**: Overlays take full viewport height
- **Consistent Headers**: All overlays have title and hamburger menu
- **Smooth Transitions**: CSS transitions for opening/closing

### Responsive Design
- **Mobile First**: Designed for mobile screens
- **Flexible Layouts**: Components adapt to screen size
- **Touch Friendly**: Large tap targets for mobile
- **Scroll Management**: Proper scroll containers

### Visual Design
- **Icon System**:
  - 🎯 Target: One-time commitments
  - 🔄 Repeat: Recurring commitments
  - 📊 BarChart3: Analytics
  - 👤 User: Profile/People
  - 💬 MessageSquare: Chat origin
- **Color Scheme**: Blue primary, gray secondary
- **Typography**: Clean, readable text hierarchy
- **Spacing**: Consistent padding and margins

## Performance Optimizations
- **Code Splitting**: Next.js automatic code splitting
- **Image Optimization**: Next.js Image component
- **Lazy Loading**: Components loaded as needed
- **Memoization**: React.memo for expensive components

## Current Status
✅ Chat-first interface fully implemented
✅ All overlay pages functional with navigation
✅ Commitments system unified and working
✅ Analytics simplified per requirements
✅ People management operational
✅ Browser history navigation working
✅ Responsive design implemented