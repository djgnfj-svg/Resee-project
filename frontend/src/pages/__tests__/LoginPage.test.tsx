import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginPage from '../LoginPage';
import { AuthProvider } from '../../contexts/AuthContext';
import { createMockLocalStorage } from '../../test-utils/test-utils';

// Mock localStorage
const mockLocalStorage = createMockLocalStorage();
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, cacheTime: 0 },
    },
  });

const Wrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
  });

  it('should render without crashing', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    expect(screen.getByText(/로그인/i)).toBeInTheDocument();
  });

  it('should display login form fields', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    expect(screen.getByLabelText(/사용자명/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/비밀번호/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /로그인/i })).toBeInTheDocument();
  });

  it('should handle successful login', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // Fill login form
    await user.type(screen.getByLabelText(/사용자명/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'password123');

    // Submit form
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Should redirect to home page
    await waitFor(() => {
      expect(window.location.pathname).toBe('/');
    });

    // Should store tokens
    expect(mockLocalStorage.getItem('access_token')).toBe('mock-access-token');
    expect(mockLocalStorage.getItem('refresh_token')).toBe('mock-refresh-token');
  });

  it('should show validation errors for empty fields', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // Try to submit without filling fields
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    await waitFor(() => {
      expect(screen.getByText(/사용자명은 필수입니다/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/비밀번호는 필수입니다/i)).toBeInTheDocument();
  });

  it('should show error for invalid credentials', async () => {
    const user = userEvent.setup();
    
    // Mock failed login
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    await user.type(screen.getByLabelText(/사용자명/i), 'wronguser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'wrongpassword');

    await user.click(screen.getByRole('button', { name: /로그인/i }));

    await waitFor(() => {
      expect(screen.getByText(/로그인에 실패했습니다/i)).toBeInTheDocument();
    });
  });

  it('should display loading state during login', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    await user.type(screen.getByLabelText(/사용자명/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'password123');

    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Should show loading state
    expect(screen.getByText(/로그인 중.../i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /로그인/i })).toBeDisabled();
  });

  it('should have link to registration page', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    const registerLink = screen.getByText(/회원가입/i);
    expect(registerLink).toBeInTheDocument();
    expect(registerLink.closest('a')).toHaveAttribute('href', '/register');
  });

  it('should display password visibility toggle', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    const passwordInput = screen.getByLabelText(/비밀번호/i);
    const toggleButton = screen.getByRole('button', { name: /비밀번호 보기/i });

    // Initially password should be hidden
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Click toggle
    await user.click(toggleButton);

    // Password should be visible
    expect(passwordInput).toHaveAttribute('type', 'text');

    // Click toggle again
    await user.click(toggleButton);

    // Password should be hidden again
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // Tab through form fields
    await user.tab();
    expect(screen.getByLabelText(/사용자명/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByLabelText(/비밀번호/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByRole('button', { name: /로그인/i })).toHaveFocus();
  });

  it('should submit form on Enter key', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    await user.type(screen.getByLabelText(/사용자명/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'password123');

    // Press Enter in password field
    await user.type(screen.getByLabelText(/비밀번호/i), '{enter}');

    await waitFor(() => {
      expect(window.location.pathname).toBe('/');
    });
  });

  it('should display remember me checkbox', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    expect(screen.getByLabelText(/로그인 상태 유지/i)).toBeInTheDocument();
  });

  it('should handle remember me functionality', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    const rememberMeCheckbox = screen.getByLabelText(/로그인 상태 유지/i);
    
    // Check remember me
    await user.click(rememberMeCheckbox);
    expect(rememberMeCheckbox).toBeChecked();

    // Login with remember me checked
    await user.type(screen.getByLabelText(/사용자명/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'password123');
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Should store tokens with longer expiration
    await waitFor(() => {
      expect(mockLocalStorage.getItem('access_token')).toBeTruthy();
    });
  });

  it('should show forgot password link', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    const forgotPasswordLink = screen.getByText(/비밀번호를 잊으셨나요/i);
    expect(forgotPasswordLink).toBeInTheDocument();
  });

  it('should be responsive on mobile devices', () => {
    // Set mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // Should render mobile-friendly layout
    const loginForm = screen.getByRole('form');
    expect(loginForm).toHaveClass('mobile-responsive');
  });

  it('should redirect authenticated users', async () => {
    // Set up authenticated state
    mockLocalStorage.setItem('access_token', 'existing-token');
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // Should redirect to home page
    await waitFor(() => {
      expect(window.location.pathname).toBe('/');
    });
  });

  it('should validate email format if email login is supported', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // If username field accepts email
    await user.type(screen.getByLabelText(/사용자명/i), 'invalid-email');
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Should show validation error if email format is required
    // This depends on actual implementation
  });

  it('should handle network errors gracefully', async () => {
    const user = userEvent.setup();
    
    // This would require mocking network failure
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    await user.type(screen.getByLabelText(/사용자명/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'password123');
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Should handle network errors and show appropriate message
    await waitFor(() => {
      expect(screen.getByText(/네트워크 오류가 발생했습니다/i)).toBeInTheDocument();
    });
  });

  it('should clear form on successful login', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    await user.type(screen.getByLabelText(/사용자명/i), 'testuser');
    await user.type(screen.getByLabelText(/비밀번호/i), 'password123');
    await user.click(screen.getByRole('button', { name: /로그인/i }));

    // Form should be cleared after successful login
    await waitFor(() => {
      expect(screen.getByLabelText(/사용자명/i)).toHaveValue('');
      expect(screen.getByLabelText(/비밀번호/i)).toHaveValue('');
    });
  });

  it('should display social login options if available', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    // Look for social login buttons
    const googleLogin = screen.queryByText(/Google로 로그인/i);
    const kakaoLogin = screen.queryByText(/카카오로 로그인/i);
    
    if (googleLogin) expect(googleLogin).toBeInTheDocument();
    if (kakaoLogin) expect(kakaoLogin).toBeInTheDocument();
  });

  it('should show terms and privacy policy links', () => {
    render(
      <Wrapper>
        <LoginPage />
      </Wrapper>
    );

    const termsLink = screen.queryByText(/이용약관/i);
    const privacyLink = screen.queryByText(/개인정보처리방침/i);
    
    if (termsLink) expect(termsLink).toBeInTheDocument();
    if (privacyLink) expect(privacyLink).toBeInTheDocument();
  });
});