import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-3xl font-bold text-slate-900">404</h1>
      <p className="mt-2 text-slate-600">Page not found.</p>
      <Link to="/" className="mt-4 inline-block text-brand-600 hover:underline">
        Go home
      </Link>
    </div>
  );
}
