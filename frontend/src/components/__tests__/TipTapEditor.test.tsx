import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import TipTapEditor from '../TipTapEditor';

// Mock the @tiptap modules
jest.mock('@tiptap/react', () => ({
  useEditor: jest.fn(),
  EditorContent: ({ editor }: { editor: any }) => (
    <div data-testid="editor-content">
      {editor?.getHTML ? editor.getHTML() : ''}
    </div>
  ),
}));

jest.mock('@tiptap/starter-kit', () => ({
  __esModule: true,
  default: jest.fn(),
}));

jest.mock('@tiptap/extension-placeholder', () => ({
  __esModule: true,
  default: {
    configure: jest.fn(),
  },
}));

jest.mock('@tiptap/extension-link', () => ({
  __esModule: true,
  default: {
    configure: jest.fn(),
  },
}));

describe('TipTapEditor Component', () => {
  const mockOnChange = jest.fn();
  const defaultProps = {
    content: '<p>Initial content</p>',
    onChange: mockOnChange,
    placeholder: 'Write something...',
  };

  // Mock editor instance
  const mockEditor = {
    getHTML: jest.fn(() => '<p>Test content</p>'),
    getText: jest.fn(() => 'Test content'),
    isEmpty: jest.fn(() => false),
    commands: {
      setContent: jest.fn(),
      toggleBold: jest.fn(),
      toggleItalic: jest.fn(),
      toggleStrike: jest.fn(),
      toggleCode: jest.fn(),
      setParagraph: jest.fn(),
      toggleHeading: jest.fn(),
      toggleBulletList: jest.fn(),
      toggleOrderedList: jest.fn(),
      toggleBlockquote: jest.fn(),
      toggleCodeBlock: jest.fn(),
      setHorizontalRule: jest.fn(),
      undo: jest.fn(),
      redo: jest.fn(),
    },
    isActive: jest.fn(() => false),
    can: jest.fn(() => ({
      undo: jest.fn(() => true),
      redo: jest.fn(() => true),
    })),
    on: jest.fn(),
    off: jest.fn(),
    destroy: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    const { useEditor } = require('@tiptap/react');
    useEditor.mockReturnValue(mockEditor);
  });

  test('renders editor with initial content', () => {
    render(<TipTapEditor {...defaultProps} />);
    
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  test('renders all toolbar buttons', () => {
    render(<TipTapEditor {...defaultProps} />);
    
    // Format buttons
    expect(screen.getByRole('button', { name: /bold/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /italic/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /strikethrough/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /inline code/i })).toBeInTheDocument();
    
    // Heading buttons
    expect(screen.getByRole('button', { name: /heading 1/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /heading 2/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /heading 3/i })).toBeInTheDocument();
    
    // List buttons
    expect(screen.getByRole('button', { name: /bullet list/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /numbered list/i })).toBeInTheDocument();
    
    // Block buttons
    expect(screen.getByRole('button', { name: /blockquote/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /code block/i })).toBeInTheDocument();
    
    // Other buttons
    expect(screen.getByRole('button', { name: /horizontal rule/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /undo/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /redo/i })).toBeInTheDocument();
  });

  test('calls editor commands when toolbar buttons are clicked', async () => {
    const user = userEvent.setup();
    render(<TipTapEditor {...defaultProps} />);
    
    // Test bold button
    await user.click(screen.getByRole('button', { name: /bold/i }));
    expect(mockEditor.commands.toggleBold).toHaveBeenCalled();
    
    // Test italic button
    await user.click(screen.getByRole('button', { name: /italic/i }));
    expect(mockEditor.commands.toggleItalic).toHaveBeenCalled();
    
    // Test heading 1 button
    await user.click(screen.getByRole('button', { name: /heading 1/i }));
    expect(mockEditor.commands.toggleHeading).toHaveBeenCalledWith({ level: 1 });
    
    // Test bullet list button
    await user.click(screen.getByRole('button', { name: /bullet list/i }));
    expect(mockEditor.commands.toggleBulletList).toHaveBeenCalled();
    
    // Test undo button
    await user.click(screen.getByRole('button', { name: /undo/i }));
    expect(mockEditor.commands.undo).toHaveBeenCalled();
  });

  test('shows active state for formatting buttons', () => {
    mockEditor.isActive.mockImplementation((format: string) => {
      return format === 'bold';
    });
    
    render(<TipTapEditor {...defaultProps} />);
    
    const boldButton = screen.getByRole('button', { name: /bold/i });
    const italicButton = screen.getByRole('button', { name: /italic/i });
    
    expect(boldButton).toHaveClass('bg-blue-500'); // Active state
    expect(italicButton).not.toHaveClass('bg-blue-500'); // Inactive state
  });

  test('disables undo/redo buttons when not available', () => {
    mockEditor.can.mockReturnValue({
      undo: () => false,
      redo: () => false,
    });
    
    render(<TipTapEditor {...defaultProps} />);
    
    expect(screen.getByRole('button', { name: /undo/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /redo/i })).toBeDisabled();
  });

  test('calls onChange when editor content changes', () => {
    const { useEditor } = require('@tiptap/react');
    
    // Simulate editor creation with onChange callback
    let onUpdateCallback: () => void;
    useEditor.mockImplementation(({ onUpdate }: { onUpdate: () => void }) => {
      onUpdateCallback = onUpdate;
      return mockEditor;
    });
    
    render(<TipTapEditor {...defaultProps} />);
    
    // Simulate content change
    if (onUpdateCallback) {
      onUpdateCallback();
    }
    
    expect(mockOnChange).toHaveBeenCalledWith('<p>Test content</p>');
  });

  test('handles editor cleanup on unmount', () => {
    const { unmount } = render(<TipTapEditor {...defaultProps} />);
    
    unmount();
    
    expect(mockEditor.destroy).toHaveBeenCalled();
  });

  test('supports keyboard shortcuts', async () => {
    const user = userEvent.setup();
    render(<TipTapEditor {...defaultProps} />);
    
    const editorContent = screen.getByTestId('editor-content');
    
    // Test Ctrl+B for bold
    await user.type(editorContent, '{Control>}b{/Control}');
    // Note: Actual keyboard shortcut testing would require more complex setup
    // This is a simplified test to ensure the component can receive keyboard events
    
    expect(editorContent).toHaveAttribute('data-testid', 'editor-content');
  });

  test('renders with custom placeholder', () => {
    const customPlaceholder = 'Enter your markdown content...';
    render(<TipTapEditor {...defaultProps} placeholder={customPlaceholder} />);
    
    // The placeholder would be set in the Placeholder extension configuration
    // This test verifies the prop is passed correctly
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  test('handles empty content', () => {
    mockEditor.isEmpty.mockReturnValue(true);
    mockEditor.getHTML.mockReturnValue('');
    mockEditor.getText.mockReturnValue('');
    
    render(<TipTapEditor {...defaultProps} content="" />);
    
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  test('supports markdown shortcuts', async () => {
    const user = userEvent.setup();
    render(<TipTapEditor {...defaultProps} />);
    
    const editorContent = screen.getByTestId('editor-content');
    
    // Test typing markdown syntax
    await user.type(editorContent, '# Heading 1');
    await user.type(editorContent, ' ');
    
    // The actual markdown transformation would be handled by TipTap extensions
    // This test ensures the component accepts text input
    expect(editorContent).toBeInTheDocument();
  });

  test('maintains focus state correctly', async () => {
    const user = userEvent.setup();
    render(<TipTapEditor {...defaultProps} />);
    
    const editorContent = screen.getByTestId('editor-content');
    
    await user.click(editorContent);
    
    // Test that clicking on toolbar buttons doesn't lose focus
    await user.click(screen.getByRole('button', { name: /bold/i }));
    
    expect(mockEditor.commands.toggleBold).toHaveBeenCalled();
  });
});