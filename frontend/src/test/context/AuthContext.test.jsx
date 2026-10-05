import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from '../../context/AuthContext';
import api from '../../api/axios';

vi.mock('../../api/axios', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}));

function TestConsumer() {
  const { user, loading, login, logout } = useAuth();
  if (loading) return <div>Loading...</div>;
  return (
    <div>
      <div data-testid="user">{user ? user.name : 'anonymous'}</div>
      <button onClick={() => login('jane@candidate.test', 'password123')}>Log in</button>
      <button onClick={logout}>Log out</button>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('starts with no user when there is no stored token', async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('anonymous'));
    expect(api.get).not.toHaveBeenCalled();
  });

  it('loads the current user when a token is already stored', async () => {
    localStorage.setItem('token', 'existing-token');
    api.get.mockResolvedValue({ data: { user: { name: 'Jane Candidate' } } });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Jane Candidate'));
    expect(api.get).toHaveBeenCalledWith('/auth/me');
  });

  it('clears the stored token when it is rejected by the server', async () => {
    localStorage.setItem('token', 'bad-token');
    api.get.mockRejectedValue(new Error('unauthorized'));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('anonymous'));
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('logs in, stores the token, and sets the user', async () => {
    api.post.mockResolvedValue({
      data: { token: 'new-token', user: { name: 'Jane Candidate' } },
    });
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('anonymous'));

    await user.click(screen.getByText('Log in'));

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Jane Candidate'));
    expect(localStorage.getItem('token')).toBe('new-token');
  });

  it('logs out and clears the token', async () => {
    localStorage.setItem('token', 'existing-token');
    api.get.mockResolvedValue({ data: { user: { name: 'Jane Candidate' } } });
    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Jane Candidate'));

    await act(async () => {
      await user.click(screen.getByText('Log out'));
    });

    expect(screen.getByTestId('user')).toHaveTextContent('anonymous');
    expect(localStorage.getItem('token')).toBeNull();
  });
});
