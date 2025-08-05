'use client';

import { useState, useEffect } from 'react';
import { Calendar, CheckCircle, SkipForward, X, Clock, TrendingUp } from 'lucide-react';
import { Commitment, CommitmentCompletion, commitmentAPI, commitmentUtils } from '@/lib/api/commitments';
import { toast } from 'sonner';

interface CommitmentCompletionsProps {
  commitment: Commitment;
  isOpen: boolean;
  onClose: () => void;
}

export default function CommitmentCompletions({
  commitment,
  isOpen,
  onClose
}: CommitmentCompletionsProps) {
  const [completions, setCompletions] = useState<CommitmentCompletion[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen && commitmentUtils.isRecurring(commitment)) {
      fetchCompletions();
    }
  }, [isOpen, commitment.id]);

  const fetchCompletions = async () => {
    setIsLoading(true);
    try {
      const data = await commitmentAPI.getCommitmentCompletions(commitment.id);
      setCompletions(data);
    } catch (error) {
      console.error('Error fetching completions:', error);
      toast.error('Failed to load completion history');
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate stats
  const totalCompletions = completions.filter(c => !c.skipped).length;
  const totalSkips = completions.filter(c => c.skipped).length;
  const totalEntries = completions.length;

  // Get recent completions (last 30 days)
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  
  const recentCompletions = completions.filter(c => 
    new Date(c.completion_date) >= thirtyDaysAgo
  );

  // Calculate completion rate for last 30 days
  const recentCompletionRate = recentCompletions.length > 0 
    ? Math.round((recentCompletions.filter(c => !c.skipped).length / recentCompletions.length) * 100)
    : 0;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              Completion History
            </h2>
            <p className="text-sm text-gray-600 mt-1">{commitment.task_description}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Stats */}
        <div className="p-6 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{totalCompletions}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{totalSkips}</div>
              <div className="text-sm text-gray-600">Skipped</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{totalEntries}</div>
              <div className="text-sm text-gray-600">Total Entries</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{recentCompletionRate}%</div>
              <div className="text-sm text-gray-600">30-day Rate</div>
            </div>
          </div>
        </div>

        {/* Completions List */}
        <div className="p-6 overflow-y-auto max-h-96">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : completions.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No completions yet</h3>
              <p className="text-gray-600">Complete or skip this commitment to start tracking your progress.</p>
            </div>
          ) : (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Recent Activity</h3>
              {completions
                .sort((a, b) => new Date(b.completion_date).getTime() - new Date(a.completion_date).getTime())
                .slice(0, 20) // Show last 20 entries
                .map((completion) => (
                  <div
                    key={completion.id}
                    className={`flex items-center justify-between p-3 rounded-lg border ${
                      completion.skipped
                        ? 'bg-gray-50 border-gray-200'
                        : 'bg-green-50 border-green-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {completion.skipped ? (
                        <SkipForward className="h-4 w-4 text-gray-500" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      )}
                      <div>
                        <div className="font-medium text-sm">
                          {completion.skipped ? 'Skipped' : 'Completed'}
                        </div>
                        <div className="text-xs text-gray-600">
                          {new Date(completion.completion_date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-xs text-gray-500 flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(completion.completed_at).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit'
                        })}
                      </div>
                      {completion.notes && (
                        <div className="text-xs text-gray-600 mt-1 max-w-32 truncate">
                          "{completion.notes}"
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              
              {completions.length > 20 && (
                <div className="text-center pt-4">
                  <p className="text-sm text-gray-500">
                    Showing latest 20 of {completions.length} total entries
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <TrendingUp className="h-4 w-4" />
              <span>
                {commitmentUtils.formatRecurrence(commitment)} • 
                Started {new Date(commitment.created_at).toLocaleDateString()}
              </span>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>

      {/* Click outside to close */}
      <div
        className="absolute inset-0 -z-10"
        onClick={onClose}
      />
    </div>
  );
}