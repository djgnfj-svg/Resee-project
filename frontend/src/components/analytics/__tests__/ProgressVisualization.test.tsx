import React from 'react';
import { render, screen } from '@testing-library/react';
import ProgressVisualization from '../ProgressVisualization';

describe('ProgressVisualization', () => {
  const mockData = {
    weeklyProgress: [
      { day: 'Mon', count: 5, success_rate: 80 },
      { day: 'Tue', count: 3, success_rate: 100 },
      { day: 'Wed', count: 7, success_rate: 71 },
      { day: 'Thu', count: 4, success_rate: 75 },
      { day: 'Fri', count: 6, success_rate: 83 },
      { day: 'Sat', count: 8, success_rate: 88 },
      { day: 'Sun', count: 2, success_rate: 50 },
    ],
    monthlyTrends: [
      { month: 'Jan', total_reviews: 120, success_rate: 75 },
      { month: 'Feb', total_reviews: 150, success_rate: 82 },
      { month: 'Mar', total_reviews: 180, success_rate: 85 },
    ],
    categoryDistribution: [
      { name: 'Python', value: 45, masteryLevel: 85 },
      { name: 'JavaScript', value: 30, masteryLevel: 72 },
      { name: 'Math', value: 25, masteryLevel: 90 },
    ],
    performanceMetrics: {
      currentStreak: 7,
      longestStreak: 15,
      totalReviews: 450,
      averageRetention: 82.5,
      studyEfficiency: 78.3,
      weeklyGoal: 30,
      weeklyProgress: 35,
    },
  };

  it('renders performance metrics correctly', () => {
    render(<ProgressVisualization data={mockData} />);
    
    // Check if key metrics are displayed
    expect(screen.getByText('7')).toBeInTheDocument(); // Current streak
    expect(screen.getByText('450')).toBeInTheDocument(); // Total reviews
    expect(screen.getByText('82.5%')).toBeInTheDocument(); // Average retention
  });

  it('shows weekly goal with current progress', () => {
    render(<ProgressVisualization data={mockData} />);
    
    // Check weekly goal display
    expect(screen.getByText('주간 목표')).toBeInTheDocument();
    expect(screen.getByText('35')).toBeInTheDocument(); // Current progress
    expect(screen.getByText('30')).toBeInTheDocument(); // Goal
  });

  it('displays goal exceeded indicator when progress > 100%', () => {
    render(<ProgressVisualization data={mockData} />);
    
    // Should show exceeded message
    expect(screen.getByText('🎉 목표 초과!')).toBeInTheDocument();
  });

  it('handles empty data gracefully', () => {
    const emptyData = {
      weeklyProgress: [],
      monthlyTrends: [],
      categoryDistribution: [],
      performanceMetrics: {
        currentStreak: 0,
        longestStreak: 0,
        totalReviews: 0,
        averageRetention: 0,
        studyEfficiency: 0,
        weeklyGoal: 7,
        weeklyProgress: 0,
      },
    };

    render(<ProgressVisualization data={emptyData} />);
    
    // Should render without errors
    expect(screen.getByText('주간 목표')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('does not show exceeded indicator when progress <= 100%', () => {
    const normalProgressData = {
      ...mockData,
      performanceMetrics: {
        ...mockData.performanceMetrics,
        weeklyProgress: 25, // Less than goal
      },
    };

    render(<ProgressVisualization data={normalProgressData} />);
    
    // Should not show exceeded message
    expect(screen.queryByText('🎉 목표 초과!')).not.toBeInTheDocument();
  });

  it('handles NaN values correctly', () => {
    const dataWithNaN = {
      ...mockData,
      performanceMetrics: {
        currentStreak: NaN,
        longestStreak: undefined as any,
        totalReviews: null as any,
        averageRetention: Infinity,
        studyEfficiency: -Infinity,
        weeklyGoal: '',
        weeklyProgress: 'not a number',
      },
    };

    render(<ProgressVisualization data={dataWithNaN as any} />);
    
    // Should show default values instead of NaN
    expect(screen.queryByText('NaN')).not.toBeInTheDocument();
    expect(screen.queryByText('Infinity')).not.toBeInTheDocument();
  });
});