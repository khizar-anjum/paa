'use client';

import { useState, useEffect } from 'react';
import { X, Save, Loader2, Calendar, AlertCircle, Plus } from 'lucide-react';
import { toast } from 'sonner';

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
    deadline: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset form when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        task_description: '',
        deadline: ''
      });
      setErrors({});
    }
  }, [isOpen]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.task_description.trim()) {
      newErrors.task_description = 'Task description is required';
    }

    if (formData.deadline) {
      const selectedDate = new Date(formData.deadline);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (selectedDate < today) {
        newErrors.deadline = 'Deadline cannot be in the past';
      }
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
      // Note: We need to create a commitment through the chat system or add a direct API endpoint
      // For now, we'll show a helpful message to use the chat
      toast.info('Create commitments by telling your AI assistant what you want to do!', {
        description: 'Try saying something like "I need to do laundry by tomorrow" in the chat.'
      });
      
      onClose();
    } catch (error) {
      console.error('Error creating commitment:', error);
      toast.error('Failed to create commitment');
    } finally {
      setIsLoading(false);
    }
  };

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

        {/* Info message */}
        <div className="p-6 pb-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <div className="text-blue-600 mt-0.5">
                <AlertCircle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-medium text-blue-900 mb-1">
                  Pro Tip: Use the AI Chat
                </h3>
                <p className="text-sm text-blue-700">
                  The easiest way to create commitments is by talking to your AI assistant in the chat panel. 
                  Just tell it what you want to do and when, like:
                </p>
                <div className="mt-2 text-sm text-blue-800 font-mono bg-blue-100 rounded px-2 py-1">
                  "I need to call mom by Friday"
                </div>
              </div>
            </div>
          </div>
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
              placeholder="e.g., Call mom, Do laundry, Submit report..."
            />
            {errors.task_description && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.task_description}
              </p>
            )}
          </div>

          {/* Deadline */}
          <div>
            <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-1">
              Deadline (Optional)
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <input
                type="date"
                id="deadline"
                value={formData.deadline}
                onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                disabled={isLoading}
                className={`w-full pl-10 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50 ${
                  errors.deadline ? 'border-red-300' : 'border-gray-300'
                }`}
              />
            </div>
            {errors.deadline && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.deadline}
              </p>
            )}
          </div>

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
                  Use Chat Instead
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