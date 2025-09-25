import React from 'react';
import { screen } from '@testing-library/react';
import { render, mockUser } from '../test-utils/test-utils';
import DashboardPage from './DashboardPage';

// Mock the useAuth hook
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
  }),
}));

// Mock React Query
jest.mock('@tanstack/react-query', () => ({
  ...jest.requireActual('@tanstack/react-query'),
  useQuery: jest.fn(() => ({
    data: {
      today_reviews: 2,
      total_content: 5,
      success_rate: 85.7,
      total_reviews_30_days: 28
    },
    isLoading: false,
    error: null,
  })),
}));


// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

describe('DashboardPage', () => {
  it('renders dashboard title', () => {
    render(<DashboardPage />);

    expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
  });

  it('renders welcome message', () => {
    render(<DashboardPage />);

    expect(screen.getByText(/안녕하세요/i)).toBeInTheDocument();
  });

  it('renders content stats', () => {
    render(<DashboardPage />);

    expect(screen.getByText(/전체 컨텐츠/i)).toBeInTheDocument();
    expect(screen.getByText(/오늘의 복습/i)).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    render(<DashboardPage />);

    expect(screen.getByText(/새 컨텐츠 작성/i)).toBeInTheDocument();
    expect(screen.getByText(/복습 시작/i)).toBeInTheDocument();
  });

  it('renders recent activity section', () => {
    render(<DashboardPage />);

    expect(screen.getByText(/최근 활동/i)).toBeInTheDocument();
  });
});