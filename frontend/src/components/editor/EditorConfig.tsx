import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';

export const createEditorExtensions = (placeholder: string) => [
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
];

export const editorProps = {
  attributes: {
    class: 'tiptap-editor-content',
  },
};