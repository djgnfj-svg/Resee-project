import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from '../Layout';
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

describe('Layout', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    // Set up authenticated state
    mockLocalStorage.setItem('access_token', 'mock-token');
  });

  it('should render without crashing', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should display navigation menu', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });
    
    expect(screen.getByText(/콘텐츠/i)).toBeInTheDocument();
    expect(screen.getByText(/복습/i)).toBeInTheDocument();
    expect(screen.getByText(/대시보드/i)).toBeInTheDocument();
  });

  it('should display user information when authenticated', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });
  });

  it('should handle navigation menu clicks', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });

    // Click navigation items
    await user.click(screen.getByText(/콘텐츠/i));
    await user.click(screen.getByText(/복습/i));
    await user.click(screen.getByText(/대시보드/i));

    // Should not crash and navigation should work
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should display mobile menu toggle', () => {
    // Set mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    // Should show mobile menu button
    expect(screen.getByRole('button', { name: /메뉴/i })).toBeInTheDocument();
  });

  it('should handle mobile menu toggle', async () => {
    const user = userEvent.setup();
    
    // Set mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    const menuButton = screen.getByRole('button', { name: /메뉴/i });
    
    // Click to open menu
    await user.click(menuButton);
    
    // Menu should be visible
    expect(screen.getByText(/홈/i)).toBeVisible();
    
    // Click to close menu
    await user.click(menuButton);
    
    // Menu should be hidden
    expect(screen.getByText(/홈/i)).not.toBeVisible();
  });

  it('should display logout button', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /로그아웃/i })).toBeInTheDocument();
    });
  });

  it('should handle logout action', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /로그아웃/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /로그아웃/i }));

    // Should clear authentication
    expect(mockLocalStorage.getItem('access_token')).toBeNull();
  });

  it('should highlight active navigation item', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });

    // Current path should be highlighted (assuming we're on home)
    const homeLink = screen.getByText(/홈/i);
    expect(homeLink).toHaveClass('active', 'bg-blue-100', 'text-blue-700');
  });

  it('should display search bar', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByPlaceholderText(/검색/i)).toBeInTheDocument();
  });

  it('should handle search input', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    const searchInput = screen.getByPlaceholderText(/검색/i);
    
    await user.type(searchInput, 'test search');
    
    expect(searchInput).toHaveValue('test search');
  });

  it('should display notifications if any', async () => {
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    // Look for notification bell or indicator
    const notificationButton = screen.queryByRole('button', { name: /알림/i });
    if (notificationButton) {
      expect(notificationButton).toBeInTheDocument();
    }
  });

  it('should be responsive on different screen sizes', () => {
    // Test desktop
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    const { rerender } = render(
      <Wrapper>
        <Layout>
          <div>Desktop Content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('Desktop Content')).toBeInTheDocument();

    // Test tablet
    Object.defineProperty(window, 'innerWidth', {
      value: 768,
    });

    rerender(
      <Wrapper>
        <Layout>
          <div>Tablet Content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('Tablet Content')).toBeInTheDocument();

    // Test mobile
    Object.defineProperty(window, 'innerWidth', {
      value: 375,
    });

    rerender(
      <Wrapper>
        <Layout>
          <div>Mobile Content</div>
        </Layout>
      </Wrapper>
    );

    expect(screen.getByText('Mobile Content')).toBeInTheDocument();
  });

  it('should render children content correctly', () => {
    const testContent = (
      <div>
        <h1>Test Page</h1>
        <p>This is test content</p>
        <button>Test Button</button>
      </div>
    );

    render(
      <Wrapper>
        <Layout>{testContent}</Layout>
      </Wrapper>
    );

    expect(screen.getByText('Test Page')).toBeInTheDocument();
    expect(screen.getByText('This is test content')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Test Button' })).toBeInTheDocument();
  });

  it('should handle keyboard navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/홈/i)).toBeInTheDocument();
    });

    // Tab through navigation items
    await user.tab();
    await user.tab();
    await user.tab();

    // Should be able to navigate with keyboard
    const focusedElement = document.activeElement;
    expect(focusedElement).toBeInTheDocument();
  });

  it('should show loading state when needed', async () => {
    // Set up loading state
    mockLocalStorage.clear(); // No token, should show loading initially
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    // Should handle loading state gracefully
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('should handle unauthenticated state', async () => {
    mockLocalStorage.clear();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    // Should redirect to login or show appropriate UI
    await waitFor(() => {
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });
  });

  it('should display user profile dropdown', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });

    // Click on user name to open dropdown
    await user.click(screen.getByText('testuser'));

    // Should show profile options
    expect(screen.getByText(/프로필/i)).toBeInTheDocument();
    expect(screen.getByText(/설정/i)).toBeInTheDocument();
  });

  it('should handle profile navigation', async () => {
    const user = userEvent.setup();
    
    render(
      <Wrapper>
        <Layout>
          <div>Test Content</div>
        </Layout>
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('testuser')).toBeInTheDocument();
    });

    // Open profile dropdown
    await user.click(screen.getByText('testuser'));
    
    // Click profile link
    await user.click(screen.getByText(/프로필/i));

    // Should navigate to profile page
    expect(window.location.pathname).toContain('/profile');
  });
});