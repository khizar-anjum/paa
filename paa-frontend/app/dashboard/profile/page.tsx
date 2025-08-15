'use client';

import { useState, useEffect } from 'react';
import { User, Edit3, Save, X, Loader2 } from 'lucide-react';
import { profileApi, UserProfile } from '@/lib/api/profile';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useDataRefresh } from '@/hooks/useDataRefresh';
import { DATA_EVENTS } from '@/lib/events/dataUpdateEvents';
import { PageOverlay } from '@/app/components/PageOverlay';
import { useSidebar } from '@/app/contexts/sidebar-context';

export default function ProfilePage() {
  const { openSidebar } = useSidebar();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  const loadProfile = async () => {
    try {
      const data = await profileApi.get();
      setProfile(data);
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Profile doesn't exist yet, show create form
        setIsEditing(true);
      } else {
        toast.error('Failed to load profile');
        console.error('Error loading profile:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  // Auto-refresh when profile is updated from chat
  useDataRefresh(
    [DATA_EVENTS.PROFILE_UPDATED],
    loadProfile,
    []
  );

  const content = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
        </div>
      );
    }

    // If profile doesn't exist or we're editing, show the form
    if (!profile || isEditing) {
      return (
        <ProfileForm 
          profile={profile}
          onSave={(savedProfile) => {
            setProfile(savedProfile);
            setIsEditing(false);
          }}
          onCancel={() => {
            if (profile) {
              setIsEditing(false);
            }
          }}
          isCreating={!profile}
        />
      );
    }

    // Show profile display
    return (
      <ProfileDisplay 
        profile={profile}
        onEdit={() => setIsEditing(true)}
      />
    );
  };

  const getPageTitle = () => {
    if (loading) return "Your Profile";
    if (!profile || isEditing) {
      return !profile ? "Create Your Profile" : "Edit Your Profile";
    }
    return "Your Profile";
  };

  return (
    <PageOverlay title={getPageTitle()} onOpenSidebar={openSidebar}>
      {content()}
    </PageOverlay>
  );
}

// Profile Display Component
function ProfileDisplay({ profile, onEdit }: { profile: UserProfile; onEdit: () => void }) {
  return (
    <div className="h-full">
      {/* Action button */}
      <div className="flex justify-end mb-6">
        <button
          onClick={onEdit}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Edit3 className="h-4 w-4" />
          Edit Profile
        </button>
      </div>

      {/* Profile Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {/* Header Section */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="h-8 w-8 text-indigo-600" />
            </div>
            <div className="flex-1">
              <h1 className="text-2xl font-bold text-gray-900">{profile.name}</h1>
              {profile.pronouns && (
                <p className="text-lg text-gray-600 mt-1">({profile.pronouns})</p>
              )}
            </div>
          </div>
        </div>

        {/* Content Sections */}
        <div className="p-6 space-y-6">
          {/* Background */}
          {profile.how_you_know_them && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Background</h3>
              <p className="text-gray-700 whitespace-pre-wrap">{profile.how_you_know_them}</p>
            </div>
          )}

          {/* About */}
          {profile.description && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">About</h3>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {profile.description}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="pt-4 border-t border-gray-100">
            <div className="text-sm text-gray-500 space-y-1">
              <p>Profile created: {new Date(profile.created_at).toLocaleDateString()}</p>
              {profile.updated_at !== profile.created_at && (
                <p>Last updated: {new Date(profile.updated_at).toLocaleDateString()}</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Profile Form Component
function ProfileForm({ 
  profile, 
  onSave, 
  onCancel, 
  isCreating 
}: { 
  profile: UserProfile | null; 
  onSave: (profile: UserProfile) => void;
  onCancel: () => void;
  isCreating: boolean;
}) {
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    how_you_know_them: profile?.how_you_know_them || '',
    pronouns: profile?.pronouns || '',
    description: profile?.description || ''
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setSaving(true);
    try {
      let savedProfile: UserProfile;
      if (isCreating) {
        savedProfile = await profileApi.create(formData);
        toast.success('Profile created successfully');
      } else {
        savedProfile = await profileApi.update(formData);
        toast.success('Profile updated successfully');
      }
      onSave(savedProfile);
    } catch (error) {
      toast.error(isCreating ? 'Failed to create profile' : 'Failed to update profile');
      console.error('Error saving profile:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (isCreating && !profile) {
      // If creating and no existing profile, reset form
      setFormData({
        name: '',
        how_you_know_them: '',
        pronouns: '',
        description: ''
      });
    } else {
      // If editing, restore original data
      setFormData({
        name: profile?.name || '',
        how_you_know_them: profile?.how_you_know_them || '',
        pronouns: profile?.pronouns || '',
        description: profile?.description || ''
      });
    }
    onCancel();
  };

  return (
    <div className="h-full">
      {/* Action buttons */}
      <div className="flex justify-end gap-2 mb-6">
        {!isCreating && (
          <button
            onClick={handleCancel}
            disabled={saving}
            className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2 disabled:opacity-50"
          >
            <X className="h-4 w-4" />
            Cancel
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={saving || !formData.name.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2 disabled:opacity-50"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          {isCreating ? 'Create Profile' : 'Save Changes'}
        </button>
      </div>

      {/* Form */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Your full name"
                required
                autoFocus
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
                value={formData.pronouns}
                onChange={(e) => setFormData({ ...formData, pronouns: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Background */}
            <div>
              <label htmlFor="background" className="block text-sm font-medium text-gray-700 mb-2">
                Background
              </label>
              <textarea
                id="background"
                rows={3}
                placeholder="Tell us about your background, where you're from, what you do..."
                value={formData.how_you_know_them}
                onChange={(e) => setFormData({ ...formData, how_you_know_them: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* About (Description) */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                About (Markdown supported)
              </label>
              <textarea
                id="description"
                rows={8}
                placeholder={`You can use markdown here:

## About Me
- Passionate about technology and innovation
- Love hiking and outdoor activities
- Currently working on personal AI assistant

**Goals:**
- Improve daily habits and productivity
- Build stronger relationships
- Learn new technologies

**Interests:**
- Machine learning and AI
- Sustainable living
- Photography`}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                Supports markdown formatting: **bold**, *italic*, lists, headers, etc.
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}