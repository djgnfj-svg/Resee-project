import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import { useCallback, useEffect, useState } from 'react';

interface TipTapEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  onImageUpload?: (file: File) => Promise<string>;
  className?: string;
}

const TipTapEditor: React.FC<TipTapEditorProps> = ({
  content,
  onChange,
  placeholder = '내용을 입력하세요. # 제목, **굵게**, *기울임*, 1. 목록 등이 바로 적용됩니다!',
  onImageUpload,
  className = ''
}) => {
  const [isUploading, setIsUploading] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // 마크다운 단축키 활성화
        heading: {
          levels: [1, 2, 3],
        },
        bulletList: {
          keepMarks: true,
          keepAttributes: false,
        },
        orderedList: {
          keepMarks: true,
          keepAttributes: false,
        },
      }),
      Placeholder.configure({
        placeholder: placeholder,
      }),
      Image.configure({
        inline: true,
        allowBase64: true,
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'tiptap-link',
        },
      }),
    ],
    content: content,
    editorProps: {
      attributes: {
        class: 'tiptap-editor-content',
      },
    },
    onUpdate: ({ editor }: any) => {
      // 마크다운 포맷으로 변환하여 전달
      const markdown = convertToMarkdown(editor.getHTML());
      onChange(markdown);
    },
  });

  // HTML을 마크다운으로 변환하는 함수
  const convertToMarkdown = useCallback((html: string): string => {
    // 간단한 HTML to Markdown 변환
    let markdown = html;
    
    // 제목 변환
    markdown = markdown.replace(/<h1[^>]*>(.*?)<\/h1>/g, '# $1');
    markdown = markdown.replace(/<h2[^>]*>(.*?)<\/h2>/g, '## $1');
    markdown = markdown.replace(/<h3[^>]*>(.*?)<\/h3>/g, '### $1');
    
    // 굵게, 기울임
    markdown = markdown.replace(/<strong[^>]*>(.*?)<\/strong>/g, '**$1**');
    markdown = markdown.replace(/<em[^>]*>(.*?)<\/em>/g, '*$1*');
    
    // 목록
    markdown = markdown.replace(/<ul[^>]*>(.*?)<\/ul>/gs, (match, content) => {
      return content.replace(/<li[^>]*>(.*?)<\/li>/g, '- $1');
    });
    markdown = markdown.replace(/<ol[^>]*>(.*?)<\/ol>/gs, (match, content) => {
      let counter = 1;
      return content.replace(/<li[^>]*>(.*?)<\/li>/g, () => `${counter++}. $1`);
    });
    
    // 인용문
    markdown = markdown.replace(/<blockquote[^>]*>(.*?)<\/blockquote>/gs, '> $1');
    
    // 코드
    markdown = markdown.replace(/<code[^>]*>(.*?)<\/code>/g, '`$1`');
    markdown = markdown.replace(/<pre[^>]*><code[^>]*>(.*?)<\/code><\/pre>/gs, '```\n$1\n```');
    
    // 링크
    markdown = markdown.replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/g, '[$2]($1)');
    
    // 이미지
    markdown = markdown.replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/g, '![$2]($1)');
    
    // 줄바꿈
    markdown = markdown.replace(/<br\s*\/?>/g, '\n');
    markdown = markdown.replace(/<\/p>\s*<p[^>]*>/g, '\n\n');
    markdown = markdown.replace(/<p[^>]*>/g, '');
    markdown = markdown.replace(/<\/p>/g, '');
    
    // HTML 태그 제거
    markdown = markdown.replace(/<[^>]*>/g, '');
    
    // HTML 엔티티 디코딩
    markdown = markdown.replace(/&amp;/g, '&');
    markdown = markdown.replace(/&lt;/g, '<');
    markdown = markdown.replace(/&gt;/g, '>');
    markdown = markdown.replace(/&quot;/g, '"');
    markdown = markdown.replace(/&#39;/g, "'");
    
    return markdown.trim();
  }, []);

  // 마크다운을 HTML로 변환하는 함수
  const convertFromMarkdown = useCallback((markdown: string): string => {
    if (!markdown) return '';
    
    let html = markdown;
    
    // 제목 변환
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // 굵게, 기울임
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // 코드
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    html = html.replace(/```\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
    
    // 링크
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
    
    // 이미지
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1">');
    
    // 목록 (간단화)
    html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.*$)/gm, '<li>$2</li>');
    
    // 인용문
    html = html.replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>');
    
    // 줄바꿈
    html = html.replace(/\n/g, '<br>');
    
    return html;
  }, []);

  // content가 변경될 때 에디터 업데이트
  useEffect(() => {
    if (editor && content !== undefined) {
      const currentContent = convertToMarkdown(editor.getHTML());
      if (currentContent !== content) {
        const htmlContent = convertFromMarkdown(content);
        editor.commands.setContent(htmlContent);
      }
    }
  }, [content, editor, convertToMarkdown, convertFromMarkdown]);

  // 이미지 업로드 핸들러
  const handleImageUpload = useCallback(async (file: File) => {
    if (!onImageUpload || !editor) return;
    
    setIsUploading(true);
    try {
      const imageUrl = await onImageUpload(file);
      editor.commands.setImage({ src: imageUrl, alt: file.name });
    } catch (error) {
      console.error('이미지 업로드 실패:', error);
      alert('이미지 업로드에 실패했습니다.');
    } finally {
      setIsUploading(false);
    }
  }, [onImageUpload, editor]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleImageUpload(file);
    }
    e.target.value = '';
  }, [handleImageUpload]);

  const addImage = useCallback(() => {
    const url = window.prompt('이미지 URL을 입력하세요:');
    if (url && editor) {
      editor.commands.setImage({ src: url });
    }
  }, [editor]);

  const addLink = useCallback(() => {
    const url = window.prompt('링크 URL을 입력하세요:');
    if (url && editor) {
      editor.commands.setLink({ href: url });
    }
  }, [editor]);

  if (!editor) {
    return null;
  }

  return (
    <div className={`tiptap-editor ${className}`}>
      {/* 툴바 */}
      <div className="tiptap-toolbar">
        <div className="toolbar-group">
          <button
            onClick={() => editor.commands.toggleBold()}
            className={`toolbar-btn ${editor.isActive('bold') ? 'active' : ''}`}
            title="굵게 (Ctrl+B)"
          >
            <strong>B</strong>
          </button>
          <button
            onClick={() => editor.commands.toggleItalic()}
            className={`toolbar-btn ${editor.isActive('italic') ? 'active' : ''}`}
            title="기울임 (Ctrl+I)"
          >
            <em>I</em>
          </button>
          <button
            onClick={() => editor.commands.toggleStrike()}
            className={`toolbar-btn ${editor.isActive('strike') ? 'active' : ''}`}
            title="취소선"
          >
            <s>S</s>
          </button>
          <button
            onClick={() => editor.commands.toggleCode()}
            className={`toolbar-btn ${editor.isActive('code') ? 'active' : ''}`}
            title="인라인 코드"
          >
            {'</>'}
          </button>
        </div>
        
        <div className="toolbar-group">
          <button
            onClick={() => editor.commands.toggleHeading({ level: 1 })}
            className={`toolbar-btn ${editor.isActive('heading', { level: 1 }) ? 'active' : ''}`}
            title="제목 1"
          >
            H1
          </button>
          <button
            onClick={() => editor.commands.toggleHeading({ level: 2 })}
            className={`toolbar-btn ${editor.isActive('heading', { level: 2 }) ? 'active' : ''}`}
            title="제목 2"
          >
            H2
          </button>
          <button
            onClick={() => editor.commands.toggleHeading({ level: 3 })}
            className={`toolbar-btn ${editor.isActive('heading', { level: 3 }) ? 'active' : ''}`}
            title="제목 3"
          >
            H3
          </button>
        </div>
        
        <div className="toolbar-group">
          <button
            onClick={() => editor.commands.toggleBulletList()}
            className={`toolbar-btn ${editor.isActive('bulletList') ? 'active' : ''}`}
            title="불릿 목록"
          >
            •
          </button>
          <button
            onClick={() => editor.commands.toggleOrderedList()}
            className={`toolbar-btn ${editor.isActive('orderedList') ? 'active' : ''}`}
            title="번호 목록"
          >
            1.
          </button>
          <button
            onClick={() => editor.commands.toggleBlockquote()}
            className={`toolbar-btn ${editor.isActive('blockquote') ? 'active' : ''}`}
            title="인용문"
          >
            "
          </button>
        </div>
        
        <div className="toolbar-group">
          <button
            onClick={() => editor.commands.toggleCodeBlock()}
            className={`toolbar-btn ${editor.isActive('codeBlock') ? 'active' : ''}`}
            title="코드 블록"
          >
            {'{ }'}
          </button>
          <button
            onClick={addLink}
            className={`toolbar-btn ${editor.isActive('link') ? 'active' : ''}`}
            title="링크"
          >
            🔗
          </button>
          <button
            onClick={addImage}
            className="toolbar-btn"
            title="이미지 URL"
          >
            🖼️
          </button>
          {onImageUpload && (
            <button
              onClick={() => document.getElementById('image-upload')?.click()}
              className="toolbar-btn"
              title="이미지 업로드"
              disabled={isUploading}
            >
              {isUploading ? '⏳' : '📷'}
            </button>
          )}
        </div>
      </div>

      {/* 에디터 */}
      <EditorContent editor={editor} className="tiptap-content" />

      {/* 숨겨진 파일 입력 */}
      {onImageUpload && (
        <input
          id="image-upload"
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      )}

      {/* 도움말 */}
      <div className="tiptap-help">
        <details>
          <summary>마크다운 단축키</summary>
          <div className="help-content">
            <p><strong># 제목1</strong> | <strong>## 제목2</strong> | <strong>### 제목3</strong></p>
            <p><strong>**굵게**</strong> | <strong>*기울임*</strong> | <strong>~~취소선~~</strong></p>
            <p><strong>- 목록</strong> | <strong>1. 번호목록</strong> | <strong>{'>'} 인용문</strong></p>
            <p><strong>`코드`</strong> | <strong>```코드블록```</strong></p>
          </div>
        </details>
      </div>

      <style>{`
        .tiptap-editor {
          border: 1px solid #e5e7eb;
          border-radius: 0.75rem;
          background: white;
          overflow: hidden;
          min-height: 400px;
        }

        .tiptap-toolbar {
          display: flex;
          align-items: center;
          padding: 0.5rem;
          background: #f9fafb;
          border-bottom: 1px solid #e5e7eb;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .toolbar-group {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          border-right: 1px solid #e5e7eb;
          padding-right: 0.5rem;
        }

        .toolbar-group:last-child {
          border-right: none;
          padding-right: 0;
        }

        .toolbar-btn {
          padding: 0.375rem 0.75rem;
          border: 1px solid #d1d5db;
          background: white;
          border-radius: 0.375rem;
          cursor: pointer;
          font-size: 0.875rem;
          transition: all 0.2s;
          min-width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 500;
        }

        .toolbar-btn:hover {
          background: #f3f4f6;
          border-color: #9ca3af;
        }

        .toolbar-btn.active {
          background: #3b82f6;
          border-color: #3b82f6;
          color: white;
        }

        .toolbar-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .tiptap-content {
          min-height: 350px;
        }

        .tiptap-editor-content {
          min-height: 350px;
          padding: 1.5rem;
          outline: none;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 1rem;
          line-height: 1.6;
          color: #1f2937;
        }

        .tiptap-editor-content p.is-editor-empty:first-child::before {
          content: attr(data-placeholder);
          float: left;
          color: #9ca3af;
          font-style: italic;
          pointer-events: none;
          height: 0;
        }

        /* 제목 스타일 */
        .tiptap-editor-content h1 {
          font-size: 2.25rem;
          font-weight: 800;
          color: #1f2937;
          margin: 1.5rem 0 1rem 0;
          border-bottom: 2px solid #e5e7eb;
          padding-bottom: 0.5rem;
        }

        .tiptap-editor-content h2 {
          font-size: 1.875rem;
          font-weight: 700;
          color: #1f2937;
          margin: 1.25rem 0 0.75rem 0;
          border-bottom: 1px solid #e5e7eb;
          padding-bottom: 0.25rem;
        }

        .tiptap-editor-content h3 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #1f2937;
          margin: 1rem 0 0.5rem 0;
        }

        /* 텍스트 스타일 */
        .tiptap-editor-content p {
          margin: 0.75rem 0;
          color: #374151;
        }

        .tiptap-editor-content strong {
          font-weight: 700;
          color: #1f2937;
        }

        .tiptap-editor-content em {
          font-style: italic;
          color: #374151;
        }

        .tiptap-editor-content s {
          text-decoration: line-through;
          color: #6b7280;
        }

        .tiptap-editor-content code {
          background: #f1f5f9;
          color: #dc2626;
          padding: 0.125rem 0.375rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-family: 'Monaco', 'Menlo', monospace;
          font-weight: 500;
        }

        .tiptap-editor-content pre {
          background: #1e293b;
          color: #e2e8f0;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 1rem 0;
        }

        .tiptap-editor-content pre code {
          background: none;
          color: inherit;
          padding: 0;
          font-family: 'Monaco', 'Menlo', monospace;
          font-size: 0.875rem;
          line-height: 1.4;
        }

        /* 목록 스타일 */
        .tiptap-editor-content ul, 
        .tiptap-editor-content ol {
          margin: 1rem 0;
          padding-left: 2rem;
        }

        .tiptap-editor-content li {
          margin: 0.5rem 0;
          color: #374151;
        }

        .tiptap-editor-content li p {
          margin: 0;
        }

        /* 인용문 스타일 */
        .tiptap-editor-content blockquote {
          border-left: 4px solid #3b82f6;
          background: #f8fafc;
          padding: 1rem 1.5rem;
          margin: 1rem 0;
          font-style: italic;
          color: #475569;
        }

        /* 링크 스타일 */
        .tiptap-editor-content a {
          color: #3b82f6;
          text-decoration: underline;
          text-decoration-color: #93c5fd;
        }

        .tiptap-editor-content a:hover {
          color: #1d4ed8;
          text-decoration-color: #3b82f6;
        }

        /* 이미지 스타일 */
        .tiptap-editor-content img {
          max-width: 100%;
          height: auto;
          border-radius: 0.5rem;
          margin: 1rem 0;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* 도움말 */
        .tiptap-help {
          padding: 0.75rem 1.5rem;
          background: #f9fafb;
          border-top: 1px solid #e5e7eb;
        }

        .tiptap-help summary {
          cursor: pointer;
          font-size: 0.875rem;
          color: #6b7280;
          user-select: none;
          font-weight: 500;
        }

        .help-content {
          margin-top: 0.75rem;
          font-size: 0.875rem;
          color: #6b7280;
        }

        .help-content p {
          margin: 0.25rem 0;
          font-family: monospace;
        }

        /* 포커스 상태 */
        .tiptap-editor:focus-within {
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        /* 반응형 디자인 */
        @media (max-width: 640px) {
          .tiptap-toolbar {
            padding: 0.375rem;
            gap: 0.25rem;
          }
          
          .toolbar-btn {
            min-width: 32px;
            height: 32px;
            padding: 0.25rem 0.5rem;
            font-size: 0.8rem;
          }
          
          .tiptap-editor-content {
            padding: 1rem;
          }
          
          .tiptap-editor-content h1 {
            font-size: 1.875rem;
          }
          
          .tiptap-editor-content h2 {
            font-size: 1.5rem;
          }
          
          .tiptap-editor-content h3 {
            font-size: 1.25rem;
          }
        }
      `}</style>
    </div>
  );
};

export default TipTapEditor;