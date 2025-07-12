'use client';

import { Edit, Trash2, Flame } from 'lucide-react';
import { Habit } from '@/lib/api/habits';
import { toast } from 'sonner';

interface HabitCardProps {
  habit: Habit;
  onEdit: (habit: Habit) => void;
  onDelete: (habitId: number) => void;
}

export function HabitCard({ habit, onEdit, onDelete }: HabitCardProps) {
  const handleEdit = () => {
    onEdit(habit);
  };

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this habit?')) {
      onDelete(habit.id);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{habit.name}</h3>
          <p className="text-sm text-gray-500">
            {habit.frequency} • {habit.reminder_time || 'No reminder set'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleEdit}
            className="text-gray-400 hover:text-blue-500 transition-colors"
          >
            <Edit className="h-4 w-4" />
          </button>
          <button
            onClick={handleDelete}
            className="text-gray-400 hover:text-red-500 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Flame className="h-5 w-5 text-orange-500 mr-1" />
          <span className="text-sm font-medium text-gray-700">
            {habit.current_streak} day streak
          </span>
        </div>

        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          habit.completed_today
            ? 'bg-green-100 text-green-700'
            : 'bg-gray-100 text-gray-600'
        }`}>
          {habit.completed_today ? 'Completed Today' : 'Pending'}
        </div>
      </div>
    </div>
  );
}