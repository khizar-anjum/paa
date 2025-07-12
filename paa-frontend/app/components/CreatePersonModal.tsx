'use client';

import { useState } from 'react';
import { X, Save, Loader2 } from 'lucide-react';
import { PersonCreate, peopleApi } from '@/lib/api/people';
import { toast } from 'sonner';

interface CreatePersonModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPersonCreated: () => void;
}

export function CreatePersonModal({ isOpen, onClose, onPersonCreated }: CreatePersonModalProps) {
  const [formData, setFormData] = useState<PersonCreate>({
    name: '',
    how_you_know_them: '',
    pronouns: '',
    description: ''
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setSaving(true);
    try {
      await peopleApi.create(formData);
      toast.success('Person added successfully');
      onPersonCreated();
      handleClose();
    } catch (error) {
      toast.error('Failed to add person');
      console.error('Error creating person:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      how_you_know_them: '',
      pronouns: '',
      description: ''
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Add New Person</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-6">
            {/* Name */}
            <div>
              <label htmlFor="modal-name" className="block text-sm font-medium text-gray-700 mb-2">
                Name *
              </label>
              <input
                type="text"
                id="modal-name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter person's name"
                required
                autoFocus
              />
            </div>

            {/* Pronouns */}
            <div>
              <label htmlFor="modal-pronouns" className="block text-sm font-medium text-gray-700 mb-2">
                Pronouns
              </label>
              <input
                type="text"
                id="modal-pronouns"
                value={formData.pronouns}
                onChange={(e) => setFormData({ ...formData, pronouns: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="they/them, she/her, he/him, etc."
              />
            </div>

            {/* How You Know Them */}
            <div>
              <label htmlFor="modal-how-know" className="block text-sm font-medium text-gray-700 mb-2">
                How You Know Them
              </label>
              <textarea
                id="modal-how-know"
                rows={3}
                value={formData.how_you_know_them}
                onChange={(e) => setFormData({ ...formData, how_you_know_them: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., College roommate, coworker at XYZ Corp, friend from hiking group..."
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="modal-description" className="block text-sm font-medium text-gray-700 mb-2">
                Description (Markdown supported)
              </label>
              <textarea
                id="modal-description"
                rows={8}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                placeholder={`You can use markdown here:

## Personal Notes
- Loves hiking and photography
- Has a dog named Max
- Works in tech, specifically frontend development

**Important dates:**
- Birthday: March 15th
- Anniversary: June 20th`}
              />
              <p className="text-xs text-gray-500 mt-1">
                Supports markdown formatting: **bold**, *italic*, lists, headers, etc.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 mt-8 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              disabled={saving}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving || !formData.name.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Add Person
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}