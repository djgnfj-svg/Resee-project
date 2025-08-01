import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import { useCallback, useEffect } from 'react';

interface TipTapEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  className?: string;
}

const TipTapEditor: React.FC<TipTapEditorProps> = ({
  content,
  onChange,
  placeholder = '내용을 입력하세요. # 제목, **굵게**, *기울임*, 1. 목록 등이 바로 적용됩니다!',
  className = ''
}) => {

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
        link: {
          openOnClick: false,
          HTMLAttributes: {
            class: 'tiptap-link',
          },
        },
      }),
      Placeholder.configure({
        placeholder: placeholder,
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
    
    
    // 목록 처리 (개선)
    // 불릿 목록
    html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>(\n|$))+/g, (match) => {
      return '<ul>' + match.replace(/\n/g, '') + '</ul>';
    });
    
    // 번호 목록
    html = html.replace(/^(\d+)\. (.*$)/gm, '<li>$2</li>');
    html = html.replace(/(<li>.*<\/li>(\n|$))+/g, (match) => {
      // 이미 <ul>로 감싸져 있지 않은 경우에만 <ol>로 감싸기
      if (!match.includes('<ul>')) {
        return '<ol>' + match.replace(/\n/g, '') + '</ol>';
      }
      return match;
    });
    
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
    <div className={`border-2 border-gray-200 dark:border-gray-600 rounded-xl overflow-hidden bg-white dark:bg-gray-700 ${className}`}>
      {/* 툴바 */}
      <div className="flex flex-wrap items-center gap-1 p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-600">
        <div className="flex items-center gap-1">
          <button
            onClick={() => editor.commands.toggleBold()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('bold')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="굵게 (Ctrl+B)"
          >
            <strong>B</strong>
          </button>
          <button
            onClick={() => editor.commands.toggleItalic()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('italic')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="기울임 (Ctrl+I)"
          >
            <em>I</em>
          </button>
          <button
            onClick={() => editor.commands.toggleStrike()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('strike')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="취소선"
          >
            <s>S</s>
          </button>
          <button
            onClick={() => editor.commands.toggleCode()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('code')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="인라인 코드"
          >
            {'</>'}
          </button>
        </div>
        
        <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
          <button
            onClick={() => editor.commands.toggleHeading({ level: 1 })}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('heading', { level: 1 })
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="제목 1"
          >
            H1
          </button>
          <button
            onClick={() => editor.commands.toggleHeading({ level: 2 })}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('heading', { level: 2 })
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="제목 2"
          >
            H2
          </button>
          <button
            onClick={() => editor.commands.toggleHeading({ level: 3 })}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('heading', { level: 3 })
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="제목 3"
          >
            H3
          </button>
        </div>
        
        <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
          <button
            onClick={() => editor.commands.toggleBulletList()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('bulletList')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="불릿 목록"
          >
            •
          </button>
          <button
            onClick={() => editor.commands.toggleOrderedList()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('orderedList')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="번호 목록"
          >
            1.
          </button>
          <button
            onClick={() => editor.commands.toggleBlockquote()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('blockquote')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="인용문"
          >
            "
          </button>
        </div>
        
        <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
          <button
            onClick={() => editor.commands.toggleCodeBlock()}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('codeBlock')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="코드 블록"
          >
            {'{ }'}
          </button>
          <button
            onClick={addLink}
            className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
              editor.isActive('link')
                ? 'bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
            title="링크"
          >
            🔗
          </button>
        </div>
      </div>

      {/* 에디터 */}
      <EditorContent editor={editor} className="tiptap-content" />


      {/* 도움말 */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-600">
        <details className="text-sm">
          <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">마크다운 단축키</summary>
          <div className="mt-2 space-y-1 text-gray-700 dark:text-gray-300">
            <p><strong># 제목1</strong> | <strong>## 제목2</strong> | <strong>### 제목3</strong></p>
            <p><strong>**굵게**</strong> | <strong>*기울임*</strong> | <strong>~~취소선~~</strong></p>
            <p><strong>- 목록</strong> | <strong>1. 번호목록</strong> | <strong>{'>'} 인용문</strong></p>
            <p><strong>`코드`</strong> | <strong>```코드블록```</strong></p>
          </div>
        </details>
      </div>

      <style>{`
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

        .dark .tiptap-editor-content {
          color: #f3f4f6;
        }

        .tiptap-editor-content p.is-editor-empty:first-child::before {
          content: attr(data-placeholder);
          float: left;
          color: #9ca3af;
          font-style: italic;
          pointer-events: none;
          height: 0;
        }

        .dark .tiptap-editor-content p.is-editor-empty:first-child::before {
          color: #6b7280;
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

        .dark .tiptap-editor-content h1 {
          color: #f3f4f6;
          border-bottom-color: #374151;
        }

        .tiptap-editor-content h2 {
          font-size: 1.875rem;
          font-weight: 700;
          color: #1f2937;
          margin: 1.25rem 0 0.75rem 0;
          border-bottom: 1px solid #e5e7eb;
          padding-bottom: 0.25rem;
        }

        .dark .tiptap-editor-content h2 {
          color: #f3f4f6;
          border-bottom-color: #374151;
        }

        .tiptap-editor-content h3 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #1f2937;
          margin: 1rem 0 0.5rem 0;
        }

        .dark .tiptap-editor-content h3 {
          color: #f3f4f6;
        }

        /* 텍스트 스타일 */
        .tiptap-editor-content p {
          margin: 0.75rem 0;
          color: #374151;
        }

        .dark .tiptap-editor-content p {
          color: #d1d5db;
        }

        .tiptap-editor-content strong {
          font-weight: 700;
          color: #1f2937;
        }

        .dark .tiptap-editor-content strong {
          color: #f3f4f6;
        }

        .tiptap-editor-content em {
          font-style: italic;
          color: #374151;
        }

        .dark .tiptap-editor-content em {
          color: #d1d5db;
        }

        .tiptap-editor-content s {
          text-decoration: line-through;
          color: #6b7280;
        }

        .dark .tiptap-editor-content s {
          color: #9ca3af;
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

        .dark .tiptap-editor-content code {
          background: #374151;
          color: #f87171;
        }

        .tiptap-editor-content pre {
          background: #1e293b;
          color: #e2e8f0;
          padding: 1rem;
          border-radius: 0.5rem;
          overflow-x: auto;
          margin: 1rem 0;
        }

        .dark .tiptap-editor-content pre {
          background: #111827;
          color: #e5e7eb;
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
        .tiptap-editor-content ul {
          margin: 1rem 0;
          padding-left: 2rem;
          list-style-type: disc;
        }

        .tiptap-editor-content ol {
          margin: 1rem 0;
          padding-left: 2rem;
          list-style-type: decimal;
        }

        .tiptap-editor-content li {
          margin: 0.5rem 0;
          color: #374151;
        }

        .dark .tiptap-editor-content li {
          color: #d1d5db;
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

        .dark .tiptap-editor-content blockquote {
          background: #1f2937;
          color: #9ca3af;
          border-left-color: #60a5fa;
        }

        /* 링크 스타일 */
        .tiptap-editor-content a {
          color: #3b82f6;
          text-decoration: underline;
          text-decoration-color: #93c5fd;
        }

        .dark .tiptap-editor-content a {
          color: #60a5fa;
          text-decoration-color: #3b82f6;
        }

        .tiptap-editor-content a:hover {
          color: #1d4ed8;
          text-decoration-color: #3b82f6;
        }

        .dark .tiptap-editor-content a:hover {
          color: #93c5fd;
          text-decoration-color: #60a5fa;
        }

        /* 반응형 디자인 */
        @media (max-width: 640px) {
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