import React, { useCallback, useEffect, useState } from 'react';
import { useEditor, EditorContent, Editor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import CharacterCount from '@tiptap/extension-character-count';
import Typography from '@tiptap/extension-typography';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import Dropcursor from '@tiptap/extension-dropcursor';
import Gapcursor from '@tiptap/extension-gapcursor';
import MarkdownShortcuts from './extensions/MarkdownShortcuts';
import ImageUploadDropzone from './ImageUploadDropzone';

interface NotionEditorProps {
  content: string;
  onChange: (content: string) => void;
  placeholder?: string;
  onImageUpload?: (file: File) => Promise<string>;
  className?: string;
}

interface SlashCommand {
  title: string;
  description: string;
  icon: string;
  command: (editor: Editor) => void;
}

const NotionEditor: React.FC<NotionEditorProps> = ({
  content,
  onChange,
  placeholder = '여기에 내용을 입력하거나 "/"를 입력하여 명령어를 확인하세요...',
  onImageUpload,
  className = ''
}) => {
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashMenuPosition, setSlashMenuPosition] = useState({ x: 0, y: 0 });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);

  const slashCommands: SlashCommand[] = [
    {
      title: '제목 1',
      description: '큰 제목',
      icon: 'H1',
      command: (editor) => editor.chain().focus().toggleHeading({ level: 1 }).run()
    },
    {
      title: '제목 2', 
      description: '중간 제목',
      icon: 'H2',
      command: (editor) => editor.chain().focus().toggleHeading({ level: 2 }).run()
    },
    {
      title: '제목 3',
      description: '작은 제목', 
      icon: 'H3',
      command: (editor) => editor.chain().focus().toggleHeading({ level: 3 }).run()
    },
    {
      title: '불릿 리스트',
      description: '간단한 불릿 목록',
      icon: '•',
      command: (editor) => editor.chain().focus().toggleBulletList().run()
    },
    {
      title: '번호 리스트',
      description: '번호가 있는 목록',
      icon: '1.',
      command: (editor) => editor.chain().focus().toggleOrderedList().run()
    },
    {
      title: '할 일 목록',
      description: '체크박스가 있는 목록',
      icon: '☑',
      command: (editor) => editor.chain().focus().toggleTaskList().run()
    },
    {
      title: '인용구',
      description: '인용 블록',
      icon: '"',
      command: (editor) => editor.chain().focus().toggleBlockquote().run()
    },
    {
      title: '코드 블록',
      description: '코드를 위한 블록',
      icon: '</>',
      command: (editor) => editor.chain().focus().toggleCodeBlock().run()
    },
    {
      title: '구분선',
      description: '수평선 추가',
      icon: '—',
      command: (editor) => editor.chain().focus().setHorizontalRule().run()
    }
  ];

  const filteredCommands = slashCommands.filter(command =>
    command.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    command.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const editor = useEditor({
    extensions: [
      StarterKit,
      MarkdownShortcuts,
      Typography,
      Image.configure({
        inline: false,
        HTMLAttributes: {
          class: 'rounded-lg max-w-full h-auto my-4',
        },
      }),
      Link.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: 'text-blue-600 hover:text-blue-800 underline cursor-pointer',
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
      CharacterCount.configure({
        limit: 10000,
      }),
      TaskList,
      TaskItem.configure({
        nested: true,
        HTMLAttributes: {
          class: 'flex items-start my-1',
        },
      }),
      Dropcursor.configure({
        color: '#3B82F6',
        width: 2,
      }),
      Gapcursor,
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    onCreate: ({ editor }) => {
      // Focus the editor when created
      editor.commands.focus();
    },
    onSelectionUpdate: ({ editor }) => {
      const { selection } = editor.state;
      const { $from } = selection;
      
      // Check if we're in a position where slash command should show
      const currentNode = $from.parent;
      const nodeText = currentNode.textContent || '';
      
      // Show slash menu when typing "/" at the beginning of a line or after whitespace
      if (nodeText === '/' || (nodeText.includes('/') && nodeText.trim().startsWith('/'))) {
        const coords = editor.view.coordsAtPos($from.pos);
        
        // Ensure menu stays within viewport
        const menuWidth = 256; // w-64 = 16rem = 256px
        const menuHeight = 320; // max-h-80 = 20rem = 320px
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let x = coords.left;
        let y = coords.bottom + 5;
        
        // Adjust horizontal position if menu would overflow
        if (x + menuWidth > viewportWidth) {
          x = viewportWidth - menuWidth - 10;
        }
        
        // Adjust vertical position if menu would overflow
        if (y + menuHeight > viewportHeight) {
          y = coords.top - menuHeight - 5;
        }
        
        setSlashMenuPosition({ x, y });
        setShowSlashMenu(true);
        
        // Extract search query after the slash
        const slashIndex = nodeText.lastIndexOf('/');
        const query = slashIndex >= 0 ? nodeText.slice(slashIndex + 1) : '';
        setSearchQuery(query);
        setSelectedCommandIndex(0);
      } else {
        setShowSlashMenu(false);
        setSearchQuery('');
      }
    },
  });

  const executeSlashCommand = useCallback((command: SlashCommand) => {
    if (!editor) return;
    
    // Delete the slash and search text
    const { selection } = editor.state;
    const { $from } = selection;
    const currentNode = $from.parent;
    
    if (currentNode.textContent?.startsWith('/')) {
      const slashLength = currentNode.textContent.length;
      editor.chain()
        .deleteRange({ 
          from: $from.pos - slashLength, 
          to: $from.pos 
        })
        .run();
    }
    
    // Execute the command
    command.command(editor);
    setShowSlashMenu(false);
    setSearchQuery('');
  }, [editor]);

  const addImage = useCallback(async (file?: File) => {
    if (!editor || !onImageUpload) return;
    
    if (file) {
      // Direct file upload (for drag & drop)
      try {
        const url = await onImageUpload(file);
        editor.chain().focus().setImage({ src: url }).run();
        return url;
      } catch (error) {
        console.error('Image upload failed:', error);
        throw error;
      }
    } else {
      // File picker
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (file) {
          try {
            const url = await onImageUpload(file);
            editor.chain().focus().setImage({ src: url }).run();
          } catch (error) {
            console.error('Image upload failed:', error);
          }
        }
      };
      input.click();
    }
  }, [editor, onImageUpload]);

  // Handle keyboard navigation for slash menu
  useEffect(() => {
    if (!showSlashMenu || !editor) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if the editor is focused
      if (!editor.isFocused) return;
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedCommandIndex(prev => 
          prev < filteredCommands.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedCommandIndex(prev => 
          prev > 0 ? prev - 1 : filteredCommands.length - 1
        );
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[selectedCommandIndex]) {
          executeSlashCommand(filteredCommands[selectedCommandIndex]);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowSlashMenu(false);
        setSearchQuery('');
      }
    };

    // Attach to editor view instead of document
    editor.view.dom.addEventListener('keydown', handleKeyDown);
    return () => editor.view.dom.removeEventListener('keydown', handleKeyDown);
  }, [showSlashMenu, filteredCommands, selectedCommandIndex, executeSlashCommand, editor]);

  // Floating toolbar for text selection
  const FloatingToolbar = () => {
    const [show, setShow] = useState(false);
    const [position, setPosition] = useState({ x: 0, y: 0 });

    useEffect(() => {
      if (!editor) return;

      const updateToolbar = () => {
        const { selection } = editor.state;
        const { empty } = selection;

        if (empty) {
          setShow(false);
          return;
        }

        const { view } = editor;
        const { from, to } = selection;
        const start = view.coordsAtPos(from);
        const end = view.coordsAtPos(to);

        setPosition({
          x: (start.left + end.left) / 2,
          y: start.top - 10
        });
        setShow(true);
      };

      const cleanup = () => {
        editor.off('selectionUpdate', updateToolbar);
        editor.off('transaction', updateToolbar);
      };
      
      editor.on('selectionUpdate', updateToolbar);
      editor.on('transaction', updateToolbar);

      return cleanup;
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    if (!show || !editor) return null;

    return (
      <div 
        className="fixed z-50 bg-gray-900 text-white rounded-lg shadow-lg px-2 py-1 flex items-center space-x-1"
        style={{
          left: position.x,
          top: position.y,
          transform: 'translate(-50%, -100%)'
        }}
      >
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${
            editor.isActive('bold') ? 'bg-gray-700' : ''
          }`}
          title="굵게"
        >
          <span className="font-bold text-sm">B</span>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${
            editor.isActive('italic') ? 'bg-gray-700' : ''
          }`}
          title="기울임"
        >
          <span className="italic text-sm">I</span>
        </button>
        <button
          onClick={() => editor.chain().focus().toggleCode().run()}
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${
            editor.isActive('code') ? 'bg-gray-700' : ''
          }`}
          title="코드"
        >
          <span className="text-sm font-mono">&lt;&gt;</span>
        </button>
        <div className="w-px h-4 bg-gray-600 mx-1" />
        <button
          onClick={() => {
            const url = window.prompt('링크 URL을 입력하세요:');
            if (url) {
              editor.chain().focus().setLink({ href: url }).run();
            }
          }}
          className={`p-1.5 rounded hover:bg-gray-700 transition-colors ${
            editor.isActive('link') ? 'bg-gray-700' : ''
          }`}
          title="링크"
        >
          <span className="text-sm">🔗</span>
        </button>
      </div>
    );
  };

  if (!editor) return null;

  return (
    <ImageUploadDropzone onImageUpload={onImageUpload ? addImage : async () => ''} className={className}>
      <div className="relative w-full">
      {/* Slash Command Menu */}
      {showSlashMenu && (
        <div 
          className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg py-2 w-64 max-h-80 overflow-hidden"
          style={{
            left: slashMenuPosition.x,
            top: slashMenuPosition.y,
          }}
        >
          <div className="px-3 py-2 text-xs text-gray-500 border-b border-gray-100">
            명령어 선택
          </div>
          <div className="max-h-64 overflow-y-auto">
            {filteredCommands.map((command, index) => (
              <button
                key={command.title}
                onClick={() => executeSlashCommand(command)}
                className={`w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center space-x-3 transition-colors ${
                  index === selectedCommandIndex ? 'bg-blue-50 border-r-2 border-blue-500' : ''
                }`}
              >
                <span className="w-8 h-8 flex items-center justify-center bg-gray-100 rounded text-sm font-medium">
                  {command.icon}
                </span>
                <div className="flex-1">
                  <div className="font-medium text-sm text-gray-900">{command.title}</div>
                  <div className="text-xs text-gray-500">{command.description}</div>
                </div>
              </button>
            ))}
            {filteredCommands.length === 0 && (
              <div className="px-3 py-2 text-sm text-gray-500">
                명령어를 찾을 수 없습니다
              </div>
            )}
          </div>
        </div>
      )}

      {/* Floating Toolbar */}
      <FloatingToolbar />

      {/* Editor Content */}
      <div className="notion-editor bg-white rounded-lg border border-gray-200 overflow-hidden min-h-[400px] relative">
        <div className="p-6">
          <EditorContent
            editor={editor}
            className="prose prose-lg max-w-none focus:outline-none min-h-[300px]"
          />
        </div>
        
        {/* Footer */}
        <div className="border-t border-gray-200 bg-gray-50 px-6 py-3 text-sm text-gray-500 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <span>💡 <strong>/</strong>를 입력하여 명령어 메뉴 열기</span>
            <span>•</span>
            <span><strong>**텍스트**</strong>로 굵게</span>
            <span>•</span>
            <span><strong>*텍스트*</strong>로 기울임</span>
          </div>
          <div>
            {editor.storage.characterCount.characters()}/{editor.storage.characterCount.limit} 문자
          </div>
        </div>
      </div>

        {/* Hidden image upload button */}
        {onImageUpload && (
          <div className="mt-4">
            <button
              type="button"
              onClick={() => addImage()}
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <span className="mr-2">📷</span>
              이미지 추가
            </button>
          </div>
        )}
      </div>
    </ImageUploadDropzone>
  );
};

export default NotionEditor;