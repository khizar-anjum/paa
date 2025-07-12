'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Calendar, Brain } from 'lucide-react';
import { analyticsApi, HabitAnalytics, MoodAnalytics, OverviewAnalytics } from '@/lib/api/analytics';
import { AnalyticsChart } from '@/app/components/AnalyticsChart';
import { toast } from 'sonner';

export default function AnalyticsPage() {
  const [habitsData, setHabitsData] = useState<HabitAnalytics[]>([]);
  const [moodData, setMoodData] = useState<MoodAnalytics | null>(null);
  const [overview, setOverview] = useState<OverviewAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(30);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    setIsLoading(true);
    try {
      const [habits, mood, overviewData] = await Promise.all([
        analyticsApi.getHabitsAnalytics(timeRange),
        analyticsApi.getMoodAnalytics(timeRange),
        analyticsApi.getOverview()
      ]);
      
      setHabitsData(habits);
      setMoodData(mood);
      setOverview(overviewData);
    } catch (error) {
      toast.error('Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const getMoodEmoji = (mood: number | null) => {
    if (!mood) return '😐';
    const emojis = ['😢', '😞', '😐', '😊', '😄'];
    return emojis[mood - 1] || '😐';
  };

  return (
    <div>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 text-sm mt-1">Track your progress and insights</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Overview Cards - Single column on narrow screen */}
      {overview && (
        <div className="grid grid-cols-1 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <BarChart3 className="h-6 w-6 text-blue-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Habits Today</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.completed_today}/{overview.total_habits}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <TrendingUp className="h-6 w-6 text-green-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Completion Rate</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.completion_rate}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <Calendar className="h-6 w-6 text-orange-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Longest Streak</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.longest_streak} days
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <span className="text-2xl">{getMoodEmoji(overview.current_mood)}</span>
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Current Mood</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.current_mood ? `${overview.current_mood}/5` : 'Not set'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts - Stacked vertically for narrow layout */}
      <div className="space-y-6">
        {habitsData.length > 0 && (
          <AnalyticsChart
            data={habitsData}
            type="habits"
            title="Habit Completion Rates"
          />
        )}

        {moodData && moodData.daily_moods && (
          <AnalyticsChart
            data={moodData.daily_moods}
            type="mood"
            title="Mood Trend"
          />
        )}
      </div>

      {/* Habits Details Table */}
      {habitsData.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow-md p-4">
          <h3 className="text-base font-semibold mb-3">Habit Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-xs">Habit</th>
                  <th className="text-left py-2 text-xs">Rate</th>
                  <th className="text-left py-2 text-xs">Days</th>
                </tr>
              </thead>
              <tbody>
                {habitsData.map((habit) => (
                  <tr key={habit.habit_id} className="border-b">
                    <td className="py-2 font-medium text-xs">{habit.habit_name}</td>
                    <td className="py-2 text-xs">{habit.completion_rate}%</td>
                    <td className="py-2 text-xs">{habit.total_completions}/{habit.total_days}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}