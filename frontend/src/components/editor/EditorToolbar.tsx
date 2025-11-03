import React from 'react';
import { Editor } from '@tiptap/react';

interface EditorToolbarProps {
  editor: Editor | null;
  addLink: () => void;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({ editor, addLink }) => {
  if (!editor) return null;

  return (
    <div className="flex flex-wrap items-center gap-1 p-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-600">
      {/* Text formatting buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => editor.commands.toggleBold()}
          className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
            editor.isActive('bold')
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title="인라인 코드"
        >
          {'</>'}
        </button>
      </div>
      
      {/* Heading buttons */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
        <button
          onClick={() => editor.commands.toggleHeading({ level: 1 })}
          className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
            editor.isActive('heading', { level: 1 })
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title="제목 3"
        >
          H3
        </button>
      </div>
      
      {/* List and quote buttons */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
        <button
          onClick={() => editor.commands.toggleBulletList()}
          className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
            editor.isActive('bulletList')
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title="인용문"
        >
          "
        </button>
      </div>
      
      {/* Code block and link buttons */}
      <div className="flex items-center gap-1 ml-2 pl-2 border-l border-gray-300 dark:border-gray-600">
        <button
          onClick={() => editor.commands.toggleCodeBlock()}
          className={`px-2 py-1 text-sm font-medium rounded transition-colors ${
            editor.isActive('codeBlock')
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
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
              ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          title="링크"
        >
          🔗
        </button>
      </div>
    </div>
  );
};

export default EditorToolbar;