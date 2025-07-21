import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ErrorBoundary from '../ErrorBoundary';

// Mock console.error to avoid error logs in tests
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

// Component that throws an error for testing
const ThrowError = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error message');
  }
  return <div data-testid="working-component">Component is working</div>;
};

// Component that throws an error in useEffect
const ThrowErrorInEffect = ({ shouldThrow = false }: { shouldThrow?: boolean }) => {
  React.useEffect(() => {
    if (shouldThrow) {
      throw new Error('Effect error message');
    }
  }, [shouldThrow]);
  
  return <div data-testid="effect-component">Effect component</div>;
};

describe('ErrorBoundary Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('working-component')).toBeInTheDocument();
    expect(screen.getByText('Component is working')).toBeInTheDocument();
  });

  test('renders error UI when child component throws an error', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.queryByTestId('working-component')).not.toBeInTheDocument();
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
    expect(screen.getByText('페이지를 새로고침하거나 잠시 후 다시 시도해주세요.')).toBeInTheDocument();
  });

  test('shows error details in development mode', () => {
    // Mock development environment
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('오류 상세 정보:')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();

    // Restore original environment
    process.env.NODE_ENV = originalEnv;
  });

  test('hides error details in production mode', () => {
    // Mock production environment
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'production';

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.queryByText('오류 상세 정보:')).not.toBeInTheDocument();
    expect(screen.queryByText('Test error message')).not.toBeInTheDocument();

    // Restore original environment
    process.env.NODE_ENV = originalEnv;
  });

  test('shows retry button that resets error state', async () => {
    const user = userEvent.setup();
    
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Error UI should be visible
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
    
    const retryButton = screen.getByRole('button', { name: /다시 시도/i });
    expect(retryButton).toBeInTheDocument();

    // Click retry button
    await user.click(retryButton);

    // Rerender with no error
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    // Component should work normally again
    expect(screen.getByTestId('working-component')).toBeInTheDocument();
    expect(screen.queryByText('오류가 발생했습니다')).not.toBeInTheDocument();
  });

  test('shows reload page button', async () => {
    const user = userEvent.setup();
    
    // Mock window.location.reload
    const mockReload = jest.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    const reloadButton = screen.getByRole('button', { name: /페이지 새로고침/i });
    expect(reloadButton).toBeInTheDocument();

    await user.click(reloadButton);

    expect(mockReload).toHaveBeenCalled();
  });

  test('logs error information for debugging', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(consoleSpy).toHaveBeenCalledWith(
      'ErrorBoundary caught an error:',
      expect.any(Error),
      expect.any(Object)
    );

    consoleSpy.mockRestore();
  });

  test('handles errors with custom fallback component', () => {
    const CustomFallback = ({ error }: { error: Error }) => (
      <div data-testid="custom-fallback">
        Custom error: {error.message}
      </div>
    );

    render(
      <ErrorBoundary fallback={CustomFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
    expect(screen.getByText('Custom error: Test error message')).toBeInTheDocument();
  });

  test('resets error state when children change', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Error UI should be visible
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();

    // Rerender with different children
    rerender(
      <ErrorBoundary>
        <div data-testid="new-component">New component</div>
      </ErrorBoundary>
    );

    // Error state should be reset
    expect(screen.getByTestId('new-component')).toBeInTheDocument();
    expect(screen.queryByText('오류가 발생했습니다')).not.toBeInTheDocument();
  });

  test('handles multiple consecutive errors', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // First error
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();

    // Reset with working component
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    expect(screen.getByTestId('working-component')).toBeInTheDocument();

    // Throw another error
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Should show error UI again
    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
  });

  test('provides helpful error information for developers', () => {
    const originalEnv = process.env.NODE_ENV;
    process.env.NODE_ENV = 'development';

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    expect(screen.getByText('오류 상세 정보:')).toBeInTheDocument();
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    
    // Should show component stack in development
    const errorDetails = screen.getByTestId('error-details');
    expect(errorDetails).toBeInTheDocument();

    process.env.NODE_ENV = originalEnv;
  });

  test('handles errors with no error message', () => {
    const ThrowEmptyError = () => {
      throw new Error('');
    };

    render(
      <ErrorBoundary>
        <ThrowEmptyError />
      </ErrorBoundary>
    );

    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
    expect(screen.getByText('페이지를 새로고침하거나 잠시 후 다시 시도해주세요.')).toBeInTheDocument();
  });

  test('handles non-Error objects thrown as errors', () => {
    const ThrowString = () => {
      throw 'String error';
    };

    render(
      <ErrorBoundary>
        <ThrowString />
      </ErrorBoundary>
    );

    expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
  });

  test('maintains accessibility features', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Error container should have proper ARIA attributes
    const errorContainer = screen.getByRole('alert');
    expect(errorContainer).toBeInTheDocument();
    expect(errorContainer).toHaveAttribute('aria-live', 'assertive');

    // Buttons should be properly labeled
    const retryButton = screen.getByRole('button', { name: /다시 시도/i });
    const reloadButton = screen.getByRole('button', { name: /페이지 새로고침/i });
    
    expect(retryButton).toBeInTheDocument();
    expect(reloadButton).toBeInTheDocument();
  });

  test('does not catch errors in event handlers', () => {
    // ErrorBoundary only catches errors in render methods, lifecycle methods, and constructors
    // It does not catch errors in event handlers, which is expected behavior
    
    const ComponentWithEventHandler = () => {
      const handleClick = () => {
        throw new Error('Event handler error');
      };

      return (
        <button onClick={handleClick} data-testid="error-button">
          Click to throw error
        </button>
      );
    };

    render(
      <ErrorBoundary>
        <ComponentWithEventHandler />
      </ErrorBoundary>
    );

    const button = screen.getByTestId('error-button');
    expect(button).toBeInTheDocument();

    // The component should render normally even though it has a handler that will throw
    expect(screen.queryByText('오류가 발생했습니다')).not.toBeInTheDocument();
  });
});