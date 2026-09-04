import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="py-12 text-center">
      <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">
        Find your next role with <span className="text-brand-600">AI-powered</span> matching
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
        JobMatch AI screens resumes automatically, scoring every applicant against the job's
        required skills and description so employers can focus on the best-fit candidates first.
      </p>
      <div className="mt-8 flex justify-center gap-4">
        <Link
          to="/jobs"
          className="rounded-md bg-brand-600 px-5 py-2.5 font-medium text-white hover:bg-brand-700"
        >
          Browse Jobs
        </Link>
        {!user && (
          <Link
            to="/register"
            className="rounded-md border border-slate-300 bg-white px-5 py-2.5 font-medium text-slate-700 hover:bg-slate-50"
          >
            Get Started
          </Link>
        )}
      </div>

      <div className="mx-auto mt-16 grid max-w-4xl gap-6 text-left sm:grid-cols-3">
        <Feature
          title="Smart Screening"
          text="Every resume is parsed and scored against a job's required skills and description in real time."
        />
        <Feature
          title="Ranked Applicants"
          text="Employers instantly see candidates ranked by AI match score, with matched and missing skills highlighted."
        />
        <Feature
          title="Simple for Everyone"
          text="Candidates apply in one click; employers post jobs and manage a pipeline with statuses."
        />
      </div>
    </div>
  );
}

function Feature({ title, text }) {
  return (
    <div className="rounded-lg border bg-white p-5">
      <h3 className="font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 text-sm text-slate-600">{text}</p>
    </div>
  );
}
