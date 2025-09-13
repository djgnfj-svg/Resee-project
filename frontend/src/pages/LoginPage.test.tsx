import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { render } from '../test-utils/test-utils';
import LoginPage from './LoginPage';

// Mock the useAuth hook
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    login: jest.fn(),
    isLoading: false,
    error: null,
  }),
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

describe('LoginPage', () => {
  it('renders login form', () => {
    render(<LoginPage />);

    expect(screen.getByLabelText(/이메일/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/비밀번호/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /로그인/i })).toBeInTheDocument();
  });

  it('shows validation errors for empty form', async () => {
    render(<LoginPage />);

    const submitButton = screen.getByRole('button', { name: /로그인/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/이메일을 입력해주세요/i)).toBeInTheDocument();
      expect(screen.getByText(/비밀번호를 입력해주세요/i)).toBeInTheDocument();
    });
  });

  it('allows user to input email and password', () => {
    render(<LoginPage />);

    const emailInput = screen.getByLabelText(/이메일/i);
    const passwordInput = screen.getByLabelText(/비밀번호/i);

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('shows Google login button', () => {
    render(<LoginPage />);

    expect(screen.getByText(/Google로 계속하기/i)).toBeInTheDocument();
  });

  it('shows register link', () => {
    render(<LoginPage />);

    expect(screen.getByText(/회원가입/i)).toBeInTheDocument();
  });
});