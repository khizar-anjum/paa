'use client';

import { Clock, CheckCircle, XCircle, AlertTriangle, Circle } from 'lucide-react';
import { Commitment, commitmentUtils } from '@/lib/api/commitments';

interface CommitmentStatusBadgeProps {
  commitment: Commitment;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function CommitmentStatusBadge({ 
  commitment, 
  showIcon = true, 
  size = 'md' 
}: CommitmentStatusBadgeProps) {
  const isOverdue = commitmentUtils.isOverdue(commitment);
  const isDueToday = commitmentUtils.isDueToday(commitment);
  
  // Get status info
  const getStatusInfo = () => {
    if (isOverdue) {
      return {
        label: 'Overdue',
        icon: AlertTriangle,
        className: 'text-red-700 bg-red-100 border-red-300'
      };
    }
    
    if (isDueToday) {
      return {
        label: 'Due Today',
        icon: Clock,
        className: 'text-amber-700 bg-amber-100 border-amber-300'
      };
    }
    
    switch (commitment.status) {
      case 'completed':
        return {
          label: 'Completed',
          icon: CheckCircle,
          className: 'text-green-700 bg-green-100 border-green-300'
        };
      case 'dismissed':
        return {
          label: 'Dismissed',
          icon: XCircle,
          className: 'text-gray-700 bg-gray-100 border-gray-300'
        };
      case 'missed':
        return {
          label: 'Missed',
          icon: XCircle,
          className: 'text-red-700 bg-red-100 border-red-300'
        };
      case 'pending':
      default:
        return {
          label: 'Pending',
          icon: Circle,
          className: 'text-blue-700 bg-blue-100 border-blue-300'
        };
    }
  };
  
  const statusInfo = getStatusInfo();
  const Icon = statusInfo.icon;
  
  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base'
  };
  
  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };
  
  return (
    <span className={`
      inline-flex items-center gap-1.5 
      ${sizeClasses[size]} 
      ${statusInfo.className}
      font-medium rounded-full border
    `}>
      {showIcon && <Icon className={iconSizes[size]} />}
      {statusInfo.label}
    </span>
  );
}