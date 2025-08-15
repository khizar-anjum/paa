'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter, usePathname } from 'next/navigation';
import { LogOut, Loader2 } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { PersistentChatPanel } from '@/app/components/PersistentChatPanel';
import { CollapsibleSidebar } from '@/app/components/CollapsibleSidebar';
import { ExpandableSidebar } from '@/app/components/ExpandableSidebar';
import { SidebarProvider } from '@/app/contexts/sidebar-context';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Debug auth state
  console.log('Dashboard layout render - Auth state:', { 
    user: user ? `${user.username} (${user.email})` : null, 
    isLoading, 
    pathname,
    hasToken: !!localStorage.getItem('token')
  });

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
    console.log('Dashboard layout: Still loading, showing spinner');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  if (!user) {
    console.log('Dashboard layout: No user found, returning null');
    return null;
  }

  console.log('Dashboard layout: User found, rendering dashboard. User:', user);
  console.log('Dashboard layout: isShowingChat:', isShowingChat, 'pathname:', pathname);

  // Check if we should show chat interface (dashboard root or non-overlay pages)
  const isShowingChat = pathname === '/dashboard';
  const isOverlayPage = ['/dashboard/profile', '/dashboard/people', '/dashboard/commitments', '/dashboard/analytics'].includes(pathname);
  

  return (
    <SidebarProvider value={{ openSidebar }}>
      <div className="min-h-screen bg-white">
        {/* Expandable Sidebar - Always visible on large screens */}
        <ExpandableSidebar 
          currentPath={pathname}
          user={user}
          onLogout={logout}
        />

        {/* Collapsible Sidebar - Only on small screens */}
        <CollapsibleSidebar 
          currentPath={pathname}
          user={user}
          onLogout={logout}
          isOpen={isSidebarOpen}
          onClose={closeSidebar}
        />

        {/* Main content area - with left margin on large screens to account for ExpandableSidebar */}
        <div className="lg:ml-16">
          {isShowingChat ? (
            // Full-width chat interface for dashboard root
            <div className="h-screen">
              <PersistentChatPanel onOpenSidebar={openSidebar} />
            </div>
          ) : isOverlayPage ? (
            // Full-screen overlay for profile, people, analytics pages - PageOverlay component handles the overlay structure
            <div className="h-screen">
              {children}
            </div>
          ) : (
            // Fallback for other pages - maintain some layout
            <div className="min-h-screen pt-16">
              <main className="container mx-auto px-4 py-8">
                {children}
              </main>
            </div>
          )}
        </div>
      </div>
    </SidebarProvider>
  );
}