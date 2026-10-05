import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';
import MatchScoreBadge from '../components/MatchScoreBadge';
import MatchingCandidates from '../components/MatchingCandidates';

const STATUS_OPTIONS = ['applied', 'shortlisted', 'rejected', 'hired'];

export default function Applicants() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [tab, setTab] = useState('applicants');

  const fetchApplicants = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/applications/job/${id}`);
      setJob(data.job);
      setApplications(data.applications);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load applicants');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplicants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleStatusChange = async (appId, status) => {
    await api.put(`/applications/${appId}/status`, { status });
    setApplications((prev) => prev.map((a) => (a._id === appId ? { ...a, status } : a)));
  };

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">
        Applicants for {job?.title}{' '}
        <span className="text-base font-normal text-slate-500">
          ({applications.length} total, ranked by AI match)
        </span>
      </h1>

      <div className="mt-4 flex gap-2 border-b">
        {[
          ['applicants', 'Applicants'],
          ['matching', 'Find Matching Candidates'],
        ].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab === key
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'matching' && <MatchingCandidates jobId={id} />}

      {tab === 'applicants' && applications.length === 0 && (
        <p className="mt-4 text-slate-500">No applicants yet.</p>
      )}

      {tab === 'applicants' && (
        <div className="mt-4 space-y-3">
          {applications.map((app) => (
            <div key={app._id} className="rounded-lg border bg-white p-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-900">{app.candidate?.name}</p>
                  <p className="text-sm text-slate-500">{app.candidate?.email}</p>
                  {app.candidate?.title && (
                    <p className="text-sm text-slate-500">{app.candidate.title}</p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <MatchScoreBadge score={app.matchScore} />
                  <select
                    value={app.status}
                    onChange={(e) => handleStatusChange(app._id, e.target.value)}
                    className="rounded-md border border-slate-300 px-2 py-1 text-sm capitalize"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <button
                onClick={() => setExpanded(expanded === app._id ? null : app._id)}
                className="mt-3 text-sm font-medium text-brand-600 hover:underline"
              >
                {expanded === app._id ? 'Hide AI match details' : 'View AI match details'}
              </button>

              {expanded === app._id && (
                <div className="mt-3 grid gap-3 rounded-md bg-slate-50 p-3 text-sm sm:grid-cols-2">
                  <div>
                    <p className="font-medium text-slate-700">
                      Skill Match: {app.matchDetails?.skillMatchPercent}%
                    </p>
                    <p className="mt-1">
                      <span className="font-medium text-emerald-700">Matched:</span>{' '}
                      {app.matchDetails?.matchedSkills?.join(', ') || 'None'}
                    </p>
                    <p className="mt-1">
                      <span className="font-medium text-rose-700">Missing:</span>{' '}
                      {app.matchDetails?.missingSkills?.join(', ') || 'None'}
                    </p>
                  </div>
                  <div>
                    <p className="font-medium text-slate-700">
                      Resume/Description Similarity: {app.matchDetails?.textSimilarityPercent}%
                    </p>
                    <p className="mt-1 font-medium text-slate-700">
                      Experience Fit: {app.matchDetails?.experienceFitPercent ?? 'Unknown'}
                      {app.matchDetails?.experienceFitPercent !== null &&
                      app.matchDetails?.experienceFitPercent !== undefined
                        ? '%'
                        : ''}{' '}
                      {app.matchDetails?.candidateYearsOfExperience !== null &&
                        app.matchDetails?.candidateYearsOfExperience !== undefined && (
                          <span className="text-slate-500">
                            ({app.matchDetails.candidateYearsOfExperience} yrs mentioned)
                          </span>
                        )}
                    </p>
                    {app.matchDetails?.educationLevel && (
                      <p className="mt-1 text-slate-600">
                        Education detected:{' '}
                        <span className="capitalize">
                          {app.matchDetails.educationLevel.replace('_', ' ')}
                        </span>
                      </p>
                    )}
                    {app.matchDetails?.semanticScore !== null &&
                      app.matchDetails?.semanticScore !== undefined && (
                        <p className="mt-1 rounded bg-brand-50 p-2 text-brand-700">
                          <span className="font-medium">
                            AI summary ({app.matchDetails.semanticScore}%):
                          </span>{' '}
                          {app.matchDetails.semanticSummary}
                        </p>
                      )}
                    {app.coverLetter && (
                      <p className="mt-1">
                        <span className="font-medium text-slate-700">Cover letter:</span>{' '}
                        {app.coverLetter}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
