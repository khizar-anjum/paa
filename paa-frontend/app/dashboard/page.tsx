'use client';

import { useAuth } from '@/lib/auth-context';
import { Target, MessageSquare, BarChart3, Smile } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useAuth();

  const quickActions = [
    {
      title: 'Manage Habits',
      description: 'Track and update your daily habits',
      icon: Target,
      href: '/dashboard/habits',
      color: 'bg-blue-500',
    },
    {
      title: 'View Analytics',
      description: 'See your progress and insights',
      icon: BarChart3,
      href: '/dashboard/analytics',
      color: 'bg-purple-500',
    },
    {
      title: 'Daily Check-in',
      description: 'Share how you&apos;re feeling today',
      icon: Smile,
      href: '/dashboard/checkin',
      color: 'bg-orange-500',
    },
  ];

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-2">
        Welcome back, {user?.username}!
      </h1>
      <p className="text-gray-600 mb-8">
        Here&apos;s your personal dashboard. What would you like to do today?
      </p>

      <div className="grid grid-cols-1 gap-4">
        {quickActions.map((action) => (
          <Link
            key={action.title}
            href={action.href}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow"
          >
            <div className="flex items-center mb-2">
              <div className={`${action.color} p-2 rounded-lg`}>
                <action.icon className="h-5 w-5 text-white" />
              </div>
              <h3 className="ml-3 text-base font-semibold text-gray-900">
                {action.title}
              </h3>
            </div>
            <p className="text-sm text-gray-600">{action.description}</p>
          </Link>
        ))}
      </div>

      {/* Quick Stats */}
      <div className="mt-6 bg-white rounded-lg shadow-md p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Quick Stats</h2>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">0</p>
            <p className="text-xs text-gray-600">Active Habits</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">0</p>
            <p className="text-xs text-gray-600">Day Streak</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">😊</p>
            <p className="text-xs text-gray-600">Current Mood</p>
          </div>
        </div>
      </div>
    </div>
  );
}