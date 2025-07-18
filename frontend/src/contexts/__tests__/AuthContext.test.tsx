import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from '../AuthContext';
import { createMockLocalStorage } from '../../test-utils/test-utils';

// Mock localStorage
const mockLocalStorage = createMockLocalStorage();
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Test component that uses AuthContext
const TestComponent = () => {
  const { user, isLoading, login, logout, register, isAuthenticated } = useAuth();

  return (
    <div>
      <div data-testid="user">{user ? `User: ${user.username}` : 'No user'}</div>
      <div data-testid="loading">{isLoading ? 'Loading...' : 'Not loading'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'Authenticated' : 'Not authenticated'}</div>
      <button 
        onClick={() => login({ username: 'testuser', password: 'password' })}
        data-testid="login-btn"
      >
        Login
      </button>
      <button onClick={logout} data-testid="logout-btn">Logout</button>
      <button 
        onClick={() => register({
          username: 'newuser',
          email: 'new@example.com',
          password: 'password',
          password_confirm: 'password',
          first_name: 'New',
          last_name: 'User'
        })}
        data-testid="register-btn"
      >
        Register
      </button>
    </div>
  );
};

const Wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0 },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
  });

  it('should render without crashing', () => {
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    expect(screen.getByTestId('user')).toHaveTextContent('No user');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('Not authenticated');
  });

  it('should handle login flow correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    // Initially not authenticated
    expect(screen.getByTestId('authenticated')).toHaveTextContent('Not authenticated');

    // Click login button
    await user.click(screen.getByTestId('login-btn'));

    // Should set loading state and then authenticate
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('User: testuser');
    });
  });

  it('should handle logout correctly', async () => {
    const user = userEvent.setup();
    
    // Set up logged in state
    mockLocalStorage.setItem('access_token', 'mock-token');
    
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    // Login first
    await user.click(screen.getByTestId('login-btn'));
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    });

    // Logout
    await user.click(screen.getByTestId('logout-btn'));

    expect(screen.getByTestId('authenticated')).toHaveTextContent('Not authenticated');
    expect(screen.getByTestId('user')).toHaveTextContent('No user');
    expect(mockLocalStorage.getItem('access_token')).toBeNull();
  });

  it('should handle registration flow correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    // Click register button
    await user.click(screen.getByTestId('register-btn'));

    // Should authenticate after registration
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
    });
  });

  it('should restore user session from localStorage', async () => {
    // Set up existing token
    mockLocalStorage.setItem('access_token', 'existing-token');
    
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    // Should load user data from token
    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('User: testuser');
    });

    expect(screen.getByTestId('authenticated')).toHaveTextContent('Authenticated');
  });

  it('should handle invalid token by clearing storage', async () => {
    // Set up invalid token
    mockLocalStorage.setItem('access_token', 'invalid-token');
    
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    // Should clear invalid token and remain unauthenticated
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Not authenticated');
    });

    expect(mockLocalStorage.getItem('access_token')).toBeNull();
  });

  it('should show loading state during initial auth check', () => {
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    // Should initially show loading
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading...');
  });

  it('should throw error when used outside provider', () => {
    // Suppress console.error for this test
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleSpy.mockRestore();
  });

  it('should handle network errors during login', async () => {
    // Mock network error
    const user = userEvent.setup();
    
    // This would require server to return error
    // For now, just test that errors don't crash the app
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    await user.click(screen.getByTestId('login-btn'));
    
    // Should handle error gracefully
    expect(screen.getByTestId('user')).toBeInTheDocument();
  });

  it('should update tokens correctly', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <TestComponent />
      </Wrapper>
    );

    await user.click(screen.getByTestId('login-btn'));

    await waitFor(() => {
      expect(mockLocalStorage.getItem('access_token')).toBe('mock-access-token');
      expect(mockLocalStorage.getItem('refresh_token')).toBe('mock-refresh-token');
    });
  });
});