import React, { useCallback, useState, useRef } from 'react';

interface BlockNoteEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  onImageUpload?: (file: File) => Promise<string>;
  className?: string;
}

const BlockNoteEditor: React.FC<BlockNoteEditorProps> = ({
  content,
  onChange,
  placeholder = '여기에 내용을 입력하세요...',
  onImageUpload,
  className = ''
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }, [onChange]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = e.currentTarget;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      
      // Insert tab
      const newValue = content.substring(0, start) + '  ' + content.substring(end);
      onChange(newValue);
      
      // Move cursor
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 2;
      }, 0);
    }
  }, [content, onChange]);

  const insertText = useCallback((text: string) => {
    if (!textareaRef.current) return;
    
    const textarea = textareaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    
    const newValue = content.substring(0, start) + text + content.substring(end);
    onChange(newValue);
    
    // Move cursor to end of inserted text
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + text.length;
      textarea.focus();
    }, 0);
  }, [content, onChange]);

  const handleImageUpload = useCallback(async (file: File) => {
    if (!onImageUpload) return;
    
    setIsUploading(true);
    try {
      const imageUrl = await onImageUpload(file);
      const imageMarkdown = `![${file.name}](${imageUrl})`;
      insertText(imageMarkdown);
    } catch (error) {
      console.error('이미지 업로드 실패:', error);
      alert('이미지 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  }, [onImageUpload, insertText]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleImageUpload(file);
    }
    // Reset input
    e.target.value = '';
  }, [handleImageUpload]);

  const insertMarkdown = useCallback((type: string) => {
    switch (type) {
      case 'bold':
        insertText('**굵은 텍스트**');
        break;
      case 'italic':
        insertText('*기울임 텍스트*');
        break;
      case 'heading1':
        insertText('# 제목 1');
        break;
      case 'heading2':
        insertText('## 제목 2');
        break;
      case 'heading3':
        insertText('### 제목 3');
        break;
      case 'list':
        insertText('\n- 목록 항목');
        break;
      case 'numbered-list':
        insertText('\n1. 번호 목록 항목');
        break;
      case 'code':
        insertText('`코드`');
        break;
      case 'code-block':
        insertText('\n```\n코드 블록\n```\n');
        break;
      case 'quote':
        insertText('\n> 인용문');
        break;
      case 'link':
        insertText('[링크 텍스트](URL)');
        break;
    }
  }, [insertText]);

  return (
    <div className={`markdown-editor ${className}`}>
      {/* Toolbar */}
      <div className="editor-toolbar">
        <button
          type="button"
          onClick={() => insertMarkdown('bold')}
          className="toolbar-btn"
          title="굵게 (Ctrl+B)"
        >
          <strong>B</strong>
        </button>
        
        <button
          type="button"
          onClick={() => insertMarkdown('italic')}
          className="toolbar-btn"
          title="기울임 (Ctrl+I)"
        >
          <em>I</em>
        </button>
        
        <div className="toolbar-separator" />
        
        <button
          type="button"
          onClick={() => insertMarkdown('heading1')}
          className="toolbar-btn"
          title="제목 1"
        >
          H1
        </button>
        
        <button
          type="button"
          onClick={() => insertMarkdown('heading2')}
          className="toolbar-btn"
          title="제목 2"
        >
          H2
        </button>
        
        <button
          type="button"
          onClick={() => insertMarkdown('heading3')}
          className="toolbar-btn"
          title="제목 3"
        >
          H3
        </button>
        
        <div className="toolbar-separator" />
        
        <button
          type="button"
          onClick={() => insertMarkdown('list')}
          className="toolbar-btn"
          title="목록"
        >
          {'•'}
        </button>
        
        <button
          type="button"
          onClick={() => insertMarkdown('numbered-list')}
          className="toolbar-btn"
          title="번호 목록"
        >
          1.
        </button>
        
        <div className="toolbar-separator" />
        
        <button
          type="button"
          onClick={() => insertMarkdown('quote')}
          className="toolbar-btn"
          title="인용문"
        >
          "
        </button>
        
        <button
          type="button"
          onClick={() => insertMarkdown('code')}
          className="toolbar-btn"
          title="인라인 코드"
        >
          {'</>'}
        </button>
        
        <button
          type="button"
          onClick={() => insertMarkdown('link')}
          className="toolbar-btn"
          title="링크"
        >
          🔗
        </button>
        
        {onImageUpload && (
          <>
            <div className="toolbar-separator" />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="toolbar-btn"
              title="이미지 업로드"
              disabled={isUploading}
            >
              {isUploading ? '⏳' : '📷'}
            </button>
          </>
        )}
      </div>

      {/* Editor */}
      <textarea
        ref={textareaRef}
        value={content}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="editor-textarea"
        rows={25}
      />

      {/* Hidden file input */}
      {onImageUpload && (
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      )}

      {/* Markdown help */}
      <div className="editor-help">
        <details>
          <summary>마크다운 도움말</summary>
          <div className="help-content">
            <p><strong>**굵게**</strong> | <em>*기울임*</em> | <code>`코드`</code></p>
            <p># 제목1 | ## 제목2 | ### 제목3</p>
            <p>- 목록 | 1. 번호목록 | {'>'} 인용문</p>
            <p>[링크](URL) | ![이미지](URL)</p>
          </div>
        </details>
      </div>

      <style>{`
        .markdown-editor {
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          overflow: hidden;
          background: white;
        }
        
        .editor-toolbar {
          display: flex;
          align-items: center;
          padding: 0.5rem;
          background: #f9fafb;
          border-bottom: 1px solid #e5e7eb;
          gap: 0.25rem;
          flex-wrap: wrap;
        }
        
        .toolbar-btn {
          padding: 0.25rem 0.5rem;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 0.25rem;
          cursor: pointer;
          font-size: 0.875rem;
          transition: all 0.2s;
          min-width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .toolbar-btn:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
        }
        
        .toolbar-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .toolbar-separator {
          width: 1px;
          height: 24px;
          background: #d1d5db;
          margin: 0 0.25rem;
        }
        
        .editor-textarea {
          width: 100%;
          padding: 1rem;
          border: none;
          outline: none;
          resize: vertical;
          min-height: 600px;
          font-family: inherit;
          font-size: 1rem;
          line-height: 1.5;
        }
        
        .editor-textarea::placeholder {
          color: #9ca3af;
        }
        
        .editor-help {
          padding: 0.5rem 1rem;
          background: #f9fafb;
          border-top: 1px solid #e5e7eb;
        }
        
        .editor-help summary {
          cursor: pointer;
          font-size: 0.875rem;
          color: #6b7280;
          user-select: none;
        }
        
        .help-content {
          margin-top: 0.5rem;
          font-size: 0.875rem;
          color: #6b7280;
        }
        
        .help-content p {
          margin: 0.25rem 0;
          font-family: monospace;
        }
      `}</style>
    </div>
  );
};

export default BlockNoteEditor;