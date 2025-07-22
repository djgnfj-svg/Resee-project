import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { contentAPI } from '../utils/api';
import { Content, Category, CreateContentData, UpdateContentData } from '../types';
import { extractResults } from '../utils/helpers';
import ContentFormV2 from '../components/ContentFormV2';
import { AIReviewSession } from '../components/ai/AIReviewSession';
import { useAuth } from '../contexts/AuthContext';

const ContentPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingContent, setEditingContent] = useState<Content | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('created_desc');
  const [aiReviewContent, setAIReviewContent] = useState<Content | null>(null);

  // Check if user can access AI features
  const canUseAI = user?.subscription?.is_active && user?.is_email_verified;

  // Fetch contents
  const { data: contents = [], isLoading: contentsLoading } = useQuery<Content[]>({
    queryKey: ['contents', selectedCategory, selectedPriority, sortBy],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category_slug', selectedCategory);
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

  const handleAIReview = (content: Content) => {
    setAIReviewContent(content);
  };

  const handleAIReviewComplete = () => {
    setAIReviewContent(null);
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

  if (aiReviewContent) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Back Button */}
        <div className="mb-4">
          <button
            onClick={handleAIReviewComplete}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg className="-ml-0.5 mr-1.5 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            콘텐츠 목록으로 돌아가기
          </button>
        </div>

        {/* AI Review Session */}
        <AIReviewSession
          content={aiReviewContent}
          onSessionComplete={handleAIReviewComplete}
        />
      </div>
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

      {/* Filters */}
      <div className="mb-6 bg-white p-4 sm:p-6 rounded-2xl shadow-lg">
        <div className="flex items-center mb-4">
          <div className="text-xl mr-2">📂</div>
          <h2 className="text-base sm:text-lg font-semibold text-gray-900">필터</h2>
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
            {selectedCategory === 'all' && selectedPriority === 'all' ? '새로운 학습 콘텐츠를 추가해보세요.' : '선택한 필터에 해당하는 콘텐츠가 없습니다.'}
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
                  {canUseAI ? (
                    <button
                      onClick={() => handleAIReview(content)}
                      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-100 rounded-full hover:bg-purple-200 transition-colors"
                      title="AI 스마트 학습으로 이 콘텐츠를 학습하세요"
                    >
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      AI 학습
                    </button>
                  ) : (
                    <button
                      onClick={() => window.location.href = '/subscription'}
                      className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-gray-500 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
                      title="구독하고 AI 학습 기능을 사용하세요"
                    >
                      <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      AI 학습 (구독 필요)
                    </button>
                  )}
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