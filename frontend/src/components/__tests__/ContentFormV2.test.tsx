import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ContentFormV2 from '../ContentFormV2';
import { createMockFile } from '../../test-utils/test-utils';

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
      {children}
    </QueryClientProvider>
  );
};

describe('ContentFormV2', () => {
  const defaultProps = {
    onSubmit: jest.fn(),
    onCancel: jest.fn(),
    isLoading: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', async () => {
    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    });
    expect(screen.getByTestId('blocknote-editor')).toBeInTheDocument();
    expect(screen.getByLabelText(/우선순위/i)).toBeInTheDocument();
  });

  it('should display form fields correctly', async () => {
    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    });
    
    expect(screen.getByLabelText(/카테고리/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/태그/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/우선순위/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /저장/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /취소/i })).toBeInTheDocument();
  });

  it('should handle form submission with valid data', async () => {
    const onSubmit = jest.fn();
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} onSubmit={onSubmit} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    });

    // Fill form
    await user.type(screen.getByLabelText(/제목/i), 'Test Content');
    
    // Change priority
    await user.selectOptions(screen.getByLabelText(/우선순위/i), 'high');

    // Submit form
    await user.click(screen.getByRole('button', { name: /저장/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Test Content',
          priority: 'high',
        })
      );
    });
  });

  it('should handle form cancellation', async () => {
    const onCancel = jest.fn();
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} onCancel={onCancel} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /취소/i })).toBeInTheDocument();
    });

    await user.click(screen.getByRole('button', { name: /취소/i }));

    expect(onCancel).toHaveBeenCalled();
  });

  it('should display validation errors for empty title', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /저장/i })).toBeInTheDocument();
    });

    // Try to submit without title
    await user.click(screen.getByRole('button', { name: /저장/i }));

    await waitFor(() => {
      expect(screen.getByText(/제목은 필수입니다/i)).toBeInTheDocument();
    });
  });

  it('should populate form with initial data', async () => {
    const initialData = {
      title: 'Initial Title',
      content: 'Initial content',
      priority: 'high' as const,
      category: 1,
      tag_ids: [1, 2],
    };

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} initialData={initialData} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Initial Title')).toBeInTheDocument();
    });
    
    expect(screen.getByDisplayValue('high')).toBeInTheDocument();
  });

  it('should handle category selection', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/카테고리/i)).toBeInTheDocument();
    });

    // Wait for categories to load
    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument();
    });

    // Select category
    await user.selectOptions(screen.getByLabelText(/카테고리/i), '1');

    expect(screen.getByDisplayValue('1')).toBeInTheDocument();
  });

  it('should handle tag selection', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/태그/i)).toBeInTheDocument();
    });

    // Wait for tags to load
    await waitFor(() => {
      expect(screen.getByText('basics')).toBeInTheDocument();
    });

    // Select tag
    await user.click(screen.getByText('basics'));

    // Tag should be selected
    expect(screen.getByText('basics')).toHaveClass('selected');
  });

  it('should handle content editor changes', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('blocknote-editor')).toBeInTheDocument();
    });

    const editor = screen.getByPlaceholderText('BlockNote Editor Mock');
    await user.type(editor, 'Test content');

    // Content should be updated in the form
    await waitFor(() => {
      expect(editor).toHaveValue('Test content');
    });
  });

  it('should show loading state correctly', async () => {
    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} isLoading={true} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /저장/i })).toBeDisabled();
    });
  });

  it('should handle image upload in editor', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByTestId('blocknote-editor')).toBeInTheDocument();
    });

    // Test image upload functionality
    const file = createMockFile('test.png', 'image/png');
    
    // This would normally trigger through the BlockNote editor
    // For testing, we just verify the component doesn't crash
    expect(screen.getByTestId('blocknote-editor')).toBeInTheDocument();
  });

  it('should validate required fields', async () => {
    const onSubmit = jest.fn();
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} onSubmit={onSubmit} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /저장/i })).toBeInTheDocument();
    });

    // Submit without required fields
    await user.click(screen.getByRole('button', { name: /저장/i }));

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/제목은 필수입니다/i)).toBeInTheDocument();
    });

    // onSubmit should not be called
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('should handle form reset on cancel', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    });

    // Fill some data
    await user.type(screen.getByLabelText(/제목/i), 'Test');

    // Cancel
    await user.click(screen.getByRole('button', { name: /취소/i }));

    // Form should still have the data (cancel doesn't reset)
    expect(screen.getByDisplayValue('Test')).toBeInTheDocument();
  });

  it('should handle priority change', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/우선순위/i)).toBeInTheDocument();
    });

    const prioritySelect = screen.getByLabelText(/우선순위/i);
    
    // Change to high priority
    await user.selectOptions(prioritySelect, 'high');
    expect(screen.getByDisplayValue('high')).toBeInTheDocument();

    // Change to low priority
    await user.selectOptions(prioritySelect, 'low');
    expect(screen.getByDisplayValue('low')).toBeInTheDocument();
  });

  it('should handle multiple tag selection', async () => {
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/태그/i)).toBeInTheDocument();
    });

    // Wait for tags to load
    await waitFor(() => {
      expect(screen.getByText('basics')).toBeInTheDocument();
    });

    // Select multiple tags
    await user.click(screen.getByText('basics'));
    await user.click(screen.getByText('advanced'));

    // Both tags should be selected
    expect(screen.getByText('basics')).toHaveClass('selected');
    expect(screen.getByText('advanced')).toHaveClass('selected');
  });

  it('should handle form submission with all fields', async () => {
    const onSubmit = jest.fn();
    const user = userEvent.setup();

    render(
      <Wrapper>
        <ContentFormV2 {...defaultProps} onSubmit={onSubmit} />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/제목/i)).toBeInTheDocument();
    });

    // Fill all fields
    await user.type(screen.getByLabelText(/제목/i), 'Complete Test');
    
    // Wait for data to load and select category
    await waitFor(() => {
      expect(screen.getByText('Python')).toBeInTheDocument();
    });
    await user.selectOptions(screen.getByLabelText(/카테고리/i), '1');

    // Select tags
    await user.click(screen.getByText('basics'));
    
    // Change priority
    await user.selectOptions(screen.getByLabelText(/우선순위/i), 'high');

    // Add content
    const editor = screen.getByPlaceholderText('BlockNote Editor Mock');
    await user.type(editor, 'Complete test content');

    // Submit
    await user.click(screen.getByRole('button', { name: /저장/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Complete Test',
          priority: 'high',
          category: 1,
          tag_ids: expect.arrayContaining([1]),
          content: expect.any(String),
        })
      );
    });
  });
});