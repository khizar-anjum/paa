'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Habit } from '@/lib/api/habits';

interface EditHabitModalProps {
  isOpen: boolean;
  habit: Habit | null;
  onClose: () => void;
  onUpdate: (habitId: number, data: any) => void;
}

export function EditHabitModal({ isOpen, habit, onClose, onUpdate }: EditHabitModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    frequency: 'daily',
    reminder_time: '',
  });
  const [selectedDay, setSelectedDay] = useState<string>('monday');

  useEffect(() => {
    if (habit) {
      // Parse frequency to check if it's weekly with day
      const isWeeklyWithDay = habit.frequency.startsWith('weekly-');
      const day = isWeeklyWithDay ? habit.frequency.split('-')[1] : 'monday';
      
      setFormData({
        name: habit.name,
        frequency: isWeeklyWithDay ? 'weekly' : habit.frequency,
        reminder_time: habit.reminder_time || '',
      });
      setSelectedDay(day);
    }
  }, [habit]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!habit) return;
    
    const habitData = {
      ...formData,
      frequency: formData.frequency === 'weekly' ? `weekly-${selectedDay}` : formData.frequency
    };
    onUpdate(habit.id, habitData);
    onClose();
  };

  if (!isOpen || !habit) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Edit Habit</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Habit Name
            </label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Morning Meditation"
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Frequency
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.frequency}
              onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>

          {formData.frequency === 'weekly' && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Day of Week
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                value={selectedDay}
                onChange={(e) => setSelectedDay(e.target.value)}
              >
                <option value="monday">Monday</option>
                <option value="tuesday">Tuesday</option>
                <option value="wednesday">Wednesday</option>
                <option value="thursday">Thursday</option>
                <option value="friday">Friday</option>
                <option value="saturday">Saturday</option>
                <option value="sunday">Sunday</option>
              </select>
            </div>
          )}

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reminder Time (Optional)
            </label>
            <input
              type="time"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              value={formData.reminder_time || ''}
              onChange={(e) => setFormData({ ...formData, reminder_time: e.target.value })}
            />
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Update Habit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}