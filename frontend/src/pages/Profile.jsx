import { useState } from 'react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({
    name: user?.name || '',
    title: user?.title || '',
    bio: user?.bio || '',
    company: user?.company || '',
    skills: (user?.skills || []).join(', '),
  });
  const [status, setStatus] = useState(null);
  const [saving, setSaving] = useState(false);
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeStatus, setResumeStatus] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleResumeUpload = async (e) => {
    e.preventDefault();
    if (!resumeFile) return;
    setUploading(true);
    setResumeStatus(null);
    try {
      const body = new FormData();
      body.append('resume', resumeFile);
      const { data } = await api.post('/users/me/resume', body);
      updateUser(data.user);
      setResumeStatus({
        type: 'success',
        message: `Resume saved. Skills detected: ${data.detectedSkills.join(', ') || 'none'}`,
      });
    } catch (err) {
      setResumeStatus({ type: 'error', message: err.response?.data?.message || 'Upload failed' });
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      const payload = {
        name: form.name,
        title: form.title,
        bio: form.bio,
        skills: form.skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      };
      if (user.role === 'employer') payload.company = form.company;
      const { data } = await api.put('/users/me', payload);
      updateUser(data.user);
      setStatus({ type: 'success', message: 'Profile updated' });
    } catch (err) {
      setStatus({ type: 'error', message: err.response?.data?.message || 'Update failed' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-4 text-2xl font-bold text-slate-900">My Profile</h1>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border bg-white p-6 shadow-sm">
        {status && (
          <p
            className={`rounded p-2 text-sm ${
              status.type === 'success'
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-rose-50 text-rose-700'
            }`}
          >
            {status.message}
          </p>
        )}
        <div>
          <label className="text-sm font-medium text-slate-700">Name</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        {user?.role === 'employer' && (
          <div>
            <label className="text-sm font-medium text-slate-700">Company</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
            />
          </div>
        )}
        <div>
          <label className="text-sm font-medium text-slate-700">Title / Headline</label>
          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
        </div>
        {user?.role === 'candidate' && (
          <div>
            <label className="text-sm font-medium text-slate-700">Skills (comma separated)</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              value={form.skills}
              onChange={(e) => setForm({ ...form, skills: e.target.value })}
            />
            <p className="mt-1 text-xs text-slate-500">
              These are combined with the skills detected in your resume during AI screening.
            </p>
          </div>
        )}
        <div>
          <label className="text-sm font-medium text-slate-700">Bio</label>
          <textarea
            rows={4}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            value={form.bio}
            onChange={(e) => setForm({ ...form, bio: e.target.value })}
          />
        </div>
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-brand-600 px-5 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </form>

      {user?.role === 'candidate' && (
        <form
          onSubmit={handleResumeUpload}
          className="mt-6 space-y-3 rounded-lg border bg-white p-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-slate-900">Profile Resume</h2>
          <p className="text-sm text-slate-500">
            {user.resumeText
              ? 'A resume is on file and powers your job recommendations. Upload a new one to replace it.'
              : 'Upload a resume (PDF, DOCX, DOC or TXT) to get AI job recommendations and appear in employer candidate searches.'}
          </p>
          {resumeStatus && (
            <p
              className={`rounded p-2 text-sm ${
                resumeStatus.type === 'success'
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-rose-50 text-rose-700'
              }`}
            >
              {resumeStatus.message}
            </p>
          )}
          <label htmlFor="profile-resume" className="sr-only">
            Resume file
          </label>
          <input
            id="profile-resume"
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            onChange={(e) => setResumeFile(e.target.files[0] || null)}
            className="block w-full text-sm text-slate-600"
          />
          <button
            type="submit"
            disabled={!resumeFile || uploading}
            className="rounded-md bg-brand-600 px-5 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
          >
            {uploading ? 'Uploading...' : 'Upload Resume'}
          </button>
        </form>
      )}
    </div>
  );
}
