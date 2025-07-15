import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import CharacterCount from '@tiptap/extension-character-count';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import { contentAPI } from '../utils/api';
import { Category, Tag } from '../types';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  tag_ids?: number[];
  priority: 'low' | 'medium' | 'high';
}

interface ContentFormProps {
  onSubmit: (data: ContentFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  initialData?: Partial<ContentFormData>;
}

const ContentForm: React.FC<ContentFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData
}) => {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors } } = useForm<ContentFormData>({
    defaultValues: {
      priority: 'medium',
      ...initialData
    }
  });

  const [selectedTags, setSelectedTags] = useState<number[]>(initialData?.tag_ids || []);
  const [content, setContent] = useState<string>(initialData?.content || '');
  const [showNewCategoryForm, setShowNewCategoryForm] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDescription, setNewCategoryDescription] = useState('');
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [autoSaveStatus, setAutoSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  
  const editor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder: 'Notion처럼 /를 입력하거나 마크다운 문법을 사용하세요...'
      }),
      CharacterCount,
      Link.configure({
        openOnClick: false,
      }),
      Image.configure({
        HTMLAttributes: {
          class: 'rounded-lg max-w-full h-auto',
        },
      }),
      Table.configure({
        resizable: true,
      }),
      TableRow,
      TableHeader,
      TableCell,
    ],
    content: content,
    onUpdate: ({ editor }) => {
      setContent(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'tiptap-editor min-h-[700px] p-8 focus:outline-none text-gray-900 leading-relaxed prose prose-lg max-w-none',
      },
    },
  });
  
  // Update editor content when initialData changes
  React.useEffect(() => {
    if (editor && initialData?.content !== undefined) {
      editor.commands.setContent(initialData.content);
    }
  }, [editor, initialData?.content]);

  // Fetch categories and tags
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(res => res.results || res),
  });

  const { data: tags = [] } = useQuery<Tag[]>({
    queryKey: ['tags'],
    queryFn: () => contentAPI.getTags().then(res => res.results || res),
  });

  // Create category mutation
  const createCategoryMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) => 
      contentAPI.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setShowNewCategoryForm(false);
      setNewCategoryName('');
      setNewCategoryDescription('');
    },
  });

  const handleTagToggle = (tagId: number) => {
    setSelectedTags(prev => 
      prev.includes(tagId) 
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const onFormSubmit = (data: ContentFormData) => {
    if (!content.trim()) {
      alert('내용을 입력해주세요.');
      return;
    }
    
    console.log('ContentForm 제출 데이터:', {
      ...data,
      content: content,
      tag_ids: selectedTags
    });
    onSubmit({
      ...data,
      content: content,
      tag_ids: selectedTags
    });
  };

  const handleCreateCategory = () => {
    if (newCategoryName.trim()) {
      createCategoryMutation.mutate({
        name: newCategoryName.trim(),
        description: newCategoryDescription.trim()
      });
    }
  };

  const handleImageUpload = async (file: File) => {
    setIsUploadingImage(true);
    try {
      const response = await contentAPI.uploadImage(file);
      
      // 이미지를 에디터에 삽입
      editor?.chain().focus().setImage({ src: response.url }).run();
      
      console.log('이미지 업로드 성공:', response);
    } catch (error) {
      console.error('이미지 업로드 실패:', error);
      alert('이미지 업로드에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsUploadingImage(false);
    }
  };

  const handleImageButtonClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      if (file) {
        handleImageUpload(file);
      }
    };
    input.click();
  };

  // Auto-save functionality
  useEffect(() => {
    if (!content || content.length < 10) return;
    
    const autoSaveTimer = setTimeout(() => {
      setAutoSaveStatus('saving');
      const draftData = {
        title: '',
        content,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('contentDraft', JSON.stringify(draftData));
      setAutoSaveStatus('saved');
      setLastSaved(new Date());
    }, 2000);

    return () => clearTimeout(autoSaveTimer);
  }, [content]);

  // Load draft on mount
  useEffect(() => {
    if (!initialData) {
      const draft = localStorage.getItem('contentDraft');
      if (draft) {
        try {
          const draftData = JSON.parse(draft);
          setContent(draftData.content || '');
          setLastSaved(new Date(draftData.timestamp));
        } catch (error) {
          console.error('Failed to load draft:', error);
        }
      }
    }
  }, [initialData]);

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-8 py-6">
            <h2 className="text-2xl font-bold text-white">
              {initialData ? '📝 콘텐츠 수정' : '✨ 새 콘텐츠 작성'}
            </h2>
            <p className="text-primary-100 mt-2">
              Tiptap으로 Notion처럼 실시간 렌더링하며 작성하세요
            </p>
          </div>

          <form onSubmit={handleSubmit(onFormSubmit)} className="p-8 space-y-8">
        {/* Title */}
        <div className="group">
          <label htmlFor="title" className="block text-sm font-semibold text-gray-800 mb-2">
            📄 제목 *
          </label>
          <input
            {...register('title', { required: '제목을 입력해주세요.' })}
            type="text"
            className="w-full px-4 py-3 text-lg border-2 border-gray-200 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all duration-200 bg-gray-50 focus:bg-white"
            placeholder="매력적인 제목을 입력하세요..."
          />
          {errors.title && (
            <p className="mt-2 text-sm text-red-600 flex items-center">
              <span className="mr-1">⚠️</span>
              {errors.title.message}
            </p>
          )}
        </div>

        {/* Content */}
        <div className="group">
          <label htmlFor="content" className="block text-sm font-semibold text-gray-800 mb-2">
            ✍️ 내용 *
          </label>
          <div className="mt-1 rounded-lg overflow-hidden border-2 border-gray-200 focus-within:border-primary-500 transition-all duration-200">
            <style>{`
              .tiptap-editor {
                font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
                font-size: 16px;
              }
              
              .tiptap-editor h1 {
                font-size: 2.5rem;
                font-weight: 800;
                line-height: 1.2;
                margin: 1.5rem 0 1rem 0;
                color: #1f2937;
                border-bottom: 2px solid #e5e7eb;
                padding-bottom: 0.5rem;
              }
              
              .tiptap-editor h2 {
                font-size: 2rem;
                font-weight: 700;
                line-height: 1.3;
                margin: 1.25rem 0 0.75rem 0;
                color: #374151;
              }
              
              .tiptap-editor h3 {
                font-size: 1.5rem;
                font-weight: 600;
                line-height: 1.4;
                margin: 1rem 0 0.5rem 0;
                color: #4b5563;
              }
              
              .tiptap-editor h4 {
                font-size: 1.25rem;
                font-weight: 600;
                line-height: 1.4;
                margin: 1rem 0 0.5rem 0;
                color: #6b7280;
              }
              
              .tiptap-editor ul {
                list-style-type: disc;
                margin-left: 1.5rem;
                margin: 1rem 0;
              }
              
              .tiptap-editor ol {
                list-style-type: decimal;
                margin-left: 1.5rem;
                margin: 1rem 0;
              }
              
              .tiptap-editor li {
                margin: 0.5rem 0;
                line-height: 1.6;
              }
              
              .tiptap-editor strong {
                font-weight: 700;
                color: #1f2937;
              }
              
              .tiptap-editor em {
                font-style: italic;
                color: #374151;
              }
              
              .tiptap-editor blockquote {
                border-left: 4px solid #3b82f6;
                padding-left: 1rem;
                margin: 1rem 0;
                background-color: #f8fafc;
                font-style: italic;
                color: #64748b;
              }
              
              
              .tiptap-editor pre {
                background-color: #1e293b;
                padding: 1rem;
                border-radius: 0.5rem;
                overflow-x: auto;
                margin: 1rem 0;
              }
              
              .tiptap-editor pre code {
                background-color: transparent;
                padding: 0;
                color: #e2e8f0;
                font-size: 0.875rem;
              }
              
              .tiptap-editor p {
                margin: 1rem 0;
                line-height: 1.7;
              }
              
              .tiptap-editor hr {
                border: none;
                height: 2px;
                background-color: #e5e7eb;
                margin: 2rem 0;
              }
              
              .tiptap-editor table {
                width: 100%;
                border-collapse: collapse;
                margin: 1rem 0;
              }
              
              .tiptap-editor th,
              .tiptap-editor td {
                border: 1px solid #d1d5db;
                padding: 0.75rem;
                text-align: left;
              }
              
              .tiptap-editor th {
                background-color: #f9fafb;
                font-weight: 600;
              }
              
              .tiptap-editor p.is-editor-empty:first-child::before {
                content: attr(data-placeholder);
                float: left;
                color: #9ca3af;
                pointer-events: none;
                height: 0;
              }
              
              .tiptap-toolbar {
                display: flex;
                gap: 0.5rem;
                padding: 0.75rem;
                background-color: #f9fafb;
                border-bottom: 1px solid #e5e7eb;
                flex-wrap: wrap;
              }
              
              .tiptap-toolbar button {
                padding: 0.5rem;
                border: 1px solid #d1d5db;
                border-radius: 0.375rem;
                background-color: white;
                color: #374151;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 0.2s;
              }
              
              .tiptap-toolbar button:hover {
                background-color: #f3f4f6;
              }
              
              .tiptap-toolbar button.is-active {
                background-color: #3b82f6;
                color: white;
                border-color: #3b82f6;
              }
            `}</style>
            
            {/* Notion-style Toolbar */}
            <div className="tiptap-toolbar">
              <button
                onClick={() => editor?.chain().focus().toggleBold().run()}
                disabled={!editor?.can().chain().focus().toggleBold().run()}
                className={editor?.isActive('bold') ? 'is-active' : ''}
                type="button"
              >
                <strong>B</strong>
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleItalic().run()}
                disabled={!editor?.can().chain().focus().toggleItalic().run()}
                className={editor?.isActive('italic') ? 'is-active' : ''}
                type="button"
              >
                <em>I</em>
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleStrike().run()}
                disabled={!editor?.can().chain().focus().toggleStrike().run()}
                className={editor?.isActive('strike') ? 'is-active' : ''}
                type="button"
              >
                <s>S</s>
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleCodeBlock().run()}
                disabled={!editor?.can().chain().focus().toggleCodeBlock().run()}
                className={editor?.isActive('codeBlock') ? 'is-active' : ''}
                type="button"
              >
                {'</>'}
              </button>
              <button
                onClick={handleImageButtonClick}
                disabled={isUploadingImage}
                type="button"
                className={isUploadingImage ? 'opacity-50 cursor-not-allowed' : ''}
              >
                {isUploadingImage ? '📤' : '🖼️'}
              </button>
              <div className="w-px h-6 bg-gray-300 mx-1" />
              <button
                onClick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}
                className={editor?.isActive('heading', { level: 1 }) ? 'is-active' : ''}
                type="button"
              >
                H1
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}
                className={editor?.isActive('heading', { level: 2 }) ? 'is-active' : ''}
                type="button"
              >
                H2
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}
                className={editor?.isActive('heading', { level: 3 }) ? 'is-active' : ''}
                type="button"
              >
                H3
              </button>
              <div className="w-px h-6 bg-gray-300 mx-1" />
              <button
                onClick={() => editor?.chain().focus().toggleBulletList().run()}
                className={editor?.isActive('bulletList') ? 'is-active' : ''}
                type="button"
              >
                • List
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleOrderedList().run()}
                className={editor?.isActive('orderedList') ? 'is-active' : ''}
                type="button"
              >
                1. List
              </button>
              <button
                onClick={() => editor?.chain().focus().toggleBlockquote().run()}
                className={editor?.isActive('blockquote') ? 'is-active' : ''}
                type="button"
              >
                Quote
              </button>
              <button
                onClick={() => editor?.chain().focus().setHorizontalRule().run()}
                type="button"
              >
                HR
              </button>
            </div>
            
            <div className="relative">
              <EditorContent editor={editor} />
            </div>
          </div>
          {!content && (
            <p className="mt-3 text-sm text-red-600 flex items-center">
              <span className="mr-1">⚠️</span>
              내용을 입력해주세요.
            </p>
          )}
          <div className="mt-3 flex justify-between items-center text-sm">
            <div className="flex items-center text-gray-600">
              <span className="mr-1">✨</span>
              <span>Tiptap WYSIWYG 에디터로 # 입력 시 즉시 큰 제목으로, ``` 입력 시 코드 블록이 생성됩니다</span>
            </div>
            <div className="flex items-center space-x-3 text-xs text-gray-500">
              <span className="flex items-center">
                <span className="mr-1">📊</span>
                {editor?.storage.characterCount?.characters() || 0} 문자
              </span>
              <span className="flex items-center">
                <span className="mr-1">📝</span>
                {editor?.storage.characterCount?.words() || 0} 단어
              </span>
              {autoSaveStatus === 'saving' && (
                <span className="flex items-center text-blue-500">
                  <span className="mr-1">💾</span>
                  저장 중...
                </span>
              )}
              {autoSaveStatus === 'saved' && lastSaved && (
                <span className="flex items-center text-green-500">
                  <span className="mr-1">✅</span>
                  {lastSaved.toLocaleTimeString()}에 저장됨
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Category */}
        <div className="group">
          <div className="flex items-center justify-between mb-3">
            <label htmlFor="category" className="block text-sm font-semibold text-gray-800">
              🏷️ 카테고리
            </label>
            <button
              type="button"
              onClick={() => setShowNewCategoryForm(!showNewCategoryForm)}
              className="inline-flex items-center px-3 py-1 text-sm font-medium text-primary-600 hover:text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-md transition-colors duration-200"
            >
              <span className="mr-1">➕</span>
              새 카테고리
            </button>
          </div>
          
          {showNewCategoryForm && (
            <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
              <div className="space-y-4">
                <div>
                  <input
                    type="text"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    placeholder="카테고리 이름을 입력하세요"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all duration-200"
                  />
                </div>
                <div>
                  <textarea
                    value={newCategoryDescription}
                    onChange={(e) => setNewCategoryDescription(e.target.value)}
                    placeholder="카테고리 설명 (선택사항)"
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all duration-200"
                  />
                </div>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={handleCreateCategory}
                    disabled={!newCategoryName.trim() || createCategoryMutation.isPending}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors duration-200"
                  >
                    {createCategoryMutation.isPending ? (
                      <>
                        <span className="mr-2">⏳</span>
                        생성 중...
                      </>
                    ) : (
                      <>
                        <span className="mr-2">✨</span>
                        생성
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowNewCategoryForm(false);
                      setNewCategoryName('');
                      setNewCategoryDescription('');
                    }}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors duration-200"
                  >
                    <span className="mr-2">❌</span>
                    취소
                  </button>
                </div>
              </div>
            </div>
          )}
          
          <select
            {...register('category')}
            className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:border-primary-500 focus:ring-2 focus:ring-primary-200 transition-all duration-200 bg-gray-50 focus:bg-white"
          >
            <option value="">📂 카테고리 선택 (선택사항)</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        {/* Priority */}
        <div className="group">
          <label className="block text-sm font-semibold text-gray-800 mb-3">
            🚨 중요도 *
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'high', label: '높음', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', emoji: '🔴' },
              { value: 'medium', label: '보통', color: 'text-yellow-600', bg: 'bg-yellow-50', border: 'border-yellow-200', emoji: '🟡' },
              { value: 'low', label: '낮음', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-200', emoji: '🟢' }
            ].map((option) => (
              <label key={option.value} className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition-all duration-200 ${option.bg} ${option.border} hover:shadow-sm`}>
                <input
                  {...register('priority', { required: true })}
                  type="radio"
                  value={option.value}
                  className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300"
                />
                <span className={`ml-3 flex items-center font-medium ${option.color}`}>
                  <span className="mr-2">{option.emoji}</span>
                  {option.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Tags */}
        {tags.length > 0 && (
          <div className="group">
            <label className="block text-sm font-semibold text-gray-800 mb-3">
              🏷️ 태그
            </label>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <button
                  key={tag.id}
                  type="button"
                  onClick={() => handleTagToggle(tag.id)}
                  className={`inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium border-2 transition-all duration-200 ${
                    selectedTags.includes(tag.id)
                      ? 'bg-primary-100 text-primary-800 border-primary-300 shadow-sm'
                      : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
                  }`}
                >
                  <span className="mr-1">{selectedTags.includes(tag.id) ? '✅' : '🔘'}</span>
                  {tag.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Submit buttons */}
        <div className="flex justify-end space-x-4 pt-8 border-t-2 border-gray-100">
          <button
            type="button"
            onClick={onCancel}
            className="inline-flex items-center px-6 py-3 border-2 border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
          >
            <span className="mr-2">❌</span>
            취소
          </button>
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center px-8 py-3 border-2 border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
          >
            {isLoading ? (
              <>
                <span className="mr-2">⏳</span>
                저장 중...
              </>
            ) : (
              <>
                <span className="mr-2">💾</span>
                저장
              </>
            )}
          </button>
        </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ContentForm;