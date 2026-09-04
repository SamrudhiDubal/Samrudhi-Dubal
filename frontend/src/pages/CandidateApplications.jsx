import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import MatchScoreBadge from '../components/MatchScoreBadge';

export default function CandidateApplications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/applications/mine');
        setApplications(data.applications);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load applications');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">My Applications</h1>
      {applications.length === 0 && (
        <p className="mt-4 text-slate-500">
          You haven't applied to any jobs yet.{' '}
          <Link to="/jobs" className="text-brand-600 hover:underline">
            Browse jobs
          </Link>
          .
        </p>
      )}
      <div className="mt-4 space-y-3">
        {applications.map((app) => (
          <div
            key={app._id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-white p-4 shadow-sm"
          >
            <div>
              <Link
                to={`/jobs/${app.job?._id}`}
                className="font-semibold text-slate-900 hover:underline"
              >
                {app.job?.title}
              </Link>
              <p className="text-sm text-slate-500">
                {app.job?.company} &middot; {app.job?.location}
              </p>
              <p className="mt-1 text-xs capitalize text-slate-500">Status: {app.status}</p>
            </div>
            <MatchScoreBadge score={app.matchScore} />
          </div>
        ))}
      </div>
    </div>
  );
}
