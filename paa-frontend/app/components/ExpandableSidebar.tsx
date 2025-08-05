'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Menu, X, User, Users, BarChart3, MessageSquare, LogOut, Target } from 'lucide-react';
import TimeDebugPanel from './TimeDebugPanel';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navigation: NavigationItem[] = [
  { name: 'Chat', href: '/dashboard', icon: MessageSquare },
  { name: 'Profile', href: '/dashboard/profile', icon: User },
  { name: 'People', href: '/dashboard/people', icon: Users },
  { name: 'Commitments', href: '/dashboard/commitments', icon: Target },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
];

interface ExpandableSidebarProps {
  currentPath?: string;
  user?: {
    username: string;
    email: string;
  };
  onLogout?: () => void;
}

export function ExpandableSidebar({ currentPath, user, onLogout }: ExpandableSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  
  // Close sidebar when route changes
  const prevPathRef = useRef(currentPath);
  useEffect(() => {
    if (prevPathRef.current !== currentPath && isExpanded) {
      prevPathRef.current = currentPath;
      setIsExpanded(false);
    } else {
      prevPathRef.current = currentPath;
    }
  }, [currentPath, isExpanded]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isExpanded) {
        setIsExpanded(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isExpanded]);

  const handleNavigation = (href: string) => {
    router.push(href);
    setIsExpanded(false);
  };

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const isActive = (href: string) => {
    return currentPath === href || (href === '/dashboard' && currentPath === '/dashboard');
  };

  return (
    <>
      {/* Backdrop when expanded */}
      {isExpanded && (
        <div
          className="hidden lg:block fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
          onClick={() => setIsExpanded(false)}
          aria-hidden="true"
        />
      )}

      {/* Expandable Sidebar - Only on large screens */}
      <div 
        className={`
          hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:z-[60] lg:bg-white lg:border-r lg:border-gray-200
          transition-all duration-300 ease-in-out
          ${isExpanded ? 'lg:w-80' : 'lg:w-16'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 h-16">
          {/* Hamburger Menu Button */}
          <button
            onClick={toggleExpanded}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label={isExpanded ? "Collapse menu" : "Expand menu"}
          >
            {isExpanded ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          
          {/* Title - only visible when expanded */}
          {isExpanded && (
            <h2 className="text-lg font-semibold text-gray-900 ml-3">Navigation</h2>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const active = isActive(item.href);
              
              return (
                <li key={item.name}>
                  <button
                    onClick={() => handleNavigation(item.href)}
                    className={`
                      w-full flex items-center rounded-lg transition-colors
                      ${isExpanded ? 'px-3 py-2' : 'p-2 justify-center'}
                      ${active
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
                      }
                    `}
                  >
                    <item.icon className={`h-5 w-5 ${
                      active ? 'text-blue-600' : 'text-gray-500'
                    } ${isExpanded ? 'mr-3' : ''}`} />
                    {isExpanded && (
                      <span className="font-medium">{item.name}</span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom section - only when expanded */}
        {isExpanded && (
          <div className="border-t border-gray-200 p-4">
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
        )}
      </div>
    </>
  );
}