'use client';

import { useState } from 'react';
import { Search, Filter, SortAsc, SortDesc, Repeat, Target } from 'lucide-react';
import { CommitmentFilters as FilterType } from '@/lib/api/commitments';

interface CommitmentFiltersProps {
  filters: FilterType;
  onFiltersChange: (filters: FilterType) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  totalCount: number;
  filteredCount: number;
}

export default function CommitmentFilters({
  filters,
  onFiltersChange,
  searchQuery,
  onSearchChange,
  totalCount,
  filteredCount
}: CommitmentFiltersProps) {
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // Status filter options
  const statusOptions = [
    { value: '', label: 'All' },
    { value: 'pending', label: 'Pending' },
    { value: 'active', label: 'Active' },
    { value: 'completed', label: 'Completed' },
    { value: 'dismissed', label: 'Dismissed' },
    { value: 'missed', label: 'Missed' }
  ];

  // Type filter options
  const typeOptions = [
    { value: '', label: 'All Types', icon: null },
    { value: 'one_time', label: 'One-time', icon: Target },
    { value: 'recurring', label: 'Recurring', icon: Repeat }
  ];
  
  // Sort options
  const sortOptions = [
    { value: 'deadline', label: 'Deadline' },
    { value: 'created_at', label: 'Created' }
  ];
  
  const handleStatusChange = (status: string) => {
    onFiltersChange({
      ...filters,
      status: status || undefined
    });
  };

  const handleTypeChange = (type: string) => {
    onFiltersChange({
      ...filters,
      type: type ? (type as 'one_time' | 'recurring') : undefined
    });
  };
  
  const handleOverdueToggle = () => {
    onFiltersChange({
      ...filters,
      overdue: filters.overdue === true ? undefined : true
    });
  };
  
  const handleSortChange = (sortBy: string) => {
    onFiltersChange({
      ...filters,
      sort_by: sortBy as 'created_at' | 'deadline'
    });
  };
  
  const handleOrderToggle = () => {
    onFiltersChange({
      ...filters,
      order: filters.order === 'asc' ? 'desc' : 'asc'
    });
  };
  
  const clearFilters = () => {
    onFiltersChange({});
    onSearchChange('');
  };
  
  const hasActiveFilters = filters.status || filters.type || filters.overdue || searchQuery;
  
  return (
    <div className="space-y-4">
      {/* Search and main filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search commitments..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        {/* Sort controls */}
        <div className="flex gap-2">
          <select
            value={filters.sort_by || 'created_at'}
            onChange={(e) => handleSortChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {sortOptions.map(option => (
              <option key={option.value} value={option.value}>
                Sort by {option.label}
              </option>
            ))}
          </select>
          
          <button
            onClick={handleOrderToggle}
            className="px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            title={`Sort ${filters.order === 'asc' ? 'ascending' : 'descending'}`}
          >
            {filters.order === 'asc' ? (
              <SortAsc className="h-4 w-4" />
            ) : (
              <SortDesc className="h-4 w-4" />
            )}
          </button>
        </div>
        
        {/* Advanced filters toggle */}
        <button
          onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
          className={`px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 flex items-center gap-2 ${
            showAdvancedFilters 
              ? 'bg-blue-100 border-blue-300 text-blue-700' 
              : 'border-gray-300 hover:bg-gray-50'
          }`}
        >
          <Filter className="h-4 w-4" />
          Filters
        </button>
      </div>
      
      {/* Status and Type filter tabs */}
      <div className="space-y-3">
        {/* Status filters */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Status</h4>
          <div className="flex flex-wrap gap-2">
            {statusOptions.map(option => (
              <button
                key={option.value}
                onClick={() => handleStatusChange(option.value)}
                className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                  (filters.status || '') === option.value
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-transparent'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Type filters */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Type</h4>
          <div className="flex flex-wrap gap-2">
            {typeOptions.map(option => {
              const IconComponent = option.icon;
              return (
                <button
                  key={option.value}
                  onClick={() => handleTypeChange(option.value)}
                  className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors flex items-center gap-1 ${
                    (filters.type || '') === option.value
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-transparent'
                  }`}
                >
                  {IconComponent && <IconComponent className="h-3 w-3" />}
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* Advanced filters */}
      {showAdvancedFilters && (
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="space-y-3">
            <h4 className="font-medium text-gray-900">Advanced Filters</h4>
            
            {/* Overdue filter */}
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.overdue === true}
                onChange={handleOverdueToggle}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Show only overdue commitments</span>
            </label>
          </div>
        </div>
      )}
      
      {/* Results summary and clear filters */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>
          Showing {filteredCount} of {totalCount} commitments
        </span>
        
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}