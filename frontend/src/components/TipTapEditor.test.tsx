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
jest.mock('@tiptap/starter-kit', () => ({
  __esModule: true,
  default: {
    configure: jest.fn(() => ({})),
  },
}));
jest.mock('@tiptap/extension-placeholder', () => ({
  __esModule: true,
  default: {
    configure: jest.fn(() => ({})),
  },
}));
jest.mock('@tiptap/extension-link', () => ({
  __esModule: true,
  default: {
    configure: jest.fn(() => ({})),
  },
}));

describe('TipTapEditor', () => {
  const mockProps = {
    content: '<p>Initial content</p>',
    onChange: jest.fn(),
    placeholder: 'Enter content...',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders editor content area', () => {
    render(<TipTapEditor {...mockProps} />);

    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  it('renders with border container', () => {
    const { container } = render(<TipTapEditor {...mockProps} />);

    const editorContainer = container.querySelector('.border');
    expect(editorContainer).toBeInTheDocument();
  });

  it('renders editor with custom className', () => {
    const { container } = render(<TipTapEditor {...mockProps} className="custom-class" />);

    const editorContainer = container.querySelector('.custom-class');
    expect(editorContainer).toBeInTheDocument();
  });

  it('renders with default placeholder', () => {
    const { container } = render(
      <TipTapEditor content="" onChange={jest.fn()} />
    );

    // Component should render even without explicit placeholder
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
  });

  it('handles empty content gracefully', () => {
    const { container } = render(
      <TipTapEditor content="" onChange={jest.fn()} placeholder="Type here..." />
    );

    // Editor should still render with empty content
    expect(screen.getByTestId('editor-content')).toBeInTheDocument();
    expect(container.querySelector('.border')).toBeInTheDocument();
  });
});