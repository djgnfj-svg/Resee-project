import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

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

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Mock user data for testing
export const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  timezone: 'Asia/Seoul',
  notification_enabled: true,
};

// Mock content data
export const mockContent = {
  id: 1,
  title: 'Test Content',
  content: 'This is test content',
  priority: 'medium' as const,
  category: 1,
  tags: [1, 2],
  author: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

// Mock category data
export const mockCategory = {
  id: 1,
  name: 'Test Category',
  description: 'Test category description',
  user: 1,
};

// Mock tag data
export const mockTag = {
  id: 1,
  name: 'test-tag',
};

// Utility function to create a test query client
export const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

// Utility function to wait for loading states
export const waitForLoadingToFinish = async () => {
  await new Promise(resolve => setTimeout(resolve, 0));
};

// Mock localStorage
export const createMockLocalStorage = () => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
};

// Mock file for testing file uploads
export const createMockFile = (name = 'test.png', type = 'image/png') => {
  const file = new File(['test'], name, { type });
  return file;
};

// Mock form data for testing
export const mockFormData = {
  title: 'Test Content',
  content: 'This is test content',
  priority: 'medium' as const,
  category: 1,
  tag_ids: [1, 2],
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };