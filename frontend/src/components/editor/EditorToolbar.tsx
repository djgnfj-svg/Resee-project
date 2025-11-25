import React from 'react';
import { Editor } from '@tiptap/react';

interface EditorToolbarProps {
  editor: Editor | null;
  addLink: () => void;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({ editor, addLink }) => {
  if (!editor) return null;

  // 공통 버튼 스타일 (터치 타겟 44px 최소, 접근성 개선)
  const getButtonClass = (isActive: boolean) =>
    `min-w-[44px] min-h-[44px] px-3 py-2 text-sm font-medium rounded transition-colors inline-flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1 ${
      isActive
        ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300'
        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
    }`;

  return (
    <div className="flex flex-wrap items-center gap-2 p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-600">
      {/* Text formatting buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => editor.commands.toggleBold()}
          className={getButtonClass(editor.isActive('bold'))}
          title="굵게 (Ctrl+B)"
          aria-label="굵게"
          aria-pressed={editor.isActive('bold')}
        >
          <strong>B</strong>
        </button>
        <button
          onClick={() => editor.commands.toggleItalic()}
          className={getButtonClass(editor.isActive('italic'))}
          title="기울임 (Ctrl+I)"
          aria-label="기울임"
          aria-pressed={editor.isActive('italic')}
        >
          <em>I</em>
        </button>
        <button
          onClick={() => editor.commands.toggleStrike()}
          className={getButtonClass(editor.isActive('strike'))}
          title="취소선"
          aria-label="취소선"
          aria-pressed={editor.isActive('strike')}
        >
          <s>S</s>
        </button>
        <button
          onClick={() => editor.commands.toggleCode()}
          className={getButtonClass(editor.isActive('code'))}
          title="인라인 코드"
          aria-label="인라인 코드"
          aria-pressed={editor.isActive('code')}
        >
          {'</>'}
        </button>
      </div>

      {/* Heading buttons */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
        <button
          onClick={() => editor.commands.toggleHeading({ level: 1 })}
          className={getButtonClass(editor.isActive('heading', { level: 1 }))}
          title="제목 1"
          aria-label="제목 1"
          aria-pressed={editor.isActive('heading', { level: 1 })}
        >
          H1
        </button>
        <button
          onClick={() => editor.commands.toggleHeading({ level: 2 })}
          className={getButtonClass(editor.isActive('heading', { level: 2 }))}
          title="제목 2"
          aria-label="제목 2"
          aria-pressed={editor.isActive('heading', { level: 2 })}
        >
          H2
        </button>
        <button
          onClick={() => editor.commands.toggleHeading({ level: 3 })}
          className={getButtonClass(editor.isActive('heading', { level: 3 }))}
          title="제목 3"
          aria-label="제목 3"
          aria-pressed={editor.isActive('heading', { level: 3 })}
        >
          H3
        </button>
      </div>

      {/* List and quote buttons */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
        <button
          onClick={() => editor.commands.toggleBulletList()}
          className={getButtonClass(editor.isActive('bulletList'))}
          title="불릿 목록"
          aria-label="불릿 목록"
          aria-pressed={editor.isActive('bulletList')}
        >
          •
        </button>
        <button
          onClick={() => editor.commands.toggleOrderedList()}
          className={getButtonClass(editor.isActive('orderedList'))}
          title="번호 목록"
          aria-label="번호 목록"
          aria-pressed={editor.isActive('orderedList')}
        >
          1.
        </button>
        <button
          onClick={() => editor.commands.toggleBlockquote()}
          className={getButtonClass(editor.isActive('blockquote'))}
          title="인용문"
          aria-label="인용문"
          aria-pressed={editor.isActive('blockquote')}
        >
          "
        </button>
      </div>

      {/* Code block and link buttons */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
        <button
          onClick={() => editor.commands.toggleCodeBlock()}
          className={getButtonClass(editor.isActive('codeBlock'))}
          title="코드 블록"
          aria-label="코드 블록"
          aria-pressed={editor.isActive('codeBlock')}
        >
          {'{ }'}
        </button>
        <button
          onClick={addLink}
          className={getButtonClass(editor.isActive('link'))}
          title="링크"
          aria-label="링크 추가"
          aria-pressed={editor.isActive('link')}
        >
          🔗
        </button>
      </div>
    </div>
  );
};

export default EditorToolbar;
