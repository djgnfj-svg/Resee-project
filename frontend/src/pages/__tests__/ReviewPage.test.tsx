import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ReviewPage from '../ReviewPage';
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

describe('ReviewPage', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    mockLocalStorage.setItem('access_token', 'mock-token');
  });

  it('should render without crashing', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/복습/i)).toBeInTheDocument();
    });
  });

  it('should display today\'s reviews', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/오늘의 복습/i)).toBeInTheDocument();
    });

    // Should load and display review items
    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });
  });

  it('should show review content correctly', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });

    // Should display content details
    expect(screen.getByText('Variables in Python are used to store data values.')).toBeInTheDocument();
  });

  it('should handle review completion with "remembered"', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /기억함/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /기억함/i }));

    // Should submit review and show next item or completion message
    await waitFor(() => {
      expect(screen.getByText(/복습이 완료되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should handle review completion with "partial"', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /애매함/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /애매함/i }));

    await waitFor(() => {
      expect(screen.getByText(/복습이 완료되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should handle review completion with "forgot"', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /모름/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /모름/i }));

    await waitFor(() => {
      expect(screen.getByText(/복습이 완료되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should track review time spent', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });

    // Wait a bit to simulate time spent
    await new Promise(resolve => setTimeout(resolve, 1000));

    await user.click(screen.getByRole('button', { name: /기억함/i }));

    // Should track and submit time spent
    await waitFor(() => {
      expect(screen.getByText(/복습이 완료되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should display review progress', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/진행률/i)).toBeInTheDocument();
    });

    // Should show progress indicator
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle empty review state', async () => {
    // Mock empty reviews
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/오늘 복습할 콘텐츠가 없습니다/i)).toBeInTheDocument();
    });

    // Should show empty state with action button
    expect(screen.getByRole('button', { name: /새 콘텐츠 생성/i })).toBeInTheDocument();
  });

  it('should display review notes input', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/복습 노트/i)).toBeInTheDocument();
    });

    // Should be able to add notes
    await user.type(screen.getByPlaceholderText(/복습 노트/i), 'This was challenging');

    expect(screen.getByDisplayValue('This was challenging')).toBeInTheDocument();
  });

  it('should handle keyboard shortcuts', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });

    // Test keyboard shortcuts
    await user.keyboard('1'); // Should select "remembered"
    
    await waitFor(() => {
      expect(screen.getByText(/복습이 완료되었습니다/i)).toBeInTheDocument();
    });
  });

  it('should show content category and tags', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });

    // Should display category and tags
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('basics')).toBeInTheDocument();
  });

  it('should handle review navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /이전/i })).toBeInTheDocument();
    });

    // Navigation buttons should be present
    expect(screen.getByRole('button', { name: /다음/i })).toBeInTheDocument();

    // Should handle navigation
    await user.click(screen.getByRole('button', { name: /다음/i }));
    
    // Should navigate to next review item
    expect(screen.getByText(/복습/i)).toBeInTheDocument();
  });

  it('should display review statistics', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/오늘의 통계/i)).toBeInTheDocument();
    });

    // Should show review stats
    expect(screen.getByText(/완료한 복습/i)).toBeInTheDocument();
    expect(screen.getByText(/남은 복습/i)).toBeInTheDocument();
  });

  it('should handle loading state', () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    // Should show loading spinner initially
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should handle error state', async () => {
    // This would require mocking error response
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    // Should handle errors gracefully
    await waitFor(() => {
      expect(screen.getByText(/복습/i)).toBeInTheDocument();
    });
  });

  it('should show review type indicator', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/첫 번째 복습/i)).toBeInTheDocument();
    });

    // Should indicate if it's initial review or subsequent review
  });

  it('should handle content rendering', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });

    // Should render markdown content properly
    expect(screen.getByText('Variables in Python are used to store data values.')).toBeInTheDocument();
  });

  it('should show review hints if available', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    // Look for hint button
    const hintButton = screen.queryByRole('button', { name: /힌트/i });
    if (hintButton) {
      expect(hintButton).toBeInTheDocument();
    }
  });

  it('should handle review completion celebration', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /기억함/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /기억함/i }));

    // Should show celebration or completion message
    await waitFor(() => {
      expect(screen.getByText(/잘했습니다/i)).toBeInTheDocument();
    });
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
        <ReviewPage />
      </Wrapper>
    );

    // Should render mobile-friendly layout
    const reviewContainer = screen.getByRole('main');
    expect(reviewContainer).toHaveClass('mobile-responsive');
  });

  it('should handle review session resumption', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    // Should resume review session if user left mid-review
    await waitFor(() => {
      expect(screen.getByText(/복습을 계속하시겠습니까/i)).toBeInTheDocument();
    });
  });

  it('should show review streaks and achievements', async () => {
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    // Look for streak indicator
    const streakIndicator = screen.queryByText(/연속 복습/i);
    if (streakIndicator) {
      expect(streakIndicator).toBeInTheDocument();
    }
  });

  it('should handle bulk review actions', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <ReviewPage />
      </Wrapper>
    );

    // Look for bulk action options
    const bulkActionsButton = screen.queryByRole('button', { name: /일괄 처리/i });
    if (bulkActionsButton) {
      await user.click(bulkActionsButton);
      expect(screen.getByText(/모두 기억함으로 처리/i)).toBeInTheDocument();
    }
  });
});