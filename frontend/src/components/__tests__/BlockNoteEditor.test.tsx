import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BlockNoteEditor from '../BlockNoteEditor';
import { createMockFile } from '../../test-utils/test-utils';

describe('BlockNoteEditor (Markdown Editor)', () => {
  const defaultProps = {
    content: '',
    onChange: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render without crashing', () => {
    render(<BlockNoteEditor {...defaultProps} />);
    
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByText('굵게 (Ctrl+B)')).toBeInTheDocument();
  });

  it('should display placeholder text', () => {
    const placeholder = '내용을 입력하세요...';
    render(<BlockNoteEditor {...defaultProps} placeholder={placeholder} />);
    
    expect(screen.getByPlaceholderText(placeholder)).toBeInTheDocument();
  });

  it('should call onChange when content changes', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, 'Test content');
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('Test content');
    });
  });

  it('should handle initial content', () => {
    const initialContent = 'Initial markdown content';
    
    render(<BlockNoteEditor {...defaultProps} content={initialContent} />);
    
    expect(screen.getByDisplayValue(initialContent)).toBeInTheDocument();
  });

  it('should handle empty initial content', () => {
    render(<BlockNoteEditor {...defaultProps} content="" />);
    
    expect(screen.getByRole('textbox')).toHaveValue('');
  });

  it('should apply custom className', () => {
    const customClass = 'custom-editor-class';
    
    render(<BlockNoteEditor {...defaultProps} className={customClass} />);
    
    const container = screen.getByRole('textbox').closest('.markdown-editor');
    expect(container).toHaveClass(customClass);
  });

  it('should handle toolbar button clicks', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    // Click bold button
    const boldButton = screen.getByTitle('굵게 (Ctrl+B)');
    await user.click(boldButton);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('**굵은 텍스트**');
    });
  });

  it('should insert markdown syntax for different elements', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    // Test different toolbar buttons
    const italicButton = screen.getByTitle('기울임 (Ctrl+I)');
    await user.click(italicButton);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('*기울임 텍스트*');
    });
  });

  it('should handle heading insertion', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const h1Button = screen.getByTitle('제목 1');
    await user.click(h1Button);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('# 제목 1');
    });
  });

  it('should handle list insertion', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const listButton = screen.getByTitle('목록');
    await user.click(listButton);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('\n- 목록 항목');
    });
  });

  it('should handle image upload when provided', async () => {
    const onImageUpload = jest.fn().mockResolvedValue('https://example.com/image.jpg');
    const user = userEvent.setup();
    
    render(
      <BlockNoteEditor {...defaultProps} onImageUpload={onImageUpload} />
    );
    
    // Should show image upload button
    expect(screen.getByTitle('이미지 업로드')).toBeInTheDocument();
    
    // Simulate file selection
    const file = createMockFile('test.png', 'image/png');
    const fileInput = screen.getByRole('textbox').closest('.markdown-editor')
      ?.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (fileInput) {
      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });
      
      fireEvent.change(fileInput);
      
      await waitFor(() => {
        expect(onImageUpload).toHaveBeenCalledWith(file);
      });
    }
  });

  it('should handle image upload error', async () => {
    const onImageUpload = jest.fn().mockRejectedValue(new Error('Upload failed'));
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation();
    
    render(
      <BlockNoteEditor {...defaultProps} onImageUpload={onImageUpload} />
    );
    
    const file = createMockFile('test.png', 'image/png');
    const fileInput = screen.getByRole('textbox').closest('.markdown-editor')
      ?.querySelector('input[type="file"]') as HTMLInputElement;
    
    if (fileInput) {
      Object.defineProperty(fileInput, 'files', {
        value: [file],
        writable: false,
      });
      
      fireEvent.change(fileInput);
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('이미지 업로드 실패:', expect.any(Error));
        expect(alertSpy).toHaveBeenCalledWith('이미지 업로드에 실패했습니다.');
      });
    }
    
    consoleSpy.mockRestore();
    alertSpy.mockRestore();
  });

  it('should handle tab key for indentation', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} content="test" onChange={onChange} />);
    
    const editor = screen.getByRole('textbox');
    await user.click(editor);
    await user.keyboard('[Tab]');
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('  test');
    });
  });

  it('should handle Korean text input', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, '안녕하세요 한글 테스트입니다');
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('안녕하세요 한글 테스트입니다');
    });
  });

  it('should handle special characters and emojis', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const editor = screen.getByRole('textbox');
    await user.type(editor, '🚀 Special chars: @#$%^&*()');
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('🚀 Special chars: @#$%^&*()');
    });
  });

  it('should handle paste operations', async () => {
    render(<BlockNoteEditor {...defaultProps} />);
    
    const editor = screen.getByRole('textbox');
    
    // Simulate paste
    fireEvent.paste(editor, {
      clipboardData: {
        getData: () => 'Pasted content',
      },
    });
    
    // Should handle paste gracefully
    expect(editor).toBeInTheDocument();
  });

  it('should show markdown help section', () => {
    render(<BlockNoteEditor {...defaultProps} />);
    
    expect(screen.getByText('마크다운 도움말')).toBeInTheDocument();
  });

  it('should handle code insertion', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const codeButton = screen.getByTitle('인라인 코드');
    await user.click(codeButton);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('`코드`');
    });
  });

  it('should handle quote insertion', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const quoteButton = screen.getByTitle('인용문');
    await user.click(quoteButton);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('\n> 인용문');
    });
  });

  it('should handle link insertion', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const linkButton = screen.getByTitle('링크');
    await user.click(linkButton);
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('[링크 텍스트](URL)');
    });
  });

  it('should auto-resize textarea', async () => {
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} />);
    
    const editor = screen.getByRole('textbox') as HTMLTextAreaElement;
    const initialHeight = editor.style.height;
    
    await user.type(editor, 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5');
    
    // Height should be auto-adjusted
    expect(editor.style.height).not.toBe(initialHeight);
  });

  it('should not show image upload button when onImageUpload is not provided', () => {
    render(<BlockNoteEditor {...defaultProps} />);
    
    expect(screen.queryByTitle('이미지 업로드')).not.toBeInTheDocument();
  });

  it('should handle rapid content changes', async () => {
    const onChange = jest.fn();
    const user = userEvent.setup();
    
    render(<BlockNoteEditor {...defaultProps} onChange={onChange} />);
    
    const editor = screen.getByRole('textbox');
    
    // Rapid typing simulation
    await user.type(editor, 'abc');
    
    await waitFor(() => {
      expect(onChange).toHaveBeenCalledWith('abc');
    });
  });
});