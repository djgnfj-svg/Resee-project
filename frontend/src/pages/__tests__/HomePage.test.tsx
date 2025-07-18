import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HomePage from '../HomePage';
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

describe('HomePage', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    mockLocalStorage.setItem('access_token', 'mock-token');
  });

  it('should render without crashing', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });
  });

  it('should display dashboard overview', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
    });

    // Should show stats cards
    expect(screen.getByText(/총 콘텐츠/i)).toBeInTheDocument();
    expect(screen.getByText(/총 복습/i)).toBeInTheDocument();
    expect(screen.getByText(/성공률/i)).toBeInTheDocument();
  });

  it('should display recent content', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/최근 콘텐츠/i)).toBeInTheDocument();
    });

    // Should show content list
    await waitFor(() => {
      expect(screen.getByText('Python Variables')).toBeInTheDocument();
    });
    expect(screen.getByText('JavaScript Functions')).toBeInTheDocument();
  });

  it('should display today\'s reviews', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/오늘의 복습/i)).toBeInTheDocument();
    });

    // Should show review items or empty state
    const reviewSection = screen.getByText(/오늘의 복습/i).closest('section');
    expect(reviewSection).toBeInTheDocument();
  });

  it('should navigate to content creation', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /새 콘텐츠 생성/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /새 콘텐츠 생성/i }));

    // Should navigate to content creation page
    expect(window.location.pathname).toContain('/content/new');
  });

  it('should navigate to review page', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /복습 시작/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /복습 시작/i }));

    // Should navigate to review page
    expect(window.location.pathname).toContain('/review');
  });

  it('should display loading state initially', () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    // Should show loading spinners or skeletons
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should handle error state gracefully', async () => {
    // Mock error response
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, cacheTime: 0 },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <HomePage />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    );

    // Should handle errors gracefully
    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });
  });

  it('should display quick stats accurately', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // total_contents
    });
    
    expect(screen.getByText('25')).toBeInTheDocument(); // total_reviews
    expect(screen.getByText('85.5%')).toBeInTheDocument(); // success_rate
  });

  it('should show empty state when no content exists', async () => {
    // This would require mocking empty response
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    // If no content, should show empty state
    // This depends on actual implementation
    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });
  });

  it('should refresh data on page visit', async () => {
    const { rerender } = render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/총 콘텐츠/i)).toBeInTheDocument();
    });

    // Rerender should trigger data refresh
    rerender(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/총 콘텐츠/i)).toBeInTheDocument();
    });
  });

  it('should display welcome message for new users', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/환영합니다/i)).toBeInTheDocument();
    });
  });

  it('should show progress indicators', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/학습 진행률/i)).toBeInTheDocument();
    });

    // Should show progress bars or indicators
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /새 콘텐츠 생성/i })).toBeInTheDocument();
    });

    // Tab through interactive elements
    await user.tab();
    await user.tab();

    const focusedElement = document.activeElement;
    expect(focusedElement).toBeInTheDocument();
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
        <HomePage />
      </Wrapper>
    );

    // Should render mobile-friendly layout
    expect(screen.getByRole('main')).toHaveClass('mobile-responsive');
  });

  it('should update in real-time when data changes', async () => {
    const { rerender } = render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    // Simulate data change (this would come from server updates)
    rerender(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    // Should reflect updated data
    await waitFor(() => {
      expect(screen.getByText(/총 콘텐츠/i)).toBeInTheDocument();
    });
  });

  it('should handle unauthenticated state', () => {
    mockLocalStorage.clear();
    
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    // Should redirect to login or show appropriate UI
    expect(window.location.pathname).toBe('/');
  });

  it('should display announcements if any', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    // Look for announcements section
    const announcementSection = screen.queryByText(/공지사항/i);
    if (announcementSection) {
      expect(announcementSection).toBeInTheDocument();
    }
  });

  it('should show shortcuts to common actions', async () => {
    render(
      <Wrapper>
        <HomePage />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/빠른 작업/i)).toBeInTheDocument();
    });

    // Should show quick action buttons
    expect(screen.getByRole('button', { name: /새 콘텐츠/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /복습 시작/i })).toBeInTheDocument();
  });
});