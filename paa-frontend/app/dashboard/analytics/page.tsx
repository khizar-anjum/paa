'use client';

import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Calendar, Brain, Target, Repeat, CheckSquare } from 'lucide-react';
import { analyticsApi, CommitmentAnalytics, MoodAnalytics, OverviewAnalytics } from '@/lib/api/analytics';
import { AnalyticsChart } from '@/app/components/AnalyticsChart';
import { toast } from 'sonner';

export default function AnalyticsPage() {
  const [commitmentsData, setCommitmentsData] = useState<CommitmentAnalytics[]>([]);
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
      const [commitments, mood, overviewData] = await Promise.all([
        analyticsApi.getCommitmentsAnalytics(timeRange),
        analyticsApi.getMoodAnalytics(timeRange),
        analyticsApi.getOverview()
      ]);
      
      setCommitmentsData(commitments);
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

      {/* Overview Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <CheckSquare className="h-6 w-6 text-blue-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Total Commitments</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.total_commitments || overview.total_habits || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <Repeat className="h-6 w-6 text-purple-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Recurring</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.recurring_commitments || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <Target className="h-6 w-6 text-green-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">One-time</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.one_time_commitments || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <TrendingUp className="h-6 w-6 text-orange-600" />
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
              <BarChart3 className="h-6 w-6 text-indigo-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Completed Today</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.completed_today}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <Calendar className="h-6 w-6 text-red-600" />
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

          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="flex items-center">
              <Brain className="h-6 w-6 text-teal-600" />
              <div className="ml-3">
                <p className="text-xs font-medium text-gray-500">Conversations</p>
                <p className="text-xl font-bold text-gray-900">
                  {overview.total_conversations}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts - Stacked vertically for narrow layout */}
      <div className="space-y-6">
        {commitmentsData.length > 0 && (
          <AnalyticsChart
            data={commitmentsData}
            type="commitments"
            title="Commitment Completion Rates"
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

      {/* Commitments Details Table */}
      {commitmentsData.length > 0 && (
        <div className="mt-6 bg-white rounded-lg shadow-md p-4">
          <h3 className="text-base font-semibold mb-3">Commitment Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-xs">Commitment</th>
                  <th className="text-left py-2 text-xs">Type</th>
                  <th className="text-left py-2 text-xs">Rate</th>
                  <th className="text-left py-2 text-xs">Completions</th>
                </tr>
              </thead>
              <tbody>
                {commitmentsData.map((commitment) => (
                  <tr key={commitment.commitment_id} className="border-b">
                    <td className="py-2 font-medium text-xs max-w-32 truncate">
                      {commitment.commitment_name}
                    </td>
                    <td className="py-2 text-xs">
                      <div className="flex items-center gap-1">
                        {commitment.is_recurring ? (
                          <>
                            <Repeat className="h-3 w-3 text-purple-500" />
                            <span className="text-purple-600 font-medium">
                              {commitment.recurrence_pattern}
                            </span>
                          </>
                        ) : (
                          <>
                            <Target className="h-3 w-3 text-green-500" />
                            <span className="text-green-600 font-medium">One-time</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="py-2 text-xs">{commitment.completion_rate}%</td>
                    <td className="py-2 text-xs">
                      {commitment.total_completions}
                      {commitment.is_recurring && `/${commitment.total_days}`}
                    </td>
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