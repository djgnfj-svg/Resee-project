import React from 'react';

const EditorStyles: React.FC = () => (
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
);

export default EditorStyles;