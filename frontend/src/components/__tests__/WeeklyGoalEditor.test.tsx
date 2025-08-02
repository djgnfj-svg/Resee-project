import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WeeklyGoalEditor from '../WeeklyGoalEditor';

// Mock the API
jest.mock('../../utils/api', () => ({
  weeklyGoalAPI: {
    updateGoal: jest.fn(),
  },
}));

import { weeklyGoalAPI } from '../../utils/api';

describe('WeeklyGoalEditor', () => {
  const mockOnGoalUpdate = jest.fn();
  const mockUpdateGoal = weeklyGoalAPI.updateGoal as jest.MockedFunction<typeof weeklyGoalAPI.updateGoal>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders current goal value', () => {
    render(<WeeklyGoalEditor currentGoal={7} onGoalUpdate={mockOnGoalUpdate} />);
    
    expect(screen.getByText('7회')).toBeInTheDocument();
  });

  it('shows input field when clicked', async () => {
    const user = userEvent.setup();
    render(<WeeklyGoalEditor currentGoal={7} onGoalUpdate={mockOnGoalUpdate} />);
    
    // Click on the goal display
    await user.click(screen.getByText('7회'));
    
    // Should show input field
    const input = screen.getByRole('spinbutton');
    expect(input).toBeInTheDocument();
    expect(input).toHaveValue(7);
  });

  it('updates goal on successful submission', async () => {
    const user = userEvent.setup();
    mockUpdateGoal.mockResolvedValueOnce({ weekly_goal: 15 });
    
    render(<WeeklyGoalEditor currentGoal={7} onGoalUpdate={mockOnGoalUpdate} />);
    
    // Click to edit
    await user.click(screen.getByText('7회'));
    
    // Change value
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '15');
    
    // Submit by pressing Enter
    await user.keyboard('{Enter}');
    
    await waitFor(() => {
      expect(mockUpdateGoal).toHaveBeenCalledWith(15);
      expect(mockOnGoalUpdate).toHaveBeenCalledWith(15);
    });
  });

  it('cancels editing on Escape key', async () => {
    const user = userEvent.setup();
    render(<WeeklyGoalEditor currentGoal={7} onGoalUpdate={mockOnGoalUpdate} />);
    
    // Click to edit
    await user.click(screen.getByText('7회'));
    
    // Press Escape
    await user.keyboard('{Escape}');
    
    // Should go back to display mode
    expect(screen.getByText('7회')).toBeInTheDocument();
    expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument();
  });

  it('validates goal range (1-100)', async () => {
    const user = userEvent.setup();
    render(<WeeklyGoalEditor currentGoal={7} onGoalUpdate={mockOnGoalUpdate} />);
    
    // Click to edit
    await user.click(screen.getByText('7회'));
    
    // Try to set invalid value
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '0');
    await user.keyboard('{Enter}');
    
    // Should not call API for invalid value
    expect(mockUpdateGoal).not.toHaveBeenCalled();
    
    // Try value over 100
    await user.clear(input);
    await user.type(input, '101');
    await user.keyboard('{Enter}');
    
    // Should not call API
    expect(mockUpdateGoal).not.toHaveBeenCalled();
  });

  it('is disabled when onGoalUpdate is not provided', () => {
    render(<WeeklyGoalEditor currentGoal={7} disabled />);
    
    const element = screen.getByText('7회');
    expect(element.parentElement).toHaveClass('cursor-default');
    
    // Clicking should not enable editing
    fireEvent.click(element);
    expect(screen.queryByRole('spinbutton')).not.toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const user = userEvent.setup();
    mockUpdateGoal.mockRejectedValueOnce(new Error('Network error'));
    
    render(<WeeklyGoalEditor currentGoal={7} onGoalUpdate={mockOnGoalUpdate} />);
    
    // Click to edit
    await user.click(screen.getByText('7회'));
    
    // Change value
    const input = screen.getByRole('spinbutton');
    await user.clear(input);
    await user.type(input, '10');
    await user.keyboard('{Enter}');
    
    await waitFor(() => {
      expect(mockUpdateGoal).toHaveBeenCalledWith(10);
      // Should not update on error
      expect(mockOnGoalUpdate).not.toHaveBeenCalled();
    });
  });
});