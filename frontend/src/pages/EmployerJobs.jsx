import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';

export default function EmployerJobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/jobs/employer/mine');
      setJobs(data.jobs);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const toggleStatus = async (job) => {
    const status = job.status === 'open' ? 'closed' : 'open';
    await api.put(`/jobs/${job._id}`, { status });
    fetchJobs();
  };

  const handleDelete = async (job) => {
    if (!window.confirm(`Delete "${job.title}"? This also removes its applications.`)) return;
    await api.delete(`/jobs/${job._id}`);
    fetchJobs();
  };

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">My Job Postings</h1>
        <Link
          to="/employer/post-job"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          + Post a Job
        </Link>
      </div>

      {jobs.length === 0 && (
        <p className="text-slate-500">You haven't posted any jobs yet.</p>
      )}

      <div className="space-y-3">
        {jobs.map((job) => (
          <div
            key={job._id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-white p-4 shadow-sm"
          >
            <div>
              <Link to={`/jobs/${job._id}`} className="font-semibold text-slate-900 hover:underline">
                {job.title}
              </Link>
              <p className="text-sm text-slate-500">
                {job.location} &middot; {job.applicationsCount || 0} applicant(s) &middot;{' '}
                <span className={job.status === 'open' ? 'text-emerald-600' : 'text-slate-400'}>
                  {job.status}
                </span>
              </p>
            </div>
            <div className="flex flex-wrap gap-2 text-sm">
              <Link
                to={`/employer/jobs/${job._id}/applicants`}
                className="rounded-md bg-brand-50 px-3 py-1.5 font-medium text-brand-700 hover:bg-brand-100"
              >
                View Applicants
              </Link>
              <Link
                to={`/employer/jobs/${job._id}/edit`}
                className="rounded-md bg-slate-100 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-200"
              >
                Edit
              </Link>
              <button
                onClick={() => toggleStatus(job)}
                className="rounded-md bg-slate-100 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-200"
              >
                {job.status === 'open' ? 'Close' : 'Reopen'}
              </button>
              <button
                onClick={() => handleDelete(job)}
                className="rounded-md bg-rose-50 px-3 py-1.5 font-medium text-rose-700 hover:bg-rose-100"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
