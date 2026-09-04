import { useEffect, useState } from 'react';
import api from '../api/axios';
import JobCard from '../components/JobCard';

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({ search: '', location: '', jobType: '' });

  const fetchJobs = async (params = {}) => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get('/jobs', { params });
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

  const handleSearch = (e) => {
    e.preventDefault();
    const params = {};
    if (filters.search) params.search = filters.search;
    if (filters.location) params.location = filters.location;
    if (filters.jobType) params.jobType = filters.jobType;
    fetchJobs(params);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Browse Jobs</h1>
      <form onSubmit={handleSearch} className="mt-4 flex flex-wrap gap-2">
        <input
          placeholder="Search title, description, company..."
          className="min-w-[240px] flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        />
        <input
          placeholder="Location"
          className="w-40 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          value={filters.location}
          onChange={(e) => setFilters({ ...filters, location: e.target.value })}
        />
        <select
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={filters.jobType}
          onChange={(e) => setFilters({ ...filters, jobType: e.target.value })}
        >
          <option value="">Any type</option>
          <option value="full-time">Full-time</option>
          <option value="part-time">Part-time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
        </select>
        <button
          type="submit"
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          Search
        </button>
      </form>

      {loading && <p className="mt-6 text-slate-500">Loading jobs...</p>}
      {error && <p className="mt-6 text-rose-600">{error}</p>}
      {!loading && !error && jobs.length === 0 && (
        <p className="mt-6 text-slate-500">No jobs found. Try a different search.</p>
      )}

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {jobs.map((job) => (
          <JobCard key={job._id} job={job} />
        ))}
      </div>
    </div>
  );
}
