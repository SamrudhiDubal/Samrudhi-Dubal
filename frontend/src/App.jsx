import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import PrivateRoute from './components/PrivateRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Jobs from './pages/Jobs';
import JobDetails from './pages/JobDetails';
import PostJob from './pages/PostJob';
import EditJob from './pages/EditJob';
import EmployerJobs from './pages/EmployerJobs';
import Applicants from './pages/Applicants';
import CandidateApplications from './pages/CandidateApplications';
import RecommendedJobs from './pages/RecommendedJobs';
import Profile from './pages/Profile';
import AdminDashboard from './pages/AdminDashboard';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/jobs/:id" element={<JobDetails />} />
          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Profile />
              </PrivateRoute>
            }
          />
          <Route
            path="/candidate/applications"
            element={
              <PrivateRoute role="candidate">
                <CandidateApplications />
              </PrivateRoute>
            }
          />
          <Route
            path="/candidate/recommended"
            element={
              <PrivateRoute role="candidate">
                <RecommendedJobs />
              </PrivateRoute>
            }
          />
          <Route
            path="/employer/post-job"
            element={
              <PrivateRoute role="employer">
                <PostJob />
              </PrivateRoute>
            }
          />
          <Route
            path="/employer/jobs"
            element={
              <PrivateRoute role="employer">
                <EmployerJobs />
              </PrivateRoute>
            }
          />
          <Route
            path="/employer/jobs/:id/edit"
            element={
              <PrivateRoute role="employer">
                <EditJob />
              </PrivateRoute>
            }
          />
          <Route
            path="/employer/jobs/:id/applicants"
            element={
              <PrivateRoute role="employer">
                <Applicants />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <PrivateRoute role="admin">
                <AdminDashboard />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}
