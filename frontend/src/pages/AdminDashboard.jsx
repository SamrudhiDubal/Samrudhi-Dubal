import { useEffect, useState } from 'react';
import api from '../api/axios';

const TABS = ['Overview', 'Users', 'Jobs', 'Applications'];

export default function AdminDashboard() {
  const [tab, setTab] = useState('Overview');

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
      <div className="mt-4 flex gap-2 border-b">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium ${
              tab === t
                ? 'border-b-2 border-brand-600 text-brand-700'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {tab === 'Overview' && <OverviewTab />}
        {tab === 'Users' && <UsersTab />}
        {tab === 'Jobs' && <JobsTab />}
        {tab === 'Applications' && <ApplicationsTab />}
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function OverviewTab() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/admin/stats');
        setStats(data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load stats');
      }
    })();
  }, []);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!stats) return <p className="text-slate-500">Loading...</p>;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard label="Total Users" value={stats.users.total} />
      <StatCard label="Candidates" value={stats.users.candidates} />
      <StatCard label="Employers" value={stats.users.employers} />
      <StatCard label="Total Jobs" value={stats.jobs.total} />
      <StatCard label="Open Jobs" value={stats.jobs.open} />
      <StatCard label="Total Applications" value={stats.applications.total} />
      <StatCard label="Avg. AI Match Score" value={`${stats.applications.averageMatchScore}%`} />
      <StatCard label="Shortlisted" value={stats.applications.byStatus.shortlisted || 0} />
    </div>
  );
}

function UsersTab() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [role, setRole] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchUsers = async (params = {}) => {
    setLoading(true);
    try {
      const { data } = await api.get('/admin/users', { params });
      setUsers(data.users);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    const params = {};
    if (search) params.search = search;
    if (role) params.role = role;
    fetchUsers(params);
  };

  const toggleActive = async (user) => {
    await api.put(`/admin/users/${user._id}`, { isActive: !user.isActive });
    fetchUsers({ search, role });
  };

  const handleDelete = async (user) => {
    if (!window.confirm(`Delete ${user.name} (${user.email})? This removes their data too.`))
      return;
    await api.delete(`/admin/users/${user._id}`);
    fetchUsers({ search, role });
  };

  return (
    <div>
      <form onSubmit={handleSearch} className="flex flex-wrap gap-2">
        <input
          placeholder="Search name or email..."
          className="min-w-[220px] flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={role}
          onChange={(e) => setRole(e.target.value)}
        >
          <option value="">Any role</option>
          <option value="candidate">Candidate</option>
          <option value="employer">Employer</option>
          <option value="admin">Admin</option>
        </select>
        <button className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          Search
        </button>
      </form>

      {loading && <p className="mt-4 text-slate-500">Loading...</p>}
      {error && <p className="mt-4 text-rose-600">{error}</p>}

      <div className="mt-4 space-y-2">
        {users.map((user) => (
          <div
            key={user._id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-white p-3 shadow-sm"
          >
            <div>
              <p className="font-medium text-slate-900">
                {user.name}{' '}
                <span className="ml-1 rounded bg-slate-100 px-2 py-0.5 text-xs capitalize text-slate-600">
                  {user.role}
                </span>
                {!user.isActive && (
                  <span className="ml-1 rounded bg-rose-100 px-2 py-0.5 text-xs text-rose-700">
                    deactivated
                  </span>
                )}
              </p>
              <p className="text-sm text-slate-500">{user.email}</p>
            </div>
            <div className="flex gap-2 text-sm">
              <button
                onClick={() => toggleActive(user)}
                className="rounded-md bg-slate-100 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-200"
              >
                {user.isActive ? 'Deactivate' : 'Activate'}
              </button>
              <button
                onClick={() => handleDelete(user)}
                className="rounded-md bg-rose-50 px-3 py-1.5 font-medium text-rose-700 hover:bg-rose-100"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {!loading && users.length === 0 && (
          <p className="text-slate-500">No users match your filters.</p>
        )}
      </div>
    </div>
  );
}

function JobsTab() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/admin/jobs');
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
    await api.put(`/admin/jobs/${job._id}`, { status });
    fetchJobs();
  };

  const handleDelete = async (job) => {
    if (!window.confirm(`Delete "${job.title}"? This removes its applications too.`)) return;
    await api.delete(`/admin/jobs/${job._id}`);
    fetchJobs();
  };

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <div
          key={job._id}
          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-white p-3 shadow-sm"
        >
          <div>
            <p className="font-medium text-slate-900">{job.title}</p>
            <p className="text-sm text-slate-500">
              {job.company} &middot; posted by {job.employer?.name} ({job.employer?.email})
            </p>
            <p className="text-xs capitalize text-slate-500">
              {job.status} &middot; {job.applicationsCount || 0} applicant(s)
            </p>
          </div>
          <div className="flex gap-2 text-sm">
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
      {jobs.length === 0 && <p className="text-slate-500">No jobs found.</p>}
    </div>
  );
}

function ApplicationsTab() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/admin/applications');
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
    <div className="space-y-2">
      {applications.map((app) => (
        <div key={app._id} className="rounded-lg border bg-white p-3 shadow-sm">
          <p className="font-medium text-slate-900">
            {app.candidate?.name} &rarr; {app.job?.title} ({app.job?.company})
          </p>
          <p className="text-sm text-slate-500">
            {app.candidate?.email} &middot; {app.matchScore}% match &middot;{' '}
            <span className="capitalize">{app.status}</span>
          </p>
        </div>
      ))}
      {applications.length === 0 && <p className="text-slate-500">No applications yet.</p>}
    </div>
  );
}
