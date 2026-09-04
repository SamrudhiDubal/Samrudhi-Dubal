import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api/axios';
import JobForm from '../components/JobForm';

export default function EditJob() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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

  const handleSubmit = async (payload) => {
    await api.put(`/jobs/${id}`, payload);
    navigate(`/jobs/${id}`);
  };

  if (loading) return <p className="text-slate-500">Loading...</p>;
  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-4 text-2xl font-bold text-slate-900">Edit Job</h1>
      <JobForm initialValues={job} onSubmit={handleSubmit} submitLabel="Save Changes" />
    </div>
  );
}
