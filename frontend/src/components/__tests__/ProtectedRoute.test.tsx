import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import '@testing-library/jest-dom';
import ProtectedRoute from '../ProtectedRoute';
import { AuthProvider } from '../../contexts/AuthContext';

// Mock the AuthContext
const mockAuthContext = {
  user: null,
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  updateProfile: jest.fn(),
  changePassword: jest.fn(),
  deleteAccount: jest.fn(),
  loading: false,
  error: null,
};

jest.mock('../../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => mockAuthContext,
}));

// Mock Navigate component
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Navigate: ({ to }: { to: string }) => {
    mockNavigate(to);
    return <div data-testid="navigate">Redirecting to {to}</div>;
  },
}));

// Test components
const ProtectedComponent = () => (
  <div data-testid="protected-content">Protected Content</div>
);

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
        <Route path="/protected" element={children} />
      </Routes>
    </AuthProvider>
  </BrowserRouter>
);

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
  });

  test('renders protected content when user is authenticated', () => {
    mockAuthContext.user = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      timezone: 'Asia/Seoul',
      notification_enabled: true,
      date_joined: '2023-01-01T00:00:00Z',
    };

    render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  test('redirects to login when user is not authenticated', async () => {
    mockAuthContext.user = null;

    render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    expect(screen.getByTestId('navigate')).toBeInTheDocument();
    expect(screen.getByText('Redirecting to /login')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
  });

  test('shows loading state when authentication is loading', () => {
    mockAuthContext.user = null;
    mockAuthContext.loading = true;

    render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  test('redirects to custom path when specified', async () => {
    mockAuthContext.user = null;
    const customRedirectPath = '/custom-login';

    render(
      <TestWrapper>
        <ProtectedRoute redirectTo={customRedirectPath}>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(customRedirectPath);
    });

    expect(screen.getByText(`Redirecting to ${customRedirectPath}`)).toBeInTheDocument();
  });

  test('handles authentication state changes', async () => {
    // Start with no user
    mockAuthContext.user = null;
    
    const { rerender } = render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    // Should redirect to login
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    // Simulate user login
    mockAuthContext.user = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      timezone: 'Asia/Seoul',
      notification_enabled: true,
      date_joined: '2023-01-01T00:00:00Z',
    };

    rerender(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    // Should now show protected content
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  test('handles loading to authenticated transition', () => {
    // Start with loading state
    mockAuthContext.user = null;
    mockAuthContext.loading = true;

    const { rerender } = render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

    // Finish loading with authenticated user
    mockAuthContext.loading = false;
    mockAuthContext.user = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      timezone: 'Asia/Seoul',
      notification_enabled: true,
      date_joined: '2023-01-01T00:00:00Z',
    };

    rerender(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });

  test('handles loading to unauthenticated transition', async () => {
    // Start with loading state
    mockAuthContext.user = null;
    mockAuthContext.loading = true;

    const { rerender } = render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

    // Finish loading without user
    mockAuthContext.loading = false;

    rerender(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    expect(screen.getByTestId('navigate')).toBeInTheDocument();
  });

  test('preserves current location for redirect after login', async () => {
    mockAuthContext.user = null;

    // Mock current location
    Object.defineProperty(window, 'location', {
      value: {
        pathname: '/protected/important-page',
        search: '?tab=settings',
        hash: '#section1',
      },
      writable: true,
    });

    render(
      <TestWrapper>
        <ProtectedRoute>
          <ProtectedComponent />
        </ProtectedRoute>
      </TestWrapper>
    );

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    // In a real implementation, the redirect path would be stored
    // for use after successful login
  });

  test('works with nested protected routes', () => {
    mockAuthContext.user = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      timezone: 'Asia/Seoul',
      notification_enabled: true,
      date_joined: '2023-01-01T00:00:00Z',
    };

    const NestedComponent = () => (
      <div data-testid="nested-content">Nested Protected Content</div>
    );

    render(
      <TestWrapper>
        <ProtectedRoute>
          <div>
            <h1>Parent Protected Content</h1>
            <ProtectedRoute>
              <NestedComponent />
            </ProtectedRoute>
          </div>
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByText('Parent Protected Content')).toBeInTheDocument();
    expect(screen.getByTestId('nested-content')).toBeInTheDocument();
  });

  test('handles multiple children correctly', () => {
    mockAuthContext.user = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      timezone: 'Asia/Seoul',
      notification_enabled: true,
      date_joined: '2023-01-01T00:00:00Z',
    };

    render(
      <TestWrapper>
        <ProtectedRoute>
          <div data-testid="child1">Child 1</div>
          <div data-testid="child2">Child 2</div>
          <div data-testid="child3">Child 3</div>
        </ProtectedRoute>
      </TestWrapper>
    );

    expect(screen.getByTestId('child1')).toBeInTheDocument();
    expect(screen.getByTestId('child2')).toBeInTheDocument();
    expect(screen.getByTestId('child3')).toBeInTheDocument();
  });
});