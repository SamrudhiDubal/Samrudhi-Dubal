import { useEffect, useState } from 'react';
import api from '../api/axios';
import MatchScoreBadge from './MatchScoreBadge';

// Employer view: every candidate on the platform ranked by AI match for a job,
// including people who have not applied yet.
export default function MatchingCandidates({ jobId }) {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get(`/jobs/${jobId}/matching-candidates`);
        setMatches(data.matches);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load matching candidates');
      } finally {
        setLoading(false);
      }
    })();
  }, [jobId]);

  if (loading) return <p className="mt-4 text-slate-500">Loading...</p>;
  if (error) return <p className="mt-4 text-rose-600">{error}</p>;
  if (matches.length === 0) {
    return <p className="mt-4 text-slate-500">No candidate profiles to match yet.</p>;
  }

  return (
    <div className="mt-4 space-y-3">
      {matches.map(({ candidate, match, hasApplied }) => (
        <div key={candidate._id} className="rounded-lg border bg-white p-4 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="font-semibold text-slate-900">{candidate.name}</p>
              <p className="text-sm text-slate-500">{candidate.email}</p>
              {candidate.title && <p className="text-sm text-slate-500">{candidate.title}</p>}
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                  hasApplied ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {hasApplied ? 'Applied' : 'Not applied'}
              </span>
              <MatchScoreBadge score={match.matchScore} />
            </div>
          </div>
          <div className="mt-3 grid gap-1 text-sm sm:grid-cols-2">
            <p>
              <span className="font-medium text-emerald-700">Matched:</span>{' '}
              {match.matchedSkills.join(', ') || 'None'}
            </p>
            <p>
              <span className="font-medium text-rose-700">Missing:</span>{' '}
              {match.missingSkills.join(', ') || 'None'}
            </p>
          </div>
          {!candidate.hasResume && (
            <p className="mt-2 text-xs text-slate-400">
              Matched on profile only (no resume uploaded).
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
