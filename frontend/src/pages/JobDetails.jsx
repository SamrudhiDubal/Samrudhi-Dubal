import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

export default function JobDetails() {
  const { id } = useParams();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [applyStatus, setApplyStatus] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/jobs/${id}`);
        setJob(data.job);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load job');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleApply = async (e) => {
    e.preventDefault();
    if (!resumeFile) {
      setApplyStatus({ type: 'error', message: 'Please attach a resume (PDF, DOCX, or TXT).' });
      return;
    }
    setSubmitting(true);
    setApplyStatus(null);
    try {
      const formData = new FormData();
      formData.append('resume', resumeFile);
      if (coverLetter) formData.append('coverLetter', coverLetter);
      const { data } = await api.post(`/applications/${id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setApplyStatus({
        type: 'success',
        message: `Application submitted! Your AI match score: ${data.application.matchScore}%`,
      });
    } catch (err) {
      setApplyStatus({ type: 'error', message: err.response?.data?.message || 'Failed to apply' });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;
  if (!job) return null;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <div className="rounded-lg border bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">{job.title}</h1>
          <p className="mt-1 text-slate-600">
            {job.company} &middot; {job.location}
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
            <span className="rounded-full bg-slate-100 px-2.5 py-1 capitalize">
              {job.jobType?.replace('-', ' ')}
            </span>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 capitalize">
              {job.experienceLevel} level
            </span>
            {(job.salaryMin || job.salaryMax) && (
              <span className="rounded-full bg-slate-100 px-2.5 py-1">
                ${job.salaryMin ?? '—'} - ${job.salaryMax ?? '—'}
              </span>
            )}
          </div>

          <h2 className="mt-6 font-semibold text-slate-900">Description</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-slate-700">{job.description}</p>

          {job.skillsRequired?.length > 0 && (
            <>
              <h2 className="mt-6 font-semibold text-slate-900">Required Skills</h2>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {job.skillsRequired.map((skill) => (
                  <span
                    key={skill}
                    className="rounded bg-brand-50 px-2 py-0.5 text-xs text-brand-700"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <div>
        <div className="rounded-lg border bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-slate-900">Apply now</h2>
          {!user && (
            <p className="mt-2 text-sm text-slate-600">
              Please log in as a candidate to apply for this job.
            </p>
          )}
          {user && user.role === 'employer' && (
            <p className="mt-2 text-sm text-slate-600">Employers cannot apply to jobs.</p>
          )}
          {user && user.role === 'candidate' && (
            <form onSubmit={handleApply} className="mt-3 space-y-3">
              <div>
                <label className="text-sm font-medium text-slate-700">Resume</label>
                <input
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(e) => setResumeFile(e.target.files[0])}
                  className="mt-1 block w-full text-sm"
                />
                <p className="mt-1 text-xs text-slate-500">
                  Our AI engine will parse your resume and score it against this job automatically.
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">
                  Cover letter (optional)
                </label>
                <textarea
                  rows={4}
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-md bg-brand-600 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
              >
                {submitting ? 'Submitting...' : 'Submit Application'}
              </button>
              {applyStatus && (
                <p
                  className={`text-sm ${
                    applyStatus.type === 'success' ? 'text-emerald-700' : 'text-rose-600'
                  }`}
                >
                  {applyStatus.message}
                </p>
              )}
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
