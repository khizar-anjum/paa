'use client';

import { useState } from 'react';
import { Edit, Trash2, Check, Clock, MessageSquare, MoreHorizontal } from 'lucide-react';
import { Commitment, commitmentAPI, commitmentUtils } from '@/lib/api/commitments';
import CommitmentStatusBadge from './CommitmentStatusBadge';
import { toast } from 'sonner';

interface CommitmentCardProps {
  commitment: Commitment;
  onUpdate: () => void;
  onEdit: (commitment: Commitment) => void;
}

export default function CommitmentCard({ commitment, onUpdate, onEdit }: CommitmentCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [showActions, setShowActions] = useState(false);
  
  const isOverdue = commitmentUtils.isOverdue(commitment);
  const isDueToday = commitmentUtils.isDueToday(commitment);
  const deadlineText = commitmentUtils.formatDeadline(commitment);
  const canComplete = commitment.status === 'pending';
  
  // Handle complete commitment
  const handleComplete = async () => {
    setIsLoading(true);
    try {
      await commitmentAPI.completeCommitment(commitment.id);
      toast.success('Commitment completed! 🎉');
      onUpdate();
    } catch (error) {
      toast.error('Failed to complete commitment');
      console.error('Error completing commitment:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle dismiss commitment
  const handleDismiss = async () => {
    setIsLoading(true);
    try {
      await commitmentAPI.dismissCommitment(commitment.id);
      toast.success('Commitment dismissed');
      onUpdate();
    } catch (error) {
      toast.error('Failed to dismiss commitment');
      console.error('Error dismissing commitment:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle postpone commitment (quick postpone to tomorrow)
  const handlePostpone = async () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const newDeadline = tomorrow.toISOString().split('T')[0];
    
    setIsLoading(true);
    try {
      await commitmentAPI.postponeCommitment(commitment.id, newDeadline);
      toast.success('Commitment postponed to tomorrow');
      onUpdate();
    } catch (error) {
      toast.error('Failed to postpone commitment');
      console.error('Error postponing commitment:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle delete commitment
  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this commitment?')) {
      return;
    }
    
    setIsLoading(true);
    try {
      await commitmentAPI.deleteCommitment(commitment.id);
      toast.success('Commitment deleted');
      onUpdate();
    } catch (error) {
      toast.error('Failed to delete commitment');
      console.error('Error deleting commitment:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Get card border color based on status
  const getBorderColor = () => {
    if (isOverdue) return 'border-l-red-500';
    if (isDueToday) return 'border-l-amber-500';
    if (commitment.status === 'completed') return 'border-l-green-500';
    if (commitment.status === 'dismissed') return 'border-l-gray-400';
    return 'border-l-blue-500';
  };
  
  return (
    <div className={`
      bg-white rounded-lg border border-gray-200 border-l-4 ${getBorderColor()}
      p-4 hover:shadow-md transition-shadow duration-200
      ${isLoading ? 'opacity-50' : ''}
    `}>
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate">
            {commitment.task_description}
          </h3>
        </div>
        
        <div className="flex items-center gap-2">
          <CommitmentStatusBadge commitment={commitment} size="sm" />
          
          {/* More actions button */}
          <div className="relative">
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
              disabled={isLoading}
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            
            {/* Actions dropdown */}
            {showActions && (
              <div className="absolute right-0 top-8 z-10 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1">
                <button
                  onClick={() => {
                    onEdit(commitment);
                    setShowActions(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                >
                  <Edit className="h-4 w-4" />
                  Edit
                </button>
                
                {canComplete && (
                  <button
                    onClick={() => {
                      handlePostpone();
                      setShowActions(false);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                  >
                    <Clock className="h-4 w-4" />
                    Postpone to Tomorrow
                  </button>
                )}
                
                <button
                  onClick={() => {
                    handleDelete();
                    setShowActions(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Deadline and details */}
      <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
        <span className="flex items-center gap-1">
          <Clock className="h-4 w-4" />
          {deadlineText}
        </span>
        
        {commitment.reminder_count > 0 && (
          <span className="text-xs text-gray-500">
            Reminded {commitment.reminder_count} time{commitment.reminder_count > 1 ? 's' : ''}
          </span>
        )}
        
        {commitment.original_message && (
          <span className="flex items-center gap-1 text-xs text-gray-500">
            <MessageSquare className="h-3 w-3" />
            From chat
          </span>
        )}
      </div>
      
      {/* Quick actions */}
      {canComplete && (
        <div className="mt-3 flex gap-2">
          <button
            onClick={handleComplete}
            disabled={isLoading}
            className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-green-700 bg-green-100 hover:bg-green-200 rounded-md transition-colors disabled:opacity-50"
          >
            <Check className="h-4 w-4" />
            Complete
          </button>
          
          {(isOverdue || isDueToday) && (
            <button
              onClick={handlePostpone}
              disabled={isLoading}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-amber-700 bg-amber-100 hover:bg-amber-200 rounded-md transition-colors disabled:opacity-50"
            >
              <Clock className="h-4 w-4" />
              Postpone
            </button>
          )}
        </div>
      )}
      
      {commitment.status === 'pending' && !canComplete && (
        <div className="mt-3">
          <button
            onClick={handleDismiss}
            disabled={isLoading}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Dismiss
          </button>
        </div>
      )}
      
      {/* Click outside to close actions */}
      {showActions && (
        <div
          className="fixed inset-0 z-5"
          onClick={() => setShowActions(false)}
        />
      )}
    </div>
  );
}