'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { Brain, Home, Target, MessageSquare, BarChart3, Users, User, LogOut, Loader2, CheckSquare } from 'lucide-react';
import Link from 'next/link';
import { useEffect } from 'react';
import { PersistentChatPanel } from '@/app/components/PersistentChatPanel';
import TimeDebugPanel from '@/app/components/TimeDebugPanel';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

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

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Your Profile', href: '/dashboard/profile', icon: User },
    { name: 'Habits', href: '/dashboard/habits', icon: Target },
    { name: 'Commitments', href: '/dashboard/commitments', icon: CheckSquare },
    { name: 'People', href: '/dashboard/people', icon: Users },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar - visible on desktop, hidden on mobile */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-lg">
        <div className="flex items-center justify-center h-16 px-4 bg-blue-600">
          <Brain className="h-8 w-8 text-white mr-2" />
          <span className="text-white font-bold text-lg">PAA</span>
        </div>
        
        <nav className="mt-8">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="flex items-center px-6 py-3 text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors"
            >
              <item.icon className="h-5 w-5 mr-3" />
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="absolute bottom-0 w-full p-4">
          {/* Time Debug Panel */}
          <div className="mb-4">
            <TimeDebugPanel />
          </div>
          
          <div className="bg-gray-100 rounded-lg p-3 mb-4">
            <p className="text-sm font-medium text-gray-700">{user.username}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
          </div>
          <button
            onClick={logout}
            className="flex items-center w-full px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="h-5 w-5 mr-2" />
            Logout
          </button>
        </div>
      </div>

      {/* Mobile header - only visible on small screens */}
      <div className="hidden bg-blue-600 h-16 flex items-center justify-between px-4">
        <div className="flex items-center">
          <Brain className="h-6 w-6 text-white mr-2" />
          <span className="text-white font-bold">PAA</span>
        </div>
        <button
          onClick={logout}
          className="text-white hover:text-gray-200"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>

      {/* Split content area */}
      <div className="ml-64 flex h-screen max-w-none overflow-hidden">
        {/* Main content - 45% of remaining space */}
        <div className="w-[45%] bg-gray-50 min-w-0">
          <main className="p-4 lg:p-6 h-full overflow-y-auto">
            {children}
          </main>
        </div>
        
        {/* Chat panel - 55% of remaining space */}
        <div className="w-[55%] bg-white border-l border-gray-200 min-w-0">
          <PersistentChatPanel />
        </div>
      </div>
    </div>
  );
}