'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Menu, X, User, Users, BarChart3, MessageSquare, LogOut, CheckSquare } from 'lucide-react';
import Link from 'next/link';
import TimeDebugPanel from './TimeDebugPanel';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navigation: NavigationItem[] = [
  { name: 'Chat', href: '/dashboard', icon: MessageSquare },
  { name: 'Your Profile', href: '/dashboard/profile', icon: User },
  { name: 'People', href: '/dashboard/people', icon: Users },
  { name: 'Commitments', href: '/dashboard/commitments', icon: CheckSquare },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
];

interface CollapsibleSidebarProps {
  currentPath?: string;
  user?: {
    username: string;
    email: string;
  };
  onLogout?: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export function CollapsibleSidebar({ currentPath, user, onLogout, isOpen, onClose }: CollapsibleSidebarProps) {
  const router = useRouter();
  

  // Close sidebar when route changes - use ref to track previous path
  const prevPathRef = useRef(currentPath);
  useEffect(() => {
    if (prevPathRef.current !== currentPath && isOpen) {
      prevPathRef.current = currentPath;
      onClose();
    } else {
      prevPathRef.current = currentPath;
    }
  }, [currentPath, isOpen, onClose]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Prevent body scroll when sidebar is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleNavigation = (href: string) => {
    router.push(href);
    onClose();
  };

  if (!isOpen) {
    return null; // Don't render anything when closed
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar */}
      <div
        className="fixed left-0 top-0 h-full w-80 bg-white shadow-xl z-50 flex flex-col animate-in slide-in-from-left duration-300"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Navigation</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors"
            aria-label="Close navigation menu"
          >
            <X className="h-6 w-6 text-gray-500" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-6">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const isActive = currentPath === item.href || 
                (item.href === '/dashboard' && currentPath === '/dashboard');
              
              return (
                <li key={item.name}>
                  <button
                    onClick={() => handleNavigation(item.href)}
                    className={`w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <item.icon className={`h-5 w-5 mr-3 ${
                      isActive ? 'text-blue-600' : 'text-gray-500'
                    }`} />
                    <span className="font-medium">{item.name}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom section with user info, debug panel, and logout */}
        <div className="border-t border-gray-200 p-6">
          {/* Time Debug Panel */}
          <div className="mb-4">
            <TimeDebugPanel />
          </div>
          
          {/* User Info */}
          {user && (
            <div className="bg-gray-100 rounded-lg p-3 mb-4">
              <p className="text-sm font-medium text-gray-700">{user.username}</p>
              <p className="text-xs text-gray-500">{user.email}</p>
            </div>
          )}
          
          {/* Logout Button */}
          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center w-full px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="h-5 w-5 mr-2" />
              Logout
            </button>
          )}
        </div>
      </div>
    </>
  );
}