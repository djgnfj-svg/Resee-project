import React from 'react';
import { screen } from '@testing-library/react';
import { render, mockUser, mockContent } from '../test-utils/test-utils';
import SimpleDashboard from './SimpleDashboard';

// Mock the useAuth hook
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
  }),
}));

// Mock API hooks
jest.mock('../hooks/useContents', () => ({
  __esModule: true,
  default: () => ({
    data: {
      pages: [{
        results: [mockContent],
        count: 1,
      }],
    },
    isLoading: false,
    error: null,
    hasNextPage: false,
    fetchNextPage: jest.fn(),
  }),
}));

jest.mock('../hooks/useReviewSchedules', () => ({
  __esModule: true,
  default: () => ({
    data: {
      pages: [{
        results: [],
        count: 0,
      }],
    },
    isLoading: false,
    error: null,
  }),
}));

// Mock chart components
jest.mock('recharts', () => ({
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

describe('SimpleDashboard', () => {
  it('renders dashboard title', () => {
    render(<SimpleDashboard />);

    expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
  });

  it('renders welcome message with user name', () => {
    render(<SimpleDashboard />);

    expect(screen.getByText(/안녕하세요, Test님!/i)).toBeInTheDocument();
  });

  it('renders content stats', () => {
    render(<SimpleDashboard />);

    expect(screen.getByText(/전체 컨텐츠/i)).toBeInTheDocument();
    expect(screen.getByText(/오늘의 복습/i)).toBeInTheDocument();
    expect(screen.getByText(/학습 연속일수/i)).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    render(<SimpleDashboard />);

    expect(screen.getByText(/새 컨텐츠 작성/i)).toBeInTheDocument();
    expect(screen.getByText(/복습 시작/i)).toBeInTheDocument();
  });

  it('renders recent activity section', () => {
    render(<SimpleDashboard />);

    expect(screen.getByText(/최근 활동/i)).toBeInTheDocument();
  });
});