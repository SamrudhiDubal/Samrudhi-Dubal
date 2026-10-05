import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import PrivateRoute from '../../components/PrivateRoute';
import { useAuth } from '../../context/AuthContext';

vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

function renderAt(initialPath) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route
          path="/protected"
          element={
            <PrivateRoute role="employer">
              <div>Secret employer content</div>
            </PrivateRoute>
          }
        />
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/" element={<div>Home page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('PrivateRoute', () => {
  it('shows a loading state while auth is resolving', () => {
    useAuth.mockReturnValue({ user: null, loading: true });
    renderAt('/protected');
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('redirects to /login when there is no user', () => {
    useAuth.mockReturnValue({ user: null, loading: false });
    renderAt('/protected');
    expect(screen.getByText('Login page')).toBeInTheDocument();
  });

  it('redirects to / when the user has the wrong role', () => {
    useAuth.mockReturnValue({ user: { role: 'candidate' }, loading: false });
    renderAt('/protected');
    expect(screen.getByText('Home page')).toBeInTheDocument();
  });

  it('renders the protected content when the role matches', () => {
    useAuth.mockReturnValue({ user: { role: 'employer' }, loading: false });
    renderAt('/protected');
    expect(screen.getByText('Secret employer content')).toBeInTheDocument();
  });
});
