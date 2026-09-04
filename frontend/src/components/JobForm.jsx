import { useState } from 'react';

const emptyJob = {
  title: '',
  company: '',
  location: '',
  description: '',
  jobType: 'full-time',
  experienceLevel: 'entry',
  salaryMin: '',
  salaryMax: '',
  skillsRequired: '',
};

export default function JobForm({ initialValues, onSubmit, submitLabel = 'Post Job' }) {
  const [form, setForm] = useState({
    ...emptyJob,
    ...initialValues,
    skillsRequired: Array.isArray(initialValues?.skillsRequired)
      ? initialValues.skillsRequired.join(', ')
      : initialValues?.skillsRequired || '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        salaryMin: form.salaryMin ? Number(form.salaryMin) : undefined,
        salaryMax: form.salaryMax ? Number(form.salaryMax) : undefined,
        skillsRequired: form.skillsRequired
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      };
      await onSubmit(payload);
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border bg-white p-6 shadow-sm">
      {error && <p className="rounded bg-rose-50 p-2 text-sm text-rose-700">{error}</p>}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Job Title" required value={form.title} onChange={handleChange('title')} />
        <Field label="Company" required value={form.company} onChange={handleChange('company')} />
        <Field label="Location" value={form.location} onChange={handleChange('location')} />
        <div>
          <label className="text-sm font-medium text-slate-700">Job Type</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.jobType}
            onChange={handleChange('jobType')}
          >
            <option value="full-time">Full-time</option>
            <option value="part-time">Part-time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700">Experience Level</label>
          <select
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.experienceLevel}
            onChange={handleChange('experienceLevel')}
          >
            <option value="entry">Entry</option>
            <option value="mid">Mid</option>
            <option value="senior">Senior</option>
            <option value="lead">Lead</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Field
            label="Salary Min"
            type="number"
            value={form.salaryMin}
            onChange={handleChange('salaryMin')}
          />
          <Field
            label="Salary Max"
            type="number"
            value={form.salaryMax}
            onChange={handleChange('salaryMax')}
          />
        </div>
      </div>

      <div>
        <label className="text-sm font-medium text-slate-700">Description</label>
        <textarea
          required
          rows={6}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          value={form.description}
          onChange={handleChange('description')}
        />
      </div>

      <div>
        <label className="text-sm font-medium text-slate-700">
          Required Skills (comma separated)
        </label>
        <input
          placeholder="e.g. react, node.js, mongodb"
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          value={form.skillsRequired}
          onChange={handleChange('skillsRequired')}
        />
        <p className="mt-1 text-xs text-slate-500">
          Used by the AI matching engine to score every applicant's resume.
        </p>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-brand-600 px-5 py-2 font-medium text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {submitting ? 'Saving...' : submitLabel}
      </button>
    </form>
  );
}

function Field({ label, ...props }) {
  return (
    <div>
      <label className="text-sm font-medium text-slate-700">{label}</label>
      <input
        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
        {...props}
      />
    </div>
  );
}
