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