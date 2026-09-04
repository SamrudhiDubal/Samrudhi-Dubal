import { Link } from 'react-router-dom';

export default function JobCard({ job }) {
  return (
    <Link
      to={`/jobs/${job._id}`}
      className="block rounded-lg border bg-white p-4 shadow-sm transition hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-slate-900">{job.title}</h3>
          <p className="text-sm text-slate-600">{job.company}</p>
        </div>
        <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-medium capitalize text-brand-700">
          {job.jobType?.replace('-', ' ')}
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-500">{job.location}</p>
      {job.skillsRequired?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {job.skillsRequired.slice(0, 6).map((skill) => (
            <span key={skill} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {skill}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
