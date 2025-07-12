# Phase 5: Daily Check-in + Analytics (1 hour)

## Overview
Implement daily mood check-in functionality and basic analytics dashboard with habit and mood tracking visualizations.

## Step-by-Step Implementation

### 1. Backend Analytics Endpoints (15 mins)

Add analytics endpoints to `main.py`:

```python
# Add to imports
from sqlalchemy import func, cast, Date
from collections import defaultdict

# Analytics endpoints
@app.get("/analytics/habits")
def get_habits_analytics(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get habits with completion data
    habits = db.query(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == 1
    ).all()
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    analytics_data = []
    
    for habit in habits:
        # Get completion logs for this period
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id,
            cast(models.HabitLog.completed_at, Date) >= start_date,
            cast(models.HabitLog.completed_at, Date) <= end_date
        ).all()
        
        # Group by date
        completions_by_date = defaultdict(int)
        for log in logs:
            log_date = log.completed_at.date()
            completions_by_date[log_date] = 1
        
        # Create daily data
        daily_data = []
        current_date = start_date
        while current_date <= end_date:
            daily_data.append({
                "date": current_date.isoformat(),
                "completed": completions_by_date.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        # Calculate stats
        total_days = days
        completed_days = len([d for d in daily_data if d["completed"] > 0])
        completion_rate = (completed_days / total_days) * 100 if total_days > 0 else 0
        
        analytics_data.append({
            "habit_id": habit.id,
            "habit_name": habit.name,
            "completion_rate": round(completion_rate, 1),
            "total_completions": completed_days,
            "total_days": total_days,
            "daily_data": daily_data
        })
    
    return analytics_data

@app.get("/analytics/mood")
def get_mood_analytics(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get mood data for the period
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    checkins = db.query(models.DailyCheckIn).filter(
        models.DailyCheckIn.user_id == current_user.id,
        cast(models.DailyCheckIn.timestamp, Date) >= start_date,
        cast(models.DailyCheckIn.timestamp, Date) <= end_date
    ).order_by(models.DailyCheckIn.timestamp.asc()).all()
    
    # Group by date (latest checkin per day)
    mood_by_date = {}
    for checkin in checkins:
        checkin_date = checkin.timestamp.date()
        if checkin_date not in mood_by_date or checkin.timestamp > mood_by_date[checkin_date]['timestamp']:
            mood_by_date[checkin_date] = {
                'mood': checkin.mood,
                'notes': checkin.notes,
                'timestamp': checkin.timestamp
            }
    
    # Create daily data
    daily_moods = []
    current_date = start_date
    while current_date <= end_date:
        mood_data = mood_by_date.get(current_date)
        daily_moods.append({
            "date": current_date.isoformat(),
            "mood": mood_data['mood'] if mood_data else None,
            "notes": mood_data['notes'] if mood_data else None
        })
        current_date += timedelta(days=1)
    
    # Calculate average mood
    mood_values = [m['mood'] for m in daily_moods if m['mood'] is not None]
    average_mood = sum(mood_values) / len(mood_values) if mood_values else None
    
    return {
        "average_mood": round(average_mood, 1) if average_mood else None,
        "total_checkins": len(mood_values),
        "daily_moods": daily_moods
    }

@app.get("/analytics/overview")
def get_overview_analytics(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Habits overview
    total_habits = db.query(func.count(models.Habit.id)).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == 1
    ).scalar()
    
    # Completed today
    today_start = datetime.combine(date.today(), datetime.min.time())
    completed_today = db.query(
        func.count(func.distinct(models.HabitLog.habit_id))
    ).join(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.HabitLog.completed_at >= today_start
    ).scalar()
    
    # Current mood (today's latest checkin)
    today_checkin = db.query(models.DailyCheckIn).filter(
        models.DailyCheckIn.user_id == current_user.id,
        cast(models.DailyCheckIn.timestamp, Date) == date.today()
    ).order_by(models.DailyCheckIn.timestamp.desc()).first()
    
    # Longest streak (for all habits combined)
    # This is simplified - could be enhanced
    all_logs = db.query(models.HabitLog).join(models.Habit).filter(
        models.Habit.user_id == current_user.id
    ).order_by(models.HabitLog.completed_at.desc()).limit(365).all()
    
    # Calculate longest streak of any activity
    streak_days = set()
    for log in all_logs:
        streak_days.add(log.completed_at.date())
    
    longest_streak = 0
    current_streak = 0
    check_date = date.today()
    
    for i in range(365):  # Check last year
        if check_date in streak_days:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0
        check_date -= timedelta(days=1)
    
    return {
        "total_habits": total_habits,
        "completed_today": completed_today,
        "completion_rate": round((completed_today / total_habits) * 100, 1) if total_habits > 0 else 0,
        "current_mood": today_checkin.mood if today_checkin else None,
        "longest_streak": longest_streak,
        "total_conversations": db.query(func.count(models.Conversation.id)).filter(
            models.Conversation.user_id == current_user.id
        ).scalar()
    }
```

### 2. Frontend Analytics Service (10 mins)

Create `lib/api/analytics.ts`:
```typescript
import axios from 'axios';

export interface HabitAnalytics {
  habit_id: number;
  habit_name: string;
  completion_rate: number;
  total_completions: number;
  total_days: number;
  daily_data: Array<{
    date: string;
    completed: number;
  }>;
}

export interface MoodAnalytics {
  average_mood: number | null;
  total_checkins: number;
  daily_moods: Array<{
    date: string;
    mood: number | null;
    notes: string | null;
  }>;
}

export interface OverviewAnalytics {
  total_habits: number;
  completed_today: number;
  completion_rate: number;
  current_mood: number | null;
  longest_streak: number;
  total_conversations: number;
}

export const analyticsApi = {
  getHabitsAnalytics: async (days: number = 30): Promise<HabitAnalytics[]> => {
    const response = await axios.get(`/analytics/habits?days=${days}`);
    return response.data;
  },

  getMoodAnalytics: async (days: number = 30): Promise<MoodAnalytics> => {
    const response = await axios.get(`/analytics/mood?days=${days}`);
    return response.data;
  },

  getOverview: async (): Promise<OverviewAnalytics> => {
    const response = await axios.get('/analytics/overview');
    return response.data;
  },
};
```

### 3. Daily Check-in Modal (15 mins)

Create `app/components/DailyCheckInModal.tsx`:
```tsx
'use client';

import { useState, useEffect } from 'react';
import { X, Smile } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

interface DailyCheckInModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const moodEmojis = ['😢', '😞', '😐', '😊', '😄'];
const moodLabels = ['Very Sad', 'Sad', 'Neutral', 'Happy', 'Very Happy'];

export function DailyCheckInModal({ isOpen, onClose, onComplete }: DailyCheckInModalProps) {
  const [mood, setMood] = useState<number>(3);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Reset form when modal opens
      setMood(3);
      setNotes('');
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await axios.post('/checkin/daily', {
        mood,
        notes: notes.trim() || null
      });
      
      toast.success('Check-in completed! Thanks for sharing 😊');
      onComplete();
      onClose();
    } catch (error) {
      toast.error('Failed to save check-in');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <Smile className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold">Daily Check-in</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              How are you feeling today?
            </label>
            <div className="grid grid-cols-5 gap-2">
              {moodEmojis.map((emoji, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => setMood(index + 1)}
                  className={`p-3 rounded-lg text-center transition-colors ${
                    mood === index + 1
                      ? 'bg-blue-100 border-2 border-blue-500'
                      : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                  }`}
                >
                  <div className="text-2xl mb-1">{emoji}</div>
                  <div className="text-xs text-gray-600">{moodLabels[index]}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Any thoughts about your day? (Optional)
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              rows={3}
              placeholder="Share how your day went, what went well, or anything else..."
            />
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              disabled={isSubmitting}
            >
              Skip for now
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Complete Check-in'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### 4. Analytics Charts Component (15 mins)

Install recharts for charts:
```bash
npm install recharts
```

Create `app/components/AnalyticsChart.tsx`:
```tsx
'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface AnalyticsChartProps {
  data: any[];
  type: 'mood' | 'habits';
  title: string;
}

export function AnalyticsChart({ data, type, title }: AnalyticsChartProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (type === 'mood') {
    // Filter out null moods for the chart
    const chartData = data
      .filter(d => d.mood !== null)
      .map(d => ({
        ...d,
        date: formatDate(d.date),
        mood: d.mood
      }));

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[1, 5]} />
            <Tooltip 
              formatter={(value: any) => [
                `Mood: ${value}`,
                ''
              ]}
            />
            <Line 
              type="monotone" 
              dataKey="mood" 
              stroke="#3B82F6" 
              strokeWidth={2}
              dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  } else {
    // Habits chart - show completion rate
    const chartData = data.map(habit => ({
      name: habit.habit_name.length > 15 
        ? habit.habit_name.substring(0, 15) + '...' 
        : habit.habit_name,
      completion_rate: habit.completion_rate
    }));

    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <Tooltip 
              formatter={(value: any) => [
                `${value}%`,
                'Completion Rate'
              ]}
            />
            <Bar dataKey="completion_rate" fill="#10B981" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }
}
```

### 5. Analytics Page (15 mins)

Create `app/dashboard/analytics/page.tsx`:
```tsx
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
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-2">Track your progress and insights</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Overview Cards */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <BarChart3 className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Habits Today</p>
                <p className="text-2xl font-bold text-gray-900">
                  {overview.completed_today}/{overview.total_habits}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <TrendingUp className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completion Rate</p>
                <p className="text-2xl font-bold text-gray-900">
                  {overview.completion_rate}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Longest Streak</p>
                <p className="text-2xl font-bold text-gray-900">
                  {overview.longest_streak} days
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <span className="text-3xl">{getMoodEmoji(overview.current_mood)}</span>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Current Mood</p>
                <p className="text-2xl font-bold text-gray-900">
                  {overview.current_mood ? `${overview.current_mood}/5` : 'Not set'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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

      {/* Habits Details */}
      {habitsData.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Habit Details</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full table-auto">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Habit</th>
                  <th className="text-left py-2">Completion Rate</th>
                  <th className="text-left py-2">Days Completed</th>
                  <th className="text-left py-2">Total Days</th>
                </tr>
              </thead>
              <tbody>
                {habitsData.map((habit) => (
                  <tr key={habit.habit_id} className="border-b">
                    <td className="py-2 font-medium">{habit.habit_name}</td>
                    <td className="py-2">{habit.completion_rate}%</td>
                    <td className="py-2">{habit.total_completions}</td>
                    <td className="py-2">{habit.total_days}</td>
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
```

### 6. Auto Check-in Prompt (5 mins)

Update dashboard home page to show check-in prompt, modify `app/dashboard/page.tsx`:

```tsx
// Add to imports
import { DailyCheckInModal } from '@/app/components/DailyCheckInModal';
import { useEffect, useState } from 'react';
import axios from 'axios';

// Add state and useEffect in component
const [showCheckIn, setShowCheckIn] = useState(false);

useEffect(() => {
  // Check if user has done check-in today
  const checkTodayCheckIn = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get('/analytics/overview');
      
      // Show check-in if no mood set today
      if (response.data.current_mood === null) {
        // Delay showing modal for better UX
        setTimeout(() => setShowCheckIn(true), 2000);
      }
    } catch (error) {
      console.error('Failed to check today\'s check-in');
    }
  };

  checkTodayCheckIn();
}, []);

// Add modal before closing div
<DailyCheckInModal
  isOpen={showCheckIn}
  onClose={() => setShowCheckIn(false)}
  onComplete={() => {
    // Refresh page data
    window.location.reload();
  }}
/>
```

## Testing Daily Check-in and Analytics

1. Complete some habits
2. Visit http://localhost:3000/dashboard/analytics
3. Check overview stats
4. Do a daily check-in (should auto-prompt)
5. View mood and habit charts
6. Try different time ranges

## Troubleshooting

1. **Charts not showing**: Install recharts and check data format
2. **Check-in not prompting**: Verify analytics/overview endpoint
3. **Date issues**: Check timezone handling in backend

## Next Steps
- Add habit reminders
- Implement export functionality
- Enhance visualizations with more chart types