import { useEditor, EditorContent } from '@tiptap/react';
import { useEffect } from 'react';
import { createEditorExtensions, editorProps } from './editor/EditorConfig';
import { convertToMarkdown, convertFromMarkdown } from '../utils/markdown-converter';
import EditorStyles from './editor/EditorStyles';

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


  if (!editor) {
    return null;
  }

  return (
    <div className={`border border-gray-300 dark:border-gray-600 rounded-md overflow-hidden bg-white dark:bg-gray-700 ${className}`}>
      <EditorContent editor={editor} className="tiptap-content" />
      <EditorStyles />
    </div>
  );
};

export default TipTapEditor;