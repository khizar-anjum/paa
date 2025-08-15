'use client';

import { useState, useEffect } from 'react';
import { Plus, User, Users, Loader2, Edit3, Save, X, Trash2 } from 'lucide-react';
import { peopleApi, Person } from '@/lib/api/people';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CreatePersonModal } from '@/app/components/CreatePersonModal';
import { useDataRefresh } from '@/hooks/useDataRefresh';
import { DATA_EVENTS } from '@/lib/events/dataUpdateEvents';
import { PageOverlay } from '@/app/components/PageOverlay';
import { useSidebar } from '@/app/contexts/sidebar-context';

export default function PeoplePage() {
  const { openSidebar } = useSidebar();
  const [people, setPeople] = useState<Person[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const loadPeople = async () => {
    try {
      const data = await peopleApi.getAll();
      setPeople(data);
    } catch (error) {
      toast.error('Failed to load people');
      console.error('Error loading people:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPeople();
  }, []);

  // Auto-refresh when profiles are updated from chat
  useDataRefresh(
    [DATA_EVENTS.PROFILE_UPDATED],
    loadPeople,
    []
  );

  const handlePersonClick = (person: Person) => {
    setSelectedPerson(person);
  };

  const handleBackToList = () => {
    setSelectedPerson(null);
    loadPeople(); // Refresh the list in case of updates
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    );
  }

  // If a person is selected, show the detail view
  if (selectedPerson) {
    return (
      <PersonDetailView 
        person={selectedPerson} 
        onBack={handleBackToList}
        onUpdate={(updatedPerson) => setSelectedPerson(updatedPerson)}
      />
    );
  }

  return (
    <PageOverlay title="People You Know" onOpenSidebar={openSidebar}>
      <div className="h-full">
        {/* Action button */}
        <div className="flex justify-end mb-6">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Person
          </button>
        </div>

        {/* People Grid */}
        {people.length === 0 ? (
          <div className="text-center py-12">
            <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No people added yet</h3>
            <p className="text-gray-600 mb-4">Start building your network by adding people you know</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Your First Person
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {people.map((person) => (
              <PersonCard
                key={person.id}
                person={person}
                onClick={() => handlePersonClick(person)}
              />
            ))}
          </div>
        )}

        {/* Create Person Modal */}
        <CreatePersonModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onPersonCreated={loadPeople}
        />
      </div>
    </PageOverlay>
  );
}

// Person Card Component
function PersonCard({ person, onClick }: { person: Person; onClick: () => void }) {
  return (
    <div
      onClick={onClick}
      className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer"
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <User className="h-6 w-6 text-blue-600" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 truncate">
              {person.name}
            </h3>
            {person.pronouns && (
              <span className="text-sm text-gray-500">({person.pronouns})</span>
            )}
          </div>
          {person.how_you_know_them && (
            <p className="text-sm text-gray-600 mt-1">{person.how_you_know_them}</p>
          )}
          {person.description && (
            <p className="text-sm text-gray-500 mt-2 line-clamp-2">
              {person.description.length > 100 
                ? person.description.substring(0, 100) + '...' 
                : person.description}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

// Person Detail View Component
function PersonDetailView({ 
  person, 
  onBack, 
  onUpdate 
}: { 
  person: Person; 
  onBack: () => void;
  onUpdate: (person: Person) => void;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: person.name,
    how_you_know_them: person.how_you_know_them || '',
    pronouns: person.pronouns || '',
    description: person.description || ''
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updatedPerson = await peopleApi.update(person.id, editForm);
      onUpdate(updatedPerson);
      setIsEditing(false);
      toast.success('Person updated successfully');
    } catch (error) {
      toast.error('Failed to update person');
      console.error('Error updating person:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditForm({
      name: person.name,
      how_you_know_them: person.how_you_know_them || '',
      pronouns: person.pronouns || '',
      description: person.description || ''
    });
    setIsEditing(false);
  };

  if (isEditing) {
    return <PersonEditForm 
      person={person}
      editForm={editForm}
      setEditForm={setEditForm}
      onSave={handleSave}
      onCancel={handleCancel}
      saving={saving}
      onBack={onBack}
    />;
  }

  return <PersonDisplayView 
    person={person}
    onEdit={() => setIsEditing(true)}
    onBack={onBack}
  />;
}

// Person Display View Component
function PersonDisplayView({ 
  person, 
  onEdit, 
  onBack 
}: { 
  person: Person; 
  onEdit: () => void;
  onBack: () => void;
}) {
  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
        >
          ← Back to People
        </button>
        <button
          onClick={onEdit}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Edit3 className="h-4 w-4" />
          Edit
        </button>
      </div>

      {/* Person Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Header Section */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="h-8 w-8 text-blue-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{person.name}</h1>
              {person.pronouns && (
                <p className="text-lg text-gray-600 mt-1">({person.pronouns})</p>
              )}
            </div>
          </div>
        </div>

        {/* Content Sections */}
        <div className="p-6 space-y-6">
          {/* How You Know Them */}
          {person.how_you_know_them && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">How You Know Them</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{person.how_you_know_them}</p>
            </div>
          )}

          {/* Description */}
          {person.description && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Description</h3>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {person.description}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="pt-4 border-t border-gray-100">
            <div className="text-sm text-gray-500 space-y-1">
              <p>Added: {new Date(person.created_at).toLocaleDateString()}</p>
              {person.updated_at !== person.created_at && (
                <p>Updated: {new Date(person.updated_at).toLocaleDateString()}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Person Edit Form Component
function PersonEditForm({ 
  person,
  editForm, 
  setEditForm, 
  onSave, 
  onCancel, 
  saving,
  onBack 
}: { 
  person: Person;
  editForm: { name: string; how_you_know_them: string; pronouns: string; description: string };
  setEditForm: (form: any) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
  onBack: () => void;
}) {
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${person.name}? This action cannot be undone.`)) {
      return;
    }
    
    setDeleteLoading(true);
    try {
      await peopleApi.delete(person.id);
      toast.success('Person deleted successfully');
      onBack(); // Go back to list after deletion
    } catch (error) {
      toast.error('Failed to delete person');
      console.error('Error deleting person:', error);
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <div className="h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={onBack}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
        >
          ← Back to People
        </button>
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            disabled={saving}
            className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <X className="h-4 w-4" />
            Cancel
          </button>
          <button
            onClick={onSave}
            disabled={saving || !editForm.name.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Save
          </button>
        </div>
      </div>

      {/* Edit Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Edit {person.name}</h1>
          
          <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); onSave(); }}>
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Name *
              </label>
              <input
                type="text"
                id="name"
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {/* Pronouns */}
            <div>
              <label htmlFor="pronouns" className="block text-sm font-medium text-gray-700 mb-2">
                Pronouns
              </label>
              <input
                type="text"
                id="pronouns"
                placeholder="they/them, she/her, he/him, etc."
                value={editForm.pronouns}
                onChange={(e) => setEditForm({ ...editForm, pronouns: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* How You Know Them */}
            <div>
              <label htmlFor="how_you_know_them" className="block text-sm font-medium text-gray-700 mb-2">
                How You Know Them
              </label>
              <textarea
                id="how_you_know_them"
                rows={3}
                placeholder="e.g., College roommate, coworker at XYZ Corp, friend from hiking group..."
                value={editForm.how_you_know_them}
                onChange={(e) => setEditForm({ ...editForm, how_you_know_them: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                Description (Markdown supported)
              </label>
              <textarea
                id="description"
                rows={8}
                placeholder="You can use markdown here:&#10;&#10;## Personal Notes&#10;- Loves hiking and photography&#10;- Has a dog named Max&#10;- Works in tech, specifically frontend development&#10;&#10;**Important dates:**&#10;- Birthday: March 15th&#10;- Anniversary: June 20th"
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                Supports markdown formatting: **bold**, *italic*, lists, headers, etc.
              </p>
            </div>
          </form>

          {/* Danger Zone */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-red-900">Danger Zone</h3>
                <p className="text-sm text-red-600">This action cannot be undone.</p>
              </div>
              <button
                onClick={handleDelete}
                disabled={deleteLoading}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {deleteLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                Delete Person
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}