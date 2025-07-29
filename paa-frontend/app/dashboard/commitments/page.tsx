'use client';

import { useState, useEffect, useMemo } from 'react';
import { Plus, CheckSquare, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { commitmentAPI, Commitment, CommitmentFilters as FilterType, commitmentUtils } from '@/lib/api/commitments';
import CommitmentCard from '@/app/components/CommitmentCard';
import CommitmentFiltersComponent from '@/app/components/CommitmentFilters';
import EditCommitmentModal from '@/app/components/EditCommitmentModal';
import CreateCommitmentModal from '@/app/components/CreateCommitmentModal';
import { toast } from 'sonner';

export default function CommitmentsPage() {
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterType>({
    sort_by: 'deadline',
    order: 'asc'
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [editingCommitment, setEditingCommitment] = useState<Commitment | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Load commitments
  const loadCommitments = async () => {
    try {
      setError(null);
      const data = await commitmentAPI.getCommitments(filters);
      setCommitments(data);
    } catch (error) {
      console.error('Error loading commitments:', error);
      setError('Failed to load commitments');
      toast.error('Failed to load commitments');
    } finally {
      setIsLoading(false);
    }
  };

  // Load commitments on mount and filter changes
  useEffect(() => {
    loadCommitments();
  }, [filters]);

  // Filter commitments by search query
  const filteredCommitments = useMemo(() => {
    if (!searchQuery.trim()) return commitments;
    
    const query = searchQuery.toLowerCase();
    return commitments.filter(commitment =>
      commitment.task_description.toLowerCase().includes(query) ||
      (commitment.original_message && commitment.original_message.toLowerCase().includes(query))
    );
  }, [commitments, searchQuery]);

  // Sort commitments by priority for display
  const sortedCommitments = useMemo(() => {
    return [...filteredCommitments].sort((a, b) => {
      // First sort by priority (overdue first)
      const priorityA = commitmentUtils.getPriority(a);
      const priorityB = commitmentUtils.getPriority(b);
      
      if (priorityA !== priorityB) {
        return priorityA - priorityB;
      }
      
      // Then by the selected sort criteria
      if (filters.sort_by === 'deadline') {
        const dateA = a.deadline ? new Date(a.deadline).getTime() : 0;
        const dateB = b.deadline ? new Date(b.deadline).getTime() : 0;
        return filters.order === 'asc' ? dateA - dateB : dateB - dateA;
      } else {
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        return filters.order === 'asc' ? dateA - dateB : dateB - dateA;
      }
    });
  }, [filteredCommitments, filters]);

  // Get commitment counts for different statuses
  const counts = useMemo(() => {
    const pending = commitments.filter(c => c.status === 'pending').length;
    const overdue = commitments.filter(c => commitmentUtils.isOverdue(c)).length;
    const dueToday = commitments.filter(c => commitmentUtils.isDueToday(c)).length;
    const completed = commitments.filter(c => c.status === 'completed').length;
    
    return { pending, overdue, dueToday, completed };
  }, [commitments]);

  const handleCommitmentUpdate = () => {
    loadCommitments();
  };

  const handleEditCommitment = (commitment: Commitment) => {
    setEditingCommitment(commitment);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CheckSquare className="h-7 w-7 text-blue-600" />
            Commitments
          </h1>
          <p className="text-gray-600 mt-1">
            Track and manage your personal commitments
          </p>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => loadCommitments()}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            title="Refresh commitments"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          
          <button 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Commitment
          </button>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-blue-600">{counts.pending}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-red-600">{counts.overdue}</div>
          <div className="text-sm text-gray-600">Overdue</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-amber-600">{counts.dueToday}</div>
          <div className="text-sm text-gray-600">Due Today</div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="text-2xl font-bold text-green-600">{counts.completed}</div>
          <div className="text-sm text-gray-600">Completed</div>
        </div>
      </div>

      {/* Filters */}
      <CommitmentFiltersComponent
        filters={filters}
        onFiltersChange={setFilters}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        totalCount={commitments.length}
        filteredCount={filteredCommitments.length}
      />

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-700">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
          <button
            onClick={() => loadCommitments()}
            className="ml-auto text-sm font-medium hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Commitments list */}
      <div className="space-y-3">
        {sortedCommitments.length === 0 ? (
          <div className="text-center py-12">
            {commitments.length === 0 ? (
              <div className="space-y-3">
                <CheckSquare className="h-12 w-12 text-gray-300 mx-auto" />
                <h3 className="text-lg font-medium text-gray-900">No commitments yet</h3>
                <p className="text-gray-600 max-w-sm mx-auto">
                  Start by making commitments in your chat, or create one directly here.
                </p>
                <button 
                  onClick={() => setShowCreateModal(true)}
                  className="mt-4 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors mx-auto"
                >
                  <Plus className="h-4 w-4" />
                  Create Your First Commitment
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-gray-500">No commitments match your current filters</div>
                <button
                  onClick={() => {
                    setFilters({});
                    setSearchQuery('');
                  }}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Priority commitments (overdue/due today) */}
            {(counts.overdue > 0 || counts.dueToday > 0) && (
              <div className="space-y-3">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                  Needs Attention
                </h2>
                {sortedCommitments
                  .filter(commitment => 
                    commitmentUtils.isOverdue(commitment) || commitmentUtils.isDueToday(commitment)
                  )
                  .map(commitment => (
                    <CommitmentCard
                      key={commitment.id}
                      commitment={commitment}
                      onUpdate={handleCommitmentUpdate}
                      onEdit={handleEditCommitment}
                    />
                  ))
                }
              </div>
            )}

            {/* Other commitments */}
            <div className="space-y-3">
              {(counts.overdue > 0 || counts.dueToday > 0) && (
                <h2 className="text-lg font-semibold text-gray-900 mt-8">
                  Other Commitments
                </h2>
              )}
              
              {sortedCommitments
                .filter(commitment => 
                  !commitmentUtils.isOverdue(commitment) && !commitmentUtils.isDueToday(commitment)
                )
                .map(commitment => (
                  <CommitmentCard
                    key={commitment.id}
                    commitment={commitment}
                    onUpdate={handleCommitmentUpdate}
                    onEdit={handleEditCommitment}
                  />
                ))
              }
            </div>
          </>
        )}
      </div>

      {/* Create Commitment Modal */}
      <CreateCommitmentModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onUpdate={handleCommitmentUpdate}
      />

      {/* Edit Commitment Modal */}
      <EditCommitmentModal
        commitment={editingCommitment}
        isOpen={!!editingCommitment}
        onClose={() => setEditingCommitment(null)}
        onUpdate={handleCommitmentUpdate}
      />
    </div>
  );
}