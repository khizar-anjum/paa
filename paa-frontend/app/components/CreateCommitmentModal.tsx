'use client';

import { useState, useEffect } from 'react';
import { X, Save, Loader2, Calendar, AlertCircle, Plus, Repeat, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { commitmentAPI, CommitmentUpdate } from '@/lib/api/commitments';

interface CreateCommitmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

export default function CreateCommitmentModal({
  isOpen,
  onClose,
  onUpdate
}: CreateCommitmentModalProps) {
  const [formData, setFormData] = useState({
    task_description: '',
    deadline: '',
    recurrence_pattern: 'none' as 'none' | 'daily' | 'weekly' | 'monthly' | 'custom',
    due_time: '',
    recurrence_days: [] as string[],
    recurrence_interval: 1
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        task_description: '',
        deadline: '',
        recurrence_pattern: 'none',
        due_time: '',
        recurrence_days: [],
        recurrence_interval: 1
      });
      setErrors({});
    }
  }, [isOpen]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.task_description.trim()) {
      newErrors.task_description = 'Task description is required';
    }

    // For one-time commitments
    if (formData.recurrence_pattern === 'none') {
      if (formData.deadline) {
        const selectedDate = new Date(formData.deadline);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        if (selectedDate < today) {
          newErrors.deadline = 'Deadline cannot be in the past';
        }
      }
    }

    // For weekly recurring commitments
    if (formData.recurrence_pattern === 'weekly' && formData.recurrence_days.length === 0) {
      newErrors.recurrence_days = 'Please select at least one day for weekly recurrence';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      // Prepare commitment data
      const commitmentData: CommitmentUpdate = {
        task_description: formData.task_description.trim(),
        recurrence_pattern: formData.recurrence_pattern,
        recurrence_interval: formData.recurrence_interval,
        due_time: formData.due_time || undefined
      };

      // Set deadline for one-time commitments
      if (formData.recurrence_pattern === 'none' && formData.deadline) {
        commitmentData.deadline = formData.deadline;
      }

      // Set recurrence days for weekly pattern
      if (formData.recurrence_pattern === 'weekly' && formData.recurrence_days.length > 0) {
        commitmentData.recurrence_days = formData.recurrence_days.join(',');
      }

      // Create commitment
      const response = await fetch('/api/commitments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(commitmentData)
      });

      if (!response.ok) {
        throw new Error('Failed to create commitment');
      }

      const isRecurring = formData.recurrence_pattern !== 'none';
      toast.success(
        `${isRecurring ? 'Recurring commitment' : 'Commitment'} created successfully! 🎉`,
        {
          description: isRecurring 
            ? `Your ${formData.recurrence_pattern} commitment is now active.`
            : 'You can track its progress in the commitments list.'
        }
      );
      
      onUpdate(); // Refresh the commitments list
      onClose();
    } catch (error) {
      console.error('Error creating commitment:', error);
      toast.error('Failed to create commitment');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper functions
  const handleDayToggle = (day: string) => {
    setFormData(prev => ({
      ...prev,
      recurrence_days: prev.recurrence_days.includes(day)
        ? prev.recurrence_days.filter(d => d !== day)
        : [...prev.recurrence_days, day]
    }));
  };

  const weekDays = [
    { key: 'mon', label: 'Mon' },
    { key: 'tue', label: 'Tue' },
    { key: 'wed', label: 'Wed' },
    { key: 'thu', label: 'Thu' },
    { key: 'fri', label: 'Fri' },
    { key: 'sat', label: 'Sat' },
    { key: 'sun', label: 'Sun' }
  ];

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Plus className="h-5 w-5 text-blue-600" />
            Create New Commitment
          </h2>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>


        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-4">
          {/* Task Description */}
          <div>
            <label htmlFor="task_description" className="block text-sm font-medium text-gray-700 mb-1">
              What do you want to commit to?
            </label>
            <textarea
              id="task_description"
              value={formData.task_description}
              onChange={(e) => setFormData({ ...formData, task_description: e.target.value })}
              disabled={isLoading}
              className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50 ${
                errors.task_description ? 'border-red-300' : 'border-gray-300'
              }`}
              rows={3}
              placeholder="e.g., Exercise for 30 minutes, Call mom, Submit report..."
            />
            {errors.task_description && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.task_description}
              </p>
            )}
          </div>

          {/* Recurrence Pattern */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <Repeat className="inline h-4 w-4 mr-1" />
              Recurrence
            </label>
            <select
              value={formData.recurrence_pattern}
              onChange={(e) => setFormData({ ...formData, recurrence_pattern: e.target.value as any })}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
            >
              <option value="none">One-time commitment</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          {/* Weekly Days Selection */}
          {formData.recurrence_pattern === 'weekly' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Days
              </label>
              <div className="flex flex-wrap gap-2">
                {weekDays.map((day) => (
                  <button
                    key={day.key}
                    type="button"
                    onClick={() => handleDayToggle(day.key)}
                    disabled={isLoading}
                    className={`px-3 py-1 text-sm rounded-full border transition-colors disabled:opacity-50 ${
                      formData.recurrence_days.includes(day.key)
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {day.label}
                  </button>
                ))}
              </div>
              {errors.recurrence_days && (
                <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-4 w-4" />
                  {errors.recurrence_days}
                </p>
              )}
            </div>
          )}

          {/* Due Time for recurring commitments */}
          {formData.recurrence_pattern !== 'none' && (
            <div>
              <label htmlFor="due_time" className="block text-sm font-medium text-gray-700 mb-1">
                <Clock className="inline h-4 w-4 mr-1" />
                Due Time (Optional)
              </label>
              <input
                type="time"
                id="due_time"
                value={formData.due_time}
                onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
                disabled={isLoading}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
              />
            </div>
          )}

          {/* Deadline for one-time commitments */}
          {formData.recurrence_pattern === 'none' && (
            <div>
              <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="inline h-4 w-4 mr-1" />
                Deadline (Optional)
              </label>
              <input
                type="date"
                id="deadline"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                disabled={isLoading}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50 ${
                  errors.deadline ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.deadline && (
                <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                  <AlertCircle className="h-4 w-4" />
                  {errors.deadline}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>
            
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Create Commitment
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Click outside to close */}
      <div
        className="absolute inset-0 -z-10"
        onClick={onClose}
      />
    </div>
  );
}