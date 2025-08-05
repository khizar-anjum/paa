'use client';

import { useRouter } from 'next/navigation';
import { X, Menu } from 'lucide-react';
import { useEffect, useCallback } from 'react';

interface PageOverlayProps {
  title: string;
  children: React.ReactNode;
  onClose?: () => void;
  onOpenSidebar?: () => void;
}

export function PageOverlay({ title, children, onClose, onOpenSidebar }: PageOverlayProps) {
  const router = useRouter();

  const handleClose = useCallback(() => {
    if (onClose) {
      onClose();
    } else {
      router.push('/dashboard');
    }
  }, [onClose, router]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [handleClose]);

  // Handle browser navigation state for overlay
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      // If browser navigates away from this overlay, close it
      if (window.location.pathname === '/dashboard') {
        handleClose();
      }
    };

    // Only add listener if we're not already at /dashboard
    if (window.location.pathname !== '/dashboard') {
      window.addEventListener('popstate', handlePopState);
      return () => window.removeEventListener('popstate', handlePopState);
    }
  }, [handleClose]);

  // Prevent body scroll when overlay is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  return (
    <div className="fixed inset-0 bg-white z-40 flex flex-col animate-in fade-in duration-300">
      {/* Header with hamburger menu and close button */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-white shadow-sm">
        <div className="flex items-center gap-4">
          {onOpenSidebar && (
            <button
              onClick={onOpenSidebar}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors"
              aria-label="Open navigation menu"
            >
              <Menu className="h-6 w-6 text-gray-600" />
            </button>
          )}
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        </div>
        <button
          onClick={handleClose}
          className="p-2 rounded-md hover:bg-gray-100 transition-colors"
          aria-label="Close and return to chat"
        >
          <X className="h-6 w-6 text-gray-600" />
        </button>
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {children}
        </div>
      </div>
    </div>
  );
}