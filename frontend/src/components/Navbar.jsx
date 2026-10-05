import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="border-b bg-white">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold text-brand-600">
          JobMatch <span className="text-slate-800">AI</span>
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link to="/jobs" className="text-slate-600 hover:text-brand-600">
            Browse Jobs
          </Link>
          {user?.role === 'employer' && (
            <>
              <Link to="/employer/jobs" className="text-slate-600 hover:text-brand-600">
                My Postings
              </Link>
              <Link to="/employer/post-job" className="text-slate-600 hover:text-brand-600">
                Post a Job
              </Link>
            </>
          )}
          {user?.role === 'candidate' && (
            <Link to="/candidate/applications" className="text-slate-600 hover:text-brand-600">
              My Applications
            </Link>
          )}
          {user?.role === 'admin' && (
            <Link to="/admin" className="text-slate-600 hover:text-brand-600">
              Admin
            </Link>
          )}
          {user ? (
            <>
              <Link to="/profile" className="text-slate-600 hover:text-brand-600">
                {user.name}
              </Link>
              <button
                onClick={handleLogout}
                className="rounded-md bg-slate-100 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-200"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-slate-600 hover:text-brand-600">
                Login
              </Link>
              <Link
                to="/register"
                className="rounded-md bg-brand-600 px-3 py-1.5 font-medium text-white hover:bg-brand-700"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
