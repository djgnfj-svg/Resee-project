import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { mockUser, createTestQueryClient } from '../test-utils/test-utils';
import DashboardPage from './DashboardPage';
import { QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { reviewAPI, contentAPI } from '../utils/api';

// Mock the useAuth hook
jest.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
  }),
}));

// Mock the API modules directly
jest.mock('../utils/api/review', () => ({
  reviewAPI: {
    getDashboard: jest.fn(),
  },
}));

jest.mock('../utils/api/content', () => ({
  contentAPI: {
    getContents: jest.fn(),
    getCategories: jest.fn(),
  },
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    // Setup mock implementations before each test
    (reviewAPI.getDashboard as jest.Mock).mockResolvedValue({
      today_reviews: 2,
      total_content: 5,
      success_rate: 85.7,
      total_reviews_30_days: 28,
      recent_reviews: [],
    });

    (contentAPI.getContents as jest.Mock).mockResolvedValue({
      results: [],
      usage: {
        used: 5,
        limit: 100,
      },
      count: 0,
      next: null,
      previous: null,
    });

    (contentAPI.getCategories as jest.Mock).mockResolvedValue({
      results: [],
      usage: {
        used: 0,
        limit: 3,
      },
      count: 0,
      next: null,
      previous: null,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  // Custom render with providers
  const renderWithProviders = (ui: React.ReactElement) => {
    const queryClient = createTestQueryClient();
    return {
      ...screen,
      ...(function() {
        const { render: rtlRender } = require('@testing-library/react');
        return rtlRender(
          <QueryClientProvider client={queryClient}>
            <MemoryRouter>
              {ui}
            </MemoryRouter>
          </QueryClientProvider>
        );
      })(),
    };
  };

  it('renders dashboard title', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('renders welcome message', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      // Component shows time-based greeting like "좋은 아침이에요", "좋은 오후에요", etc.
      expect(screen.getByText(/좋은/i)).toBeInTheDocument();
    });
  });

  it('renders content stats', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/학습 콘텐츠/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/오늘의 복습/i)).toBeInTheDocument();
  });

  it('renders action buttons', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/새 콘텐츠 추가하기/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/복습 시작/i)).toBeInTheDocument();
  });

  it('renders statistics section', async () => {
    renderWithProviders(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/평균 복습 성공률/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/최근 30일 복습 횟수/i)).toBeInTheDocument();
  });
});