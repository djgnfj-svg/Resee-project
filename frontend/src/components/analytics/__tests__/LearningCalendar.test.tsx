import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import LearningCalendar from '../LearningCalendar';
import { DailyReviewData } from '../../../types';

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  CalendarHeatmap: ({ data }: { data: any[] }) => (
    <div data-testid="calendar-heatmap" data-length={data?.length}>
      Calendar Heatmap
    </div>
  ),
}));

// Mock date-fns
jest.mock('date-fns', () => ({
  format: (date: Date, formatStr: string) => {
    if (formatStr === 'yyyy-MM-dd') {
      return date.toISOString().split('T')[0];
    }
    if (formatStr === 'yyyy년 MM월') {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      return `${year}년 ${month}월`;
    }
    return date.toLocaleDateString();
  },
  subDays: (date: Date, days: number) => {
    const result = new Date(date);
    result.setDate(result.getDate() - days);
    return result;
  },
  addDays: (date: Date, days: number) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  },
  startOfWeek: (date: Date) => {
    const result = new Date(date);
    const day = result.getDay();
    const diff = result.getDate() - day;
    result.setDate(diff);
    return result;
  },
  endOfWeek: (date: Date) => {
    const result = new Date(date);
    const day = result.getDay();
    const diff = result.getDate() + (6 - day);
    result.setDate(diff);
    return result;
  },
  eachDayOfInterval: (interval: { start: Date; end: Date }) => {
    const days = [];
    const current = new Date(interval.start);
    while (current <= interval.end) {
      days.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    return days;
  },
}));

describe('LearningCalendar Component', () => {
  const mockData: DailyReviewData[] = [
    {
      date: '2023-12-01',
      count: 5,
      success_rate: 80,
      remembered: 4,
      partial: 1,
      forgot: 0,
    },
    {
      date: '2023-12-02',
      count: 3,
      success_rate: 66.7,
      remembered: 2,
      partial: 1,
      forgot: 0,
    },
    {
      date: '2023-12-03',
      count: 8,
      success_rate: 75,
      remembered: 6,
      partial: 1,
      forgot: 1,
    },
    {
      date: '2023-12-04',
      count: 0,
      success_rate: 0,
      remembered: 0,
      partial: 0,
      forgot: 0,
    },
    {
      date: '2023-12-05',
      count: 12,
      success_rate: 91.7,
      remembered: 11,
      partial: 1,
      forgot: 0,
    },
  ];

  const defaultProps = {
    data: mockData,
    loading: false,
  };

  test('renders calendar component with data', () => {
    render(<LearningCalendar {...defaultProps} />);

    expect(screen.getByText('학습 캘린더')).toBeInTheDocument();
    expect(screen.getByTestId('calendar-heatmap')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  test('shows loading state', () => {
    render(<LearningCalendar {...defaultProps} loading={true} />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.queryByTestId('calendar-heatmap')).not.toBeInTheDocument();
  });

  test('displays month navigation', () => {
    render(<LearningCalendar {...defaultProps} />);

    expect(screen.getByRole('button', { name: /이전 달/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /다음 달/i })).toBeInTheDocument();
    expect(screen.getByText(/2023년 12월/)).toBeInTheDocument();
  });

  test('navigates to previous month', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    const prevButton = screen.getByRole('button', { name: /이전 달/i });
    await user.click(prevButton);

    // Should show previous month
    expect(screen.getByText(/2023년 11월/)).toBeInTheDocument();
  });

  test('navigates to next month', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    const nextButton = screen.getByRole('button', { name: /다음 달/i });
    await user.click(nextButton);

    // Should show next month
    expect(screen.getByText(/2024년 01월/)).toBeInTheDocument();
  });

  test('displays activity levels correctly', () => {
    render(<LearningCalendar {...defaultProps} />);

    // Should show legend
    expect(screen.getByText('활동 수준')).toBeInTheDocument();
    expect(screen.getByText('적음')).toBeInTheDocument();
    expect(screen.getByText('많음')).toBeInTheDocument();

    // Should show activity level indicators
    const activityLevels = screen.getAllByTestId(/activity-level-/);
    expect(activityLevels).toHaveLength(5); // 0, 1, 2, 3, 4 levels
  });

  test('shows today indicator', () => {
    const todayData = [
      ...mockData,
      {
        date: new Date().toISOString().split('T')[0],
        count: 3,
        success_rate: 100,
        remembered: 3,
        partial: 0,
        forgot: 0,
      },
    ];

    render(<LearningCalendar data={todayData} loading={false} />);

    expect(screen.getByTestId('today-indicator')).toBeInTheDocument();
  });

  test('handles empty data', () => {
    render(<LearningCalendar data={[]} loading={false} />);

    expect(screen.getByText('학습 캘린더')).toBeInTheDocument();
    expect(screen.getByText('아직 학습 데이터가 없습니다.')).toBeInTheDocument();
  });

  test('displays streak information', () => {
    render(<LearningCalendar {...defaultProps} />);

    expect(screen.getByText('현재 연속 학습')).toBeInTheDocument();
    expect(screen.getByText('최장 연속 학습')).toBeInTheDocument();
    
    // Should calculate and display streak days
    expect(screen.getByTestId('current-streak')).toBeInTheDocument();
    expect(screen.getByTestId('longest-streak')).toBeInTheDocument();
  });

  test('shows day details on hover', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    // Mock hovering over a day
    const calendarDay = screen.getByTestId('calendar-day-2023-12-01');
    await user.hover(calendarDay);

    await waitFor(() => {
      expect(screen.getByTestId('day-tooltip')).toBeInTheDocument();
      expect(screen.getByText('2023년 12월 1일')).toBeInTheDocument();
      expect(screen.getByText('복습 5개')).toBeInTheDocument();
      expect(screen.getByText('성공률 80%')).toBeInTheDocument();
    });
  });

  test('hides tooltip on mouse leave', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    const calendarDay = screen.getByTestId('calendar-day-2023-12-01');
    
    // Hover to show tooltip
    await user.hover(calendarDay);
    expect(screen.getByTestId('day-tooltip')).toBeInTheDocument();

    // Leave to hide tooltip
    await user.unhover(calendarDay);
    
    await waitFor(() => {
      expect(screen.queryByTestId('day-tooltip')).not.toBeInTheDocument();
    });
  });

  test('shows detailed view on day click', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    const calendarDay = screen.getByTestId('calendar-day-2023-12-01');
    await user.click(calendarDay);

    await waitFor(() => {
      expect(screen.getByTestId('day-detail-modal')).toBeInTheDocument();
      expect(screen.getByText('2023년 12월 1일 상세 정보')).toBeInTheDocument();
      expect(screen.getByText('총 복습: 5개')).toBeInTheDocument();
      expect(screen.getByText('기억함: 4개')).toBeInTheDocument();
      expect(screen.getByText('애매함: 1개')).toBeInTheDocument();
      expect(screen.getByText('모름: 0개')).toBeInTheDocument();
    });
  });

  test('closes detailed view modal', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    // Open modal
    const calendarDay = screen.getByTestId('calendar-day-2023-12-01');
    await user.click(calendarDay);

    expect(screen.getByTestId('day-detail-modal')).toBeInTheDocument();

    // Close modal
    const closeButton = screen.getByRole('button', { name: /닫기/i });
    await user.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByTestId('day-detail-modal')).not.toBeInTheDocument();
    });
  });

  test('calculates streak correctly', () => {
    const consecutiveData: DailyReviewData[] = [
      { date: '2023-12-01', count: 5, success_rate: 80, remembered: 4, partial: 1, forgot: 0 },
      { date: '2023-12-02', count: 3, success_rate: 67, remembered: 2, partial: 1, forgot: 0 },
      { date: '2023-12-03', count: 8, success_rate: 75, remembered: 6, partial: 1, forgot: 1 },
      { date: '2023-12-04', count: 0, success_rate: 0, remembered: 0, partial: 0, forgot: 0 }, // Break
      { date: '2023-12-05', count: 12, success_rate: 92, remembered: 11, partial: 1, forgot: 0 },
    ];

    render(<LearningCalendar data={consecutiveData} loading={false} />);

    // Should show correct streak calculations
    const currentStreak = screen.getByTestId('current-streak');
    const longestStreak = screen.getByTestId('longest-streak');

    expect(currentStreak).toBeInTheDocument();
    expect(longestStreak).toBeInTheDocument();
  });

  test('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    render(<LearningCalendar {...defaultProps} />);

    const prevButton = screen.getByRole('button', { name: /이전 달/i });
    const nextButton = screen.getByRole('button', { name: /다음 달/i });

    // Test keyboard navigation
    prevButton.focus();
    await user.keyboard('{Enter}');
    expect(screen.getByText(/2023년 11월/)).toBeInTheDocument();

    nextButton.focus();
    await user.keyboard('{Enter}');
    await user.keyboard('{Enter}');
    expect(screen.getByText(/2024년 01월/)).toBeInTheDocument();
  });

  test('maintains accessibility features', () => {
    render(<LearningCalendar {...defaultProps} />);

    // Calendar should have proper ARIA labels
    const calendar = screen.getByRole('grid');
    expect(calendar).toHaveAttribute('aria-label', '학습 캘린더');

    // Navigation buttons should be properly labeled
    const prevButton = screen.getByRole('button', { name: /이전 달/i });
    const nextButton = screen.getByRole('button', { name: /다음 달/i });

    expect(prevButton).toHaveAttribute('aria-label');
    expect(nextButton).toHaveAttribute('aria-label');

    // Calendar days should be accessible
    const calendarDays = screen.getAllByRole('gridcell');
    expect(calendarDays.length).toBeGreaterThan(0);

    calendarDays.forEach(day => {
      expect(day).toHaveAttribute('tabindex');
    });
  });

  test('responds to window resize', () => {
    render(<LearningCalendar {...defaultProps} />);

    // Simulate window resize
    fireEvent(window, new Event('resize'));

    // Calendar should still be rendered correctly
    expect(screen.getByTestId('calendar-heatmap')).toBeInTheDocument();
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
  });

  test('handles data prop changes', () => {
    const { rerender } = render(<LearningCalendar {...defaultProps} />);

    expect(screen.getByTestId('calendar-heatmap')).toHaveAttribute('data-length', '5');

    // Update with new data
    const newData = [...mockData, {
      date: '2023-12-06',
      count: 7,
      success_rate: 85,
      remembered: 6,
      partial: 1,
      forgot: 0,
    }];

    rerender(<LearningCalendar data={newData} loading={false} />);

    expect(screen.getByTestId('calendar-heatmap')).toHaveAttribute('data-length', '6');
  });
});