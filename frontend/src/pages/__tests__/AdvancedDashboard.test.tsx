import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import AdvancedDashboard from '../AdvancedDashboard';
import api from '../../utils/api';

// Mock the API
jest.mock('../../utils/api');

const mockApi = api as jest.Mocked<typeof api>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('AdvancedDashboard', () => {
  const mockAnalyticsData = {
    learning_insights: {
      total_content: 25,
      total_reviews: 150,
      recent_30d_reviews: 80,
      recent_7d_reviews: 20,
      recent_success_rate: 85.5,
      week_success_rate: 90.0,
      average_interval_days: 7.2,
      streak_days: 5,
    },
    category_performance: [
      {
        id: 1,
        name: 'Python',
        slug: 'python',
        content_count: 10,
        total_reviews: 60,
        success_rate: 88.3,
        recent_success_rate: 91.2,
        difficulty_level: 11.7,
        mastery_level: 'advanced',
      },
    ],
    study_patterns: {
      hourly_pattern: Array(24).fill(0).map((_, hour) => ({ hour, count: hour === 9 ? 15 : 0 })),
      daily_pattern: [
        { day: 'Mon', count: 10 },
        { day: 'Tue', count: 8 },
        { day: 'Wed', count: 12 },
        { day: 'Thu', count: 9 },
        { day: 'Fri', count: 11 },
        { day: 'Sat', count: 5 },
        { day: 'Sun', count: 3 },
      ],
      recommended_hour: 9,
      recommended_day: 'Wed',
      total_study_sessions: 58,
    },
    achievement_stats: {
      current_streak: 5,
      max_streak: 15,
      perfect_sessions: 12,
      mastered_categories: 2,
      monthly_progress: 65.5,
      monthly_target: 100,
      monthly_completed: 65,
    },
    performance_metrics: {
      currentStreak: 5,
      longestStreak: 15,
      totalReviews: 150,
      averageRetention: 85.5,
      studyEfficiency: 88.2,
      weeklyGoal: 30,
      weeklyProgress: 20,
    },
    recommendations: [],
  };

  const mockCalendarData = {
    calendar_data: Array(365).fill(0).map((_, index) => {
      const date = new Date();
      date.setDate(date.getDate() - (364 - index));
      return {
        date: date.toISOString().split('T')[0],
        count: index === 364 ? 5 : 0, // Today has 5 reviews
        success_rate: index === 364 ? 80 : 0,
        intensity: index === 364 ? 1 : 0,
        remembered: index === 364 ? 4 : 0,
        partial: index === 364 ? 1 : 0,
        forgot: 0,
      };
    }),
    monthly_summary: [],
    total_active_days: 1,
    best_day: { date: new Date().toISOString().split('T')[0], count: 5 },
  };

  beforeEach(() => {
    mockApi.get.mockImplementation((url) => {
      if (url === '/analytics/advanced/') {
        return Promise.resolve({ data: mockAnalyticsData });
      }
      if (url === '/analytics/calendar/') {
        return Promise.resolve({ data: mockCalendarData });
      }
      return Promise.reject(new Error('Not found'));
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<AdvancedDashboard />, { wrapper: createWrapper() });
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('renders analytics data after loading', async () => {
    render(<AdvancedDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('고급 학습 분석')).toBeInTheDocument();
    });

    // Check key metrics are displayed
    expect(screen.getByText('총 복습 수')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    
    expect(screen.getByText('현재 연속')).toBeInTheDocument();
    expect(screen.getByText('5일')).toBeInTheDocument();
  });

  it('displays weekly goal progress correctly', async () => {
    render(<AdvancedDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('주간 목표')).toBeInTheDocument();
    });

    // Check progress display
    expect(screen.getByText('20')).toBeInTheDocument(); // Current progress
    expect(screen.getByText('30회')).toBeInTheDocument(); // Goal
  });

  it('does not show goal exceeded message when under 100%', async () => {
    render(<AdvancedDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('주간 목표')).toBeInTheDocument();
    });

    // Should not show exceeded message (20/30 = 66.7%)
    expect(screen.queryByText('🎉 목표 초과!')).not.toBeInTheDocument();
  });

  it('shows goal exceeded message when over 100%', async () => {
    // Modify mock data for exceeded goal
    mockApi.get.mockImplementation((url) => {
      if (url === '/analytics/advanced/') {
        return Promise.resolve({
          data: {
            ...mockAnalyticsData,
            performance_metrics: {
              ...mockAnalyticsData.performance_metrics,
              weeklyProgress: 35, // Exceeds goal of 30
            },
          },
        });
      }
      if (url === '/analytics/calendar/') {
        return Promise.resolve({ data: mockCalendarData });
      }
      return Promise.reject(new Error('Not found'));
    });

    render(<AdvancedDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('🎉 목표 초과!')).toBeInTheDocument();
    });
  });

  it('displays learning calendar', async () => {
    render(<AdvancedDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('학습 캘린더')).toBeInTheDocument();
    });

    // Calendar should be rendered
    // Note: Detailed calendar testing would be in LearningCalendar.test.tsx
  });

  it('handles API errors gracefully', async () => {
    mockApi.get.mockRejectedValue(new Error('Network error'));

    render(<AdvancedDashboard />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/오류가 발생했습니다/)).toBeInTheDocument();
    });
  });
});