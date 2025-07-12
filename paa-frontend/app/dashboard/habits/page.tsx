'use client';

import { useState, useEffect } from 'react';
import { Plus, Target } from 'lucide-react';
import { toast } from 'sonner';
import { habitsApi, Habit } from '@/lib/api/habits';
import { HabitCard } from '@/app/components/HabitCard';
import { CreateHabitModal } from '@/app/components/CreateHabitModal';
import { EditHabitModal } from '@/app/components/EditHabitModal';

export default function HabitsPage() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);

  useEffect(() => {
    fetchHabits();
  }, []);

  const fetchHabits = async () => {
    try {
      const data = await habitsApi.getAll();
      setHabits(data);
    } catch (error) {
      toast.error('Failed to load habits');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateHabit = async (data: any) => {
    try {
      const newHabit = await habitsApi.create(data);
      setHabits([...habits, newHabit]);
      toast.success('Habit created successfully!');
    } catch (error) {
      toast.error('Failed to create habit');
    }
  };

  const handleEditHabit = (habit: Habit) => {
    setEditingHabit(habit);
  };

  const handleUpdateHabit = async (habitId: number, data: any) => {
    try {
      const updatedHabit = await habitsApi.update(habitId, data);
      setHabits(habits.map(h => h.id === habitId ? updatedHabit : h));
      setEditingHabit(null);
      toast.success('Habit updated successfully!');
    } catch (error) {
      toast.error('Failed to update habit');
    }
  };

  const handleDeleteHabit = async (habitId: number) => {
    try {
      await habitsApi.delete(habitId);
      setHabits(habits.filter(h => h.id !== habitId));
      toast.success('Habit deleted');
    } catch (error) {
      toast.error('Failed to delete habit');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <div className="flex justify-between items-start mb-4">
          <h1 className="text-2xl font-bold text-gray-900">Your Habits</h1>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
          >
            <Plus className="h-4 w-4 mr-1" />
            New Habit
          </button>
        </div>
        <p className="text-gray-600 text-sm">Here's what I know about your habits so far based on our chats. Feel free to edit any habit if you'd like something changed.</p>
      </div>

      {habits.length === 0 ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Target className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No habits yet</h3>
          <p className="text-gray-600 mb-6">Start building better habits today!</p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Create Your First Habit
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {habits.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onEdit={handleEditHabit}
              onDelete={handleDeleteHabit}
            />
          ))}
        </div>
      )}

      <CreateHabitModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreateHabit}
      />

      <EditHabitModal
        isOpen={!!editingHabit}
        habit={editingHabit}
        onClose={() => setEditingHabit(null)}
        onUpdate={handleUpdateHabit}
      />
    </div>
  );
}