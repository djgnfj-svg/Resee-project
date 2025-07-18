import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { contentAPI } from '../utils/api';
import { Content, Category, CreateContentData, UpdateContentData } from '../types';
import { extractResults } from '../utils/helpers';
import ContentFormV2 from '../components/ContentFormV2';

const ContentPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingContent, setEditingContent] = useState<Content | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('created_desc');

  // Fetch contents
  const { data: contents = [], isLoading: contentsLoading } = useQuery<Content[]>({
    queryKey: ['contents', selectedCategory, searchTerm, selectedPriority, sortBy],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category_slug', selectedCategory);
      }
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (selectedPriority !== 'all') {
        params.append('priority', selectedPriority);
      }
      params.append('ordering', sortBy);
      return contentAPI.getContents(params.toString()).then(extractResults);
    },
  });

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Create content mutation
  const createContentMutation = useMutation({
    mutationFn: contentAPI.createContent,
    onSuccess: () => {
      alert('Success: 콘텐츠가 성공적으로 생성되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setShowForm(false);
    },
    onError: () => {
      alert('Error: 콘텐츠 생성에 실패했습니다.');
    },
  });

  // Update content mutation
  const updateContentMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateContentData }) => 
      contentAPI.updateContent(id, data),
    onSuccess: () => {
      alert('Success: 콘텐츠가 성공적으로 수정되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setEditingContent(null);
      setShowForm(false);
    },
    onError: () => {
      alert('Error: 콘텐츠 수정에 실패했습니다.');
    },
  });

  // Delete content mutation
  const deleteContentMutation = useMutation({
    mutationFn: contentAPI.deleteContent,
    onSuccess: () => {
      alert('Success: 콘텐츠가 성공적으로 삭제되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
    },
    onError: () => {
      alert('Error: 콘텐츠 삭제에 실패했습니다.');
    },
  });

  const handleSubmit = (data: CreateContentData | UpdateContentData) => {
    if (editingContent) {
      updateContentMutation.mutate({ id: editingContent.id, data });
    } else {
      createContentMutation.mutate(data as CreateContentData);
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
      <ContentFormV2
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        isLoading={createContentMutation.isPending || updateContentMutation.isPending}
        initialData={editingContent ? {
          title: editingContent.title,
          content: editingContent.content,
          category: editingContent.category?.id,
          priority: editingContent.priority,
        } : undefined}
      />
    );
  }

  return (
    <div>
      <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">콘텐츠 관리</h1>
          <p className="mt-2 text-sm sm:text-base text-gray-600">
            학습 콘텐츠를 작성하고 관리합니다.
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-500 w-full sm:w-auto"
        >
          <svg className="-ml-0.5 mr-1.5 h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
          </svg>
          새 콘텐츠
        </button>
      </div>

      {/* Advanced Search & Filters */}
      <div className="mb-6 bg-white p-4 sm:p-6 rounded-2xl shadow-lg">
        <div className="flex items-center mb-4">
          <div className="text-xl mr-2">🔍</div>
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">검색 & 필터</h2>
        </div>
        
        {/* Search Bar */}
        <div className="relative mb-4">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="제목이나 내용으로 검색..."
            className="block w-full pl-10 pr-4 py-3 text-base sm:text-lg border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
          />
        </div>

        {/* Filter Options */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Category filter */}
          <div>
            <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 mb-2">
              📂 카테고리
            </label>
            <select
              id="category-filter"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-all duration-200"
            >
              <option value="all">전체 카테고리</option>
              {categories.map((category) => (
                <option key={category.slug} value={category.slug}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority filter */}
          <div>
            <label htmlFor="priority-filter" className="block text-sm font-medium text-gray-700 mb-2">
              ⚡ 우선순위
            </label>
            <select
              id="priority-filter"
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-all duration-200"
            >
              <option value="all">전체 우선순위</option>
              <option value="high">높음</option>
              <option value="medium">보통</option>
              <option value="low">낮음</option>
            </select>
          </div>

          {/* Sort by */}
          <div>
            <label htmlFor="sort-filter" className="block text-sm font-medium text-gray-700 mb-2">
              📊 정렬
            </label>
            <select
              id="sort-filter"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 transition-all duration-200"
            >
              <option value="created_desc">최신순</option>
              <option value="created_asc">오래된순</option>
              <option value="title_asc">제목순</option>
              <option value="priority_desc">우선순위 높은순</option>
              <option value="priority_asc">우선순위 낮은순</option>
            </select>
          </div>
        </div>

        {/* Active Filters Display */}
        <div className="mt-4 flex flex-wrap gap-2">
          {searchTerm && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              검색: "{searchTerm}"
              <button
                onClick={() => setSearchTerm('')}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          )}
          {selectedCategory !== 'all' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
              카테고리: {categories.find(c => c.slug === selectedCategory)?.name}
              <button
                onClick={() => setSelectedCategory('all')}
                className="ml-2 text-green-600 hover:text-green-800"
              >
                ×
              </button>
            </span>
          )}
          {selectedPriority !== 'all' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
              우선순위: {selectedPriority === 'high' ? '높음' : selectedPriority === 'medium' ? '보통' : '낮음'}
              <button
                onClick={() => setSelectedPriority('all')}
                className="ml-2 text-yellow-600 hover:text-yellow-800"
              >
                ×
              </button>
            </span>
          )}
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
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                >
                  {content.content.length > 200 
                    ? content.content.substring(0, 200) + '...' 
                    : content.content}
                </ReactMarkdown>
              </div>

            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContentPage;