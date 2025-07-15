import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Content, Category } from '../types';
import ContentForm from '../components/ContentForm';
import ReactMarkdown from 'react-markdown';

const ContentPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingContent, setEditingContent] = useState<Content | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch contents
  const { data: contents = [], isLoading: contentsLoading } = useQuery<Content[]>({
    queryKey: ['contents', selectedCategory, searchTerm],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category_slug', selectedCategory);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      return contentAPI.getContents(params.toString()).then(res => res.results || res);
    },
  });

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(res => res.results || res),
  });

  // Create content mutation
  const createContentMutation = useMutation({
    mutationFn: contentAPI.createContent,
    onSuccess: (data) => {
      console.log('콘텐츠 생성 성공:', data);
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setShowForm(false);
    },
    onError: (error) => {
      console.error('콘텐츠 생성 실패:', error);
    },
  });

  // Update content mutation
  const updateContentMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => 
      contentAPI.updateContent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setEditingContent(null);
      setShowForm(false);
    },
  });

  // Delete content mutation
  const deleteContentMutation = useMutation({
    mutationFn: contentAPI.deleteContent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contents'] });
    },
  });

  const handleSubmit = (data: any) => {
    console.log('폼 제출됨:', data);
    if (editingContent) {
      console.log('콘텐츠 수정 모드');
      updateContentMutation.mutate({ id: editingContent.id, data });
    } else {
      console.log('새 콘텐츠 생성 모드');
      createContentMutation.mutate(data);
    }
  };

  const handleEdit = (content: Content) => {
    setEditingContent(content);
    setShowForm(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('정말로 이 콘텐츠를 삭제하시겠습니까?')) {
      deleteContentMutation.mutate(id);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingContent(null);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high': return '높음';
      case 'medium': return '보통';
      case 'low': return '낮음';
      default: return priority;
    }
  };

  if (showForm) {
    return (
      <div>
        <ContentForm
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          isLoading={createContentMutation.isPending || updateContentMutation.isPending}
          initialData={editingContent ? {
            title: editingContent.title,
            content: editingContent.content,
            category: editingContent.category?.id,
            priority: editingContent.priority,
            tag_ids: editingContent.tags.map(tag => tag.id)
          } : undefined}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">콘텐츠 관리</h1>
          <p className="mt-2 text-gray-600">
            학습 콘텐츠를 작성하고 관리합니다.
          </p>
        </div>
        <button
          onClick={() => {
            console.log('새 콘텐츠 버튼 클릭됨');
            setShowForm(true);
          }}
          className="inline-flex items-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500"
        >
          <svg className="-ml-0.5 mr-1.5 h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          새 콘텐츠
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Category filter */}
          <div>
            <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 mb-1">
              카테고리
            </label>
            <select
              id="category-filter"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            >
              <option value="all">전체 카테고리</option>
              {categories.map((category) => (
                <option key={category.slug} value={category.slug}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* Search */}
          <div>
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              검색
            </label>
            <input
              type="text"
              id="search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="제목이나 내용으로 검색..."
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Content list */}
      {contentsLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : contents.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">콘텐츠 없음</h3>
          <p className="mt-1 text-sm text-gray-500">
            {selectedCategory === 'all' ? '새로운 학습 콘텐츠를 추가해보세요.' : '이 카테고리에 콘텐츠가 없습니다.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {contents.map((content) => (
            <div key={content.id} className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {content.title}
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    {content.category && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {content.category.name}
                      </span>
                    )}
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(content.priority)}`}>
                      {getPriorityText(content.priority)}
                    </span>
                    <span>{new Date(content.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex space-x-2 ml-4">
                  <button
                    onClick={() => handleEdit(content)}
                    className="text-primary-600 hover:text-primary-900 text-sm"
                  >
                    편집
                  </button>
                  <button
                    onClick={() => handleDelete(content.id)}
                    className="text-red-600 hover:text-red-900 text-sm"
                  >
                    삭제
                  </button>
                </div>
              </div>
              
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>
                  {content.content.length > 200 
                    ? content.content.substring(0, 200) + '...' 
                    : content.content
                  }
                </ReactMarkdown>
              </div>

              {content.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1">
                  {content.tags.map((tag) => (
                    <span key={tag.id} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {tag.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentPage;