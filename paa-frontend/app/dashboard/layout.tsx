'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter, usePathname } from 'next/navigation';
import { LogOut, Loader2 } from 'lucide-react';
import { useEffect, useState, useCallback, createContext, useContext } from 'react';
import { PersistentChatPanel } from '@/app/components/PersistentChatPanel';
import { CollapsibleSidebar } from '@/app/components/CollapsibleSidebar';

// Create context for sidebar functionality
const SidebarContext = createContext<{
  openSidebar: () => void;
} | null>(null);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Memoize the close function to prevent useEffect re-runs
  const closeSidebar = useCallback(() => {
    setIsSidebarOpen(false);
  }, []);

  const openSidebar = useCallback(() => {
    setIsSidebarOpen(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  // Handle browser navigation for overlay pages
  useEffect(() => {
    const handlePopstate = (event: PopStateEvent) => {
      // If we're navigating away from an overlay page to /dashboard
      // ensure we close any open sidebar
      if (window.location.pathname === '/dashboard') {
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('popstate', handlePopstate);
    return () => window.removeEventListener('popstate', handlePopstate);
  }, []);

  // Redirect /dashboard to show chat interface
  useEffect(() => {
    if (pathname === '/dashboard') {
      // This is handled by showing the chat interface directly
      setIsSidebarOpen(false); // Ensure sidebar is closed when returning to chat
    }
  }, [pathname]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Check if we should show chat interface (dashboard root or non-overlay pages)
  const isShowingChat = pathname === '/dashboard';
  const isOverlayPage = ['/dashboard/profile', '/dashboard/people', '/dashboard/commitments', '/dashboard/analytics'].includes(pathname);
  

  return (
    <div className="min-h-screen bg-white">
      {/* Collapsible Sidebar */}
      <CollapsibleSidebar 
        currentPath={pathname}
        user={user}
        onLogout={logout}
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
      />

      {/* Main content area */}
      {isShowingChat ? (
        // Full-width chat interface for dashboard root
        <div className="h-screen">
          <PersistentChatPanel onOpenSidebar={openSidebar} />
        </div>
      ) : isOverlayPage ? (
        // Full-screen overlay for profile, people, analytics pages - PageOverlay component handles the overlay structure
        <SidebarContext.Provider value={{ openSidebar }}>
          <div className="h-screen">
            {children}
          </div>
        </SidebarContext.Provider>
      ) : (
        // Fallback for other pages - maintain some layout
        <div className="min-h-screen pt-16">
          <main className="container mx-auto px-4 py-8">
            {children}
          </main>
        </div>
      )}
    </div>
  );
}