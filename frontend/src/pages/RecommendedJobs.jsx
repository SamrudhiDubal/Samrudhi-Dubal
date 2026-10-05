import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/axios';
import MatchScoreBadge from '../components/MatchScoreBadge';

export default function RecommendedJobs() {
  const [recommendations, setRecommendations] = useState([]);
  const [basedOn, setBasedOn] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/jobs/recommended');
        setRecommendations(data.recommendations);
        setBasedOn(data.basedOn);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load recommendations');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Recommended for You</h1>
      <p className="mt-1 text-sm text-slate-500">
        Open jobs ranked by the AI matching engine against your{' '}
        {basedOn === 'resume' ? 'resume' : 'profile skills, headline and bio'}.
        {basedOn !== 'resume' && (
          <>
            {' '}
            <Link to="/profile" className="font-medium text-brand-600 hover:underline">
              Upload a resume
            </Link>{' '}
            for more accurate matches.
          </>
        )}
      </p>

      {recommendations.length === 0 && (
        <p className="mt-4 text-slate-500">No open jobs to recommend right now.</p>
      )}

      <div className="mt-4 space-y-3">
        {recommendations.map(({ job, match, alreadyApplied }) => (
          <Link
            key={job._id}
            to={`/jobs/${job._id}`}
            className="block rounded-lg border bg-white p-4 shadow-sm transition hover:shadow-md"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-slate-900">{job.title}</h3>
                <p className="text-sm text-slate-600">
                  {job.company} · {job.location}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {alreadyApplied && (
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                    Applied
                  </span>
                )}
                <MatchScoreBadge score={match.matchScore} />
              </div>
            </div>
            <div className="mt-3 grid gap-1 text-sm sm:grid-cols-2">
              <p>
                <span className="font-medium text-emerald-700">You have:</span>{' '}
                {match.matchedSkills.join(', ') || 'None of the listed skills'}
              </p>
              <p>
                <span className="font-medium text-rose-700">To learn:</span>{' '}
                {match.missingSkills.join(', ') || 'Nothing, full skill match'}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
