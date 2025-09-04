import { useEditor, EditorContent } from '@tiptap/react';
import { useCallback, useEffect } from 'react';
import { createEditorExtensions, editorProps } from './editor/EditorConfig';
import { convertToMarkdown, convertFromMarkdown } from '../utils/markdown-converter';
import EditorToolbar from './editor/EditorToolbar';
import EditorStyles from './editor/EditorStyles';
import EditorHelp from './editor/EditorHelp';

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
    extensions: createEditorExtensions(placeholder),
    content: content,
    editorProps,
    onUpdate: ({ editor }: any) => {
      const markdown = convertToMarkdown(editor.getHTML());
      onChange(markdown);
    },
  });

  useEffect(() => {
    if (editor && content !== undefined) {
      const currentContent = convertToMarkdown(editor.getHTML());
      if (currentContent !== content) {
        const htmlContent = convertFromMarkdown(content);
        editor.commands.setContent(htmlContent);
      }
    }
  }, [content, editor]);

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
      <EditorToolbar editor={editor} addLink={addLink} />
      <EditorContent editor={editor} className="tiptap-content" />
      <EditorHelp />
      <EditorStyles />
    </div>
  );
};

export default TipTapEditor;