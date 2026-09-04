import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import JobForm from '../components/JobForm';

export default function PostJob() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleSubmit = async (payload) => {
    const { data } = await api.post('/jobs', payload);
    navigate(`/jobs/${data.job._id}`);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-4 text-2xl font-bold text-slate-900">Post a New Job</h1>
      <JobForm initialValues={{ company: user?.company || '' }} onSubmit={handleSubmit} />
    </div>
  );
}
