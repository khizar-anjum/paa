'use client';

import { useAuth } from '@/lib/auth-context';
import { Target, MessageSquare, BarChart3, Smile, Users, User } from 'lucide-react';
import Link from 'next/link';
import { DailyCheckInModal } from '@/app/components/DailyCheckInModal';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { analyticsApi, OverviewAnalytics } from '@/lib/api/analytics';

export default function DashboardPage() {
  const { user } = useAuth();
  const [showCheckIn, setShowCheckIn] = useState(false);
  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);

  const getMoodEmoji = (mood: number | null) => {
    if (!mood) return '😐';
    const emojis = ['😢', '😞', '😐', '😊', '😄'];
    return emojis[mood - 1] || '😐';
  };

  useEffect(() => {
    // Load overview data and check for check-in
    const loadData = async () => {
      try {
        const today = new Date().toISOString().split('T')[0];
        const promptKey = `checkin-prompted-${today}`;
        
        // Load overview data
        const overviewData = await analyticsApi.getOverview();
        setOverview(overviewData);
        
        // Check if we've already prompted today
        const hasBeenPromptedToday = localStorage.getItem(promptKey);
        
        if (hasBeenPromptedToday) {
          return; // Don't prompt again today
        }
        
        // Show check-in if no mood set today AND we haven't prompted yet
        if (overviewData.current_mood === null) {
          // Mark that we've prompted today
          localStorage.setItem(promptKey, 'true');
          
          // Delay showing modal for better UX
          setTimeout(() => setShowCheckIn(true), 2000);
        }
      } catch (error) {
        console.error('Failed to load dashboard data');
      }
    };

    loadData();
  }, []);

  const quickActions = [
    {
      title: 'Your Profile',
      description: 'Manage your personal profile and information',
      icon: User,
      href: '/dashboard/profile',
      color: 'bg-indigo-500',
      isLink: true,
    },
    {
      title: 'Manage Habits',
      description: 'Track and update your daily habits',
      icon: Target,
      href: '/dashboard/habits',
      color: 'bg-blue-500',
      isLink: true,
    },
    {
      title: 'Manage People You Know',
      description: 'Manage your relationships and connections',
      icon: Users,
      href: '/dashboard/people',
      color: 'bg-green-500',
      isLink: true,
    },
    {
      title: 'View Analytics',
      description: 'See your progress and insights',
      icon: BarChart3,
      href: '/dashboard/analytics',
      color: 'bg-purple-500',
      isLink: true,
    },
    {
      title: 'Daily Check-in',
      description: "Share how you're feeling today",
      icon: Smile,
      color: 'bg-orange-500',
      isLink: false,
      onClick: () => setShowCheckIn(true),
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
        {quickActions.map((action) => {
          if (action.isLink) {
            return (
              <Link
                key={action.title}
                href={action.href!}
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
            );
          } else {
            return (
              <button
                key={action.title}
                onClick={action.onClick}
                className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow text-left"
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
              </button>
            );
          }
        })}
      </div>

      {/* Quick Stats */}
      <div className="mt-6 bg-white rounded-lg shadow-md p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Quick Stats</h2>
        <div className="grid grid-cols-3 gap-2">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">
              {overview ? `${overview.completed_today}/${overview.total_habits}` : '...'}
            </p>
            <p className="text-xs text-gray-600">Habits Today</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">
              {overview ? `${overview.longest_streak}` : '...'}
            </p>
            <p className="text-xs text-gray-600">Best Streak</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">
              {overview ? getMoodEmoji(overview.current_mood) : '...'}
            </p>
            <p className="text-xs text-gray-600">Current Mood</p>
          </div>
        </div>
      </div>


      <DailyCheckInModal
        isOpen={showCheckIn}
        onClose={() => setShowCheckIn(false)}
        onComplete={async () => {
          // Refresh overview data
          try {
            const overviewData = await analyticsApi.getOverview();
            setOverview(overviewData);
          } catch (error) {
            console.error('Failed to refresh overview data');
          }
        }}
      />
    </div>
  );
}