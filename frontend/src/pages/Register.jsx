import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'candidate',
    company: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const payload = { ...form };
      if (payload.role !== 'employer') delete payload.company;
      const user = await register(payload);
      navigate(user.role === 'employer' ? '/employer/jobs' : '/jobs', { replace: true });
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md rounded-lg border bg-white p-6 shadow-sm">
      <h1 className="text-xl font-bold text-slate-900">Create your account</h1>
      {error && <p className="mt-3 rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}
      <form onSubmit={handleSubmit} className="mt-4 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700">I am a...</label>
          <div className="mt-1 grid grid-cols-2 gap-2">
            {['candidate', 'employer'].map((r) => (
              <button
                type="button"
                key={r}
                onClick={() => setForm({ ...form, role: r })}
                className={`rounded-md border px-3 py-2 text-sm font-medium capitalize ${
                  form.role === r
                    ? 'border-brand-600 bg-brand-50 text-brand-700'
                    : 'border-slate-300 text-slate-600'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Full name</label>
          <input
            required
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        {form.role === 'employer' && (
          <div>
            <label className="text-sm font-medium text-slate-700">Company</label>
            <input
              required
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              value={form.company}
              onChange={(e) => setForm({ ...form, company: e.target.value })}
            />
          </div>
        )}
        <div>
          <label className="text-sm font-medium text-slate-700">Email</label>
          <input
            type="email"
            required
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Password</label>
          <input
            type="password"
            required
            minLength={6}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-brand-600 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? 'Creating account...' : 'Sign up'}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-brand-600 hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
