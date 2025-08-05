'use client';

import { useState, useEffect } from 'react';
import { X, Save, Loader2, Calendar, AlertCircle, Clock } from 'lucide-react';
import { Commitment, commitmentAPI, commitmentUtils } from '@/lib/api/commitments';
import { toast } from 'sonner';

interface EditCommitmentModalProps {
  commitment: Commitment | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

export default function EditCommitmentModal({
  commitment,
  isOpen,
  onClose,
  onUpdate
}: EditCommitmentModalProps) {
  const [formData, setFormData] = useState({
    task_description: '',
    deadline: '',
    due_time: '',
    status: 'pending'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Initialize form when commitment changes
  useEffect(() => {
    if (commitment) {
      setFormData({
        task_description: commitment.task_description,
        deadline: commitment.deadline ? commitment.deadline.split('T')[0] : '',
        due_time: commitment.due_time || '',
        status: commitment.status
      });
      setErrors({});
    }
  }, [commitment]);

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setFormData({
        task_description: '',
        deadline: '',
        due_time: '',
        status: 'pending'
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
      
      if (selectedDate < today && formData.status === 'pending') {
        newErrors.deadline = 'Deadline cannot be in the past for pending commitments';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!commitment || !validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      await commitmentAPI.updateCommitment(commitment.id, {
        status: formData.status,
        deadline: formData.deadline || undefined,
        due_time: formData.due_time || undefined
      });
      
      // Note: The API doesn't currently support updating task_description
      // We'd need to add that to the backend endpoint
      
      toast.success('Commitment updated successfully!');
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Error updating commitment:', error);
      toast.error('Failed to update commitment');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!commitment) return;
    
    if (!confirm('Are you sure you want to delete this commitment? This action cannot be undone.')) {
      return;
    }

    setIsLoading(true);
    try {
      await commitmentAPI.deleteCommitment(commitment.id);
      toast.success('Commitment deleted');
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Error deleting commitment:', error);
      toast.error('Failed to delete commitment');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !commitment) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Edit Commitment
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
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Task Description */}
          <div>
            <label htmlFor="task_description" className="block text-sm font-medium text-gray-700 mb-1">
              Task Description
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
              placeholder="Describe what you need to do..."
            />
            {errors.task_description && (
              <p className="mt-1 text-sm text-red-600 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {errors.task_description}
              </p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Note: Task description editing is currently view-only. Create a new commitment for different text.
            </p>
          </div>

          {/* Deadline - Only for one-time commitments */}
          {!commitmentUtils.isRecurring(commitment) && (
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
          )}

          {/* Due Time - Only for recurring commitments */}
          {commitmentUtils.isRecurring(commitment) && (
            <div>
              <label htmlFor="due_time" className="block text-sm font-medium text-gray-700 mb-1">
                <Clock className="inline h-4 w-4 mr-1" />
                Due Time (Optional)
              </label>
              <input
                type="time"
                id="due_time"
                value={formData.due_time || ''}
                onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
                disabled={isLoading}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
              />
            </div>
          )}

          {/* Status */}
          <div>
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              id="status"
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:bg-gray-50"
            >
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="dismissed">Dismissed</option>
              <option value="missed">Missed</option>
            </select>
          </div>

          {/* Commitment Info */}
          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
            <div className="space-y-1">
              <div>Created: {new Date(commitment.created_at).toLocaleDateString()}</div>
              {commitment.reminder_count > 0 && (
                <div>Reminders sent: {commitment.reminder_count}</div>
              )}
              {commitment.last_reminded_at && (
                <div>Last reminded: {new Date(commitment.last_reminded_at).toLocaleDateString()}</div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  Update Commitment
                </>
              )}
            </button>
            
            <button
              type="button"
              onClick={handleDelete}
              disabled={isLoading}
              className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Delete
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