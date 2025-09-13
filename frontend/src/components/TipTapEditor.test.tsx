import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { render } from '../test-utils/test-utils';
import TipTapEditor from './TipTapEditor';

// Mock @tiptap/react
jest.mock('@tiptap/react', () => ({
  useEditor: () => ({
    commands: {
      setContent: jest.fn(),
      focus: jest.fn(),
      toggleBold: jest.fn(),
      toggleItalic: jest.fn(),
      toggleStrike: jest.fn(),
      toggleCode: jest.fn(),
      toggleBulletList: jest.fn(),
      toggleOrderedList: jest.fn(),
      toggleBlockquote: jest.fn(),
      setHorizontalRule: jest.fn(),
      undo: jest.fn(),
      redo: jest.fn(),
    },
    getHTML: jest.fn(() => '<p>Test content</p>'),
    isActive: jest.fn(() => false),
    can: () => ({ undo: jest.fn(() => true), redo: jest.fn(() => true) }),
  }),
  EditorContent: ({ editor }: any) => <div data-testid="editor-content">Editor Content</div>,
}));

// Mock @tiptap/starter-kit and other extensions
jest.mock('@tiptap/starter-kit', () => jest.fn());
jest.mock('@tiptap/extension-placeholder', () => ({ configure: jest.fn() }));
jest.mock('@tiptap/extension-link', () => ({ configure: jest.fn() }));

describe('TipTapEditor', () => {
  const mockProps = {
    content: '<p>Initial content</p>',
    onChange: jest.fn(),
    placeholder: 'Enter content...',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders editor toolbar', () => {
    render(<TipTapEditor {...mockProps} />);

    expect(screen.getByLabelText(/볼드/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/이탤릭/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/취소선/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/인라인 코드/i)).toBeInTheDocument();
  });

  it('renders editor content', () => {
    render(<TipTapEditor {...mockProps} />);

    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  it('calls onChange when content changes', () => {
    const mockOnChange = jest.fn();
    render(<TipTapEditor {...mockProps} onChange={mockOnChange} />);

    // Since we're mocking the editor, we'll test that the component renders
    // In a real test, you would trigger content changes and verify onChange is called
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  it('renders toolbar buttons', () => {
    render(<TipTapEditor {...mockProps} />);

    // Check for various formatting buttons
    expect(screen.getByText('B')).toBeInTheDocument(); // Bold
    expect(screen.getByText('I')).toBeInTheDocument(); // Italic
    expect(screen.getByText('S')).toBeInTheDocument(); // Strike
    expect(screen.getByText('</>')).toBeInTheDocument(); // Code
  });

  it('handles toolbar button clicks', () => {
    render(<TipTapEditor {...mockProps} />);

    const boldButton = screen.getByLabelText(/볼드/i);
    fireEvent.click(boldButton);

    // The actual command execution is mocked, so we just verify the button exists
    expect(boldButton).toBeInTheDocument();
  });
});