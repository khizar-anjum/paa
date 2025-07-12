# Phase 3: Habit Management (1 hour)

## Overview
Implement the core habit tracking functionality with CRUD operations, completion tracking, and streak calculation.

## Step-by-Step Implementation

### 1. Backend Enhancements (15 mins)

Update `main.py` to add habit-related endpoints:

```python
# Add to imports
from datetime import date, datetime, timedelta
from sqlalchemy import func, and_

# Add habit completion endpoint
@app.post("/habits/{habit_id}/complete")
def complete_habit(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify habit belongs to user
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Check if already completed today
    today_start = datetime.combine(date.today(), datetime.min.time())
    existing_log = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id,
        models.HabitLog.completed_at >= today_start
    ).first()
    
    if existing_log:
        raise HTTPException(status_code=400, detail="Habit already completed today")
    
    # Create completion log
    log = models.HabitLog(habit_id=habit_id)
    db.add(log)
    db.commit()
    
    return {"message": "Habit completed!", "completed_at": log.completed_at}

# Add habit stats endpoint
@app.get("/habits/{habit_id}/stats")
def get_habit_stats(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify habit belongs to user
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Calculate stats
    total_completions = db.query(func.count(models.HabitLog.id)).filter(
        models.HabitLog.habit_id == habit_id
    ).scalar()
    
    # Calculate current streak
    logs = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id
    ).order_by(models.HabitLog.completed_at.desc()).all()
    
    current_streak = 0
    if logs:
        check_date = date.today()
        for log in logs:
            log_date = log.completed_at.date()
            if log_date == check_date:
                current_streak += 1
                check_date -= timedelta(days=1)
            elif log_date == check_date - timedelta(days=1):
                current_streak += 1
                check_date = log_date - timedelta(days=1)
            else:
                break
    
    # Check if completed today
    today_start = datetime.combine(date.today(), datetime.min.time())
    completed_today = db.query(models.HabitLog).filter(
        models.HabitLog.habit_id == habit_id,
        models.HabitLog.completed_at >= today_start
    ).first() is not None
    
    return {
        "habit_id": habit_id,
        "total_completions": total_completions,
        "current_streak": current_streak,
        "completed_today": completed_today
    }

# Update habits list to include stats
@app.get("/habits", response_model=List[schemas.Habit])
def get_habits(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habits = db.query(models.Habit).filter(
        models.Habit.user_id == current_user.id,
        models.Habit.is_active == 1
    ).all()
    
    # Add stats to each habit
    for habit in habits:
        # Check if completed today
        today_start = datetime.combine(date.today(), datetime.min.time())
        habit.completed_today = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id,
            models.HabitLog.completed_at >= today_start
        ).first() is not None
        
        # Get streak
        logs = db.query(models.HabitLog).filter(
            models.HabitLog.habit_id == habit.id
        ).order_by(models.HabitLog.completed_at.desc()).limit(30).all()
        
        current_streak = 0
        if logs:
            check_date = date.today()
            for log in logs:
                log_date = log.completed_at.date()
                if log_date == check_date or (current_streak == 0 and log_date == check_date - timedelta(days=1)):
                    current_streak += 1
                    check_date = log_date - timedelta(days=1)
                else:
                    break
        
        habit.current_streak = current_streak
    
    return habits

# Delete habit endpoint
@app.delete("/habits/{habit_id}")
def delete_habit(
    habit_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    habit = db.query(models.Habit).filter(
        models.Habit.id == habit_id,
        models.Habit.user_id == current_user.id
    ).first()
    
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    
    # Soft delete
    habit.is_active = 0
    db.commit()
    
    return {"message": "Habit deleted successfully"}
```

Update `schemas.py` to include stats:
```python
# Update Habit schema
class Habit(HabitBase):
    id: int
    user_id: int
    created_at: datetime
    is_active: int
    completed_today: bool = False
    current_streak: int = 0
    
    class Config:
        from_attributes = True
```

### 2. Frontend Habit Service (10 mins)

Create `lib/api/habits.ts`:
```typescript
import axios from 'axios';

export interface Habit {
  id: number;
  name: string;
  frequency: string;
  reminder_time: string | null;
  created_at: string;
  is_active: number;
  completed_today: boolean;
  current_streak: number;
}

export interface CreateHabitData {
  name: string;
  frequency: string;
  reminder_time?: string;
}

export const habitsApi = {
  getAll: async (): Promise<Habit[]> => {
    const response = await axios.get('/habits');
    return response.data;
  },

  create: async (data: CreateHabitData): Promise<Habit> => {
    const response = await axios.post('/habits', data);
    return response.data;
  },

  complete: async (habitId: number) => {
    const response = await axios.post(`/habits/${habitId}/complete`);
    return response.data;
  },

  delete: async (habitId: number) => {
    const response = await axios.delete(`/habits/${habitId}`);
    return response.data;
  },

  getStats: async (habitId: number) => {
    const response = await axios.get(`/habits/${habitId}/stats`);
    return response.data;
  },
};
```

### 3. Habit Components (20 mins)

Create `app/components/HabitCard.tsx`:
```tsx
'use client';

import { Check, Trash2, Flame } from 'lucide-react';
import { Habit } from '@/lib/api/habits';
import { toast } from 'sonner';

interface HabitCardProps {
  habit: Habit;
  onComplete: (habitId: number) => void;
  onDelete: (habitId: number) => void;
}

export function HabitCard({ habit, onComplete, onDelete }: HabitCardProps) {
  const handleComplete = () => {
    if (!habit.completed_today) {
      onComplete(habit.id);
    }
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
        <button
          onClick={handleDelete}
          className="text-gray-400 hover:text-red-500 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Flame className="h-5 w-5 text-orange-500 mr-1" />
          <span className="text-sm font-medium text-gray-700">
            {habit.current_streak} day streak
          </span>
        </div>

        <button
          onClick={handleComplete}
          disabled={habit.completed_today}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            habit.completed_today
              ? 'bg-green-100 text-green-700 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {habit.completed_today ? (
            <>
              <Check className="h-4 w-4 inline mr-1" />
              Completed
            </>
          ) : (
            'Mark Complete'
          )}
        </button>
      </div>
    </div>
  );
}
```

Create `app/components/CreateHabitModal.tsx`:
```tsx
'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { CreateHabitData } from '@/lib/api/habits';

interface CreateHabitModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (data: CreateHabitData) => void;
}

export function CreateHabitModal({ isOpen, onClose, onCreate }: CreateHabitModalProps) {
  const [formData, setFormData] = useState<CreateHabitData>({
    name: '',
    frequency: 'daily',
    reminder_time: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onCreate(formData);
    setFormData({ name: '', frequency: 'daily', reminder_time: '' });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Create New Habit</h2>
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
              Create Habit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

### 4. Habits Page (15 mins)

Create `app/dashboard/habits/page.tsx`:
```tsx
'use client';

import { useState, useEffect } from 'react';
import { Plus, Target } from 'lucide-react';
import { toast } from 'sonner';
import { habitsApi, Habit } from '@/lib/api/habits';
import { HabitCard } from '@/app/components/HabitCard';
import { CreateHabitModal } from '@/app/components/CreateHabitModal';

export default function HabitsPage() {
  const [habits, setHabits] = useState<Habit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

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

  const handleCompleteHabit = async (habitId: number) => {
    try {
      await habitsApi.complete(habitId);
      toast.success('Great job! Habit completed! 🎉');
      fetchHabits(); // Refresh to update streak
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to complete habit');
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
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Habits</h1>
          <p className="text-gray-600 mt-2">Track your daily progress and build consistency</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          New Habit
        </button>
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {habits.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onComplete={handleCompleteHabit}
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
    </div>
  );
}
```

## Testing Habit Management

1. Navigate to http://localhost:3000/dashboard/habits
2. Create a new habit
3. Mark it as complete
4. Check the streak counter
5. Try completing it again (should show error)
6. Delete a habit

## Troubleshooting

1. **Completion not working**: Check timezone handling in backend
2. **Streak calculation**: Verify date comparisons in SQL queries
3. **UI not updating**: Ensure fetchHabits() is called after actions

## Next Steps
- Phase 4: AI Chat integration
- Add habit reminders
- Implement habit categories