import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewAPI, contentAPI } from '../utils/api';
import { ReviewSchedule, Category } from '../types';

const ReviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);

  // Fetch today's reviews
  const { data: reviews = [], isLoading, refetch } = useQuery<ReviewSchedule[]>({
    queryKey: ['todayReviews', selectedCategory],
    queryFn: () => {
      const params = selectedCategory !== 'all' ? `?category_slug=${selectedCategory}` : '';
      return reviewAPI.getTodayReviews(params).then(res => res.results || res);
    },
  });

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(res => res.results || res),
  });

  // Complete review mutation
  const completeReviewMutation = useMutation({
    mutationFn: reviewAPI.completeReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['todayReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      
      // Move to next review
      if (currentReviewIndex < reviews.length - 1) {
        setCurrentReviewIndex(prev => prev + 1);
        setShowContent(false);
      } else {
        // All reviews completed
        setCurrentReviewIndex(0);
        setShowContent(false);
        refetch();
      }
    },
  });

  const handleReviewComplete = (result: 'remembered' | 'partial' | 'forgot') => {
    const currentReview = reviews[currentReviewIndex];
    if (currentReview) {
      completeReviewMutation.mutate({
        content_id: currentReview.content.id,
        result: result,
        time_spent: Math.floor(Math.random() * 300) + 60, // Mock time spent
      });
    }
  };

  const currentReview = reviews[currentReviewIndex];

  return (
    <div>
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">복습</h1>
          <p className="mt-2 text-gray-600">
            오늘 복습할 콘텐츠를 확인하고 복습을 진행합니다.
          </p>
        </div>
        {reviews.length > 0 && (
          <div className="text-sm text-gray-500">
            {currentReviewIndex + 1} / {reviews.length}
          </div>
        )}
      </div>

      {/* Category filter */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="max-w-md">
          <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 mb-1">
            카테고리별 복습
          </label>
          <select
            id="category-filter"
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setCurrentReviewIndex(0);
              setShowContent(false);
            }}
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
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">복습할 항목 없음</h3>
          <p className="mt-1 text-sm text-gray-500">
            {selectedCategory === 'all' 
              ? '오늘 복습할 콘텐츠가 없습니다.' 
              : '이 카테고리에 복습할 콘텐츠가 없습니다.'}
          </p>
        </div>
      ) : currentReview ? (
        <div className="bg-white rounded-lg shadow">
          {/* Review Header */}
          <div className="p-6 border-b">
            <div className="flex justify-between items-start">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">
                  {currentReview.content.title}
                </h2>
                <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                  {currentReview.content.category && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {currentReview.content.category.name}
                    </span>
                  )}
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    currentReview.content.priority === 'high' ? 'text-red-600 bg-red-50' :
                    currentReview.content.priority === 'medium' ? 'text-yellow-600 bg-yellow-50' :
                    'text-green-600 bg-green-50'
                  }`}>
                    {currentReview.content.priority === 'high' ? '높음' :
                     currentReview.content.priority === 'medium' ? '보통' : '낮음'}
                  </span>
                  <span>
                    {currentReview.interval_index + 1}번째 복습
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowContent(!showContent)}
                className="px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                {showContent ? '내용 숨기기' : '내용 보기'}
              </button>
            </div>
          </div>

          {/* Review Content */}
          {showContent && (
            <div className="p-6 border-b bg-gray-50">
              <div className="prose max-w-none">
                <div 
                  className="prose prose-lg max-w-none"
                  dangerouslySetInnerHTML={{ __html: currentReview.content.content }}
                />
              </div>
              {currentReview.content.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1">
                  {currentReview.content.tags.map((tag) => (
                    <span key={tag.id} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {tag.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Review Actions */}
          <div className="p-6">
            <div className="text-center">
              <p className="text-lg font-medium text-gray-900 mb-6">
                이 내용을 얼마나 잘 기억하고 있나요?
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => handleReviewComplete('forgot')}
                  disabled={completeReviewMutation.isPending}
                  className="p-4 border-2 border-red-200 rounded-lg text-center hover:border-red-300 hover:bg-red-50 disabled:opacity-50"
                >
                  <div className="text-red-600 font-semibold">😔 모름</div>
                  <div className="text-sm text-gray-600 mt-1">다시 처음부터</div>
                </button>
                
                <button
                  onClick={() => handleReviewComplete('partial')}
                  disabled={completeReviewMutation.isPending}
                  className="p-4 border-2 border-yellow-200 rounded-lg text-center hover:border-yellow-300 hover:bg-yellow-50 disabled:opacity-50"
                >
                  <div className="text-yellow-600 font-semibold">🤔 애매함</div>
                  <div className="text-sm text-gray-600 mt-1">같은 간격으로</div>
                </button>
                
                <button
                  onClick={() => handleReviewComplete('remembered')}
                  disabled={completeReviewMutation.isPending}
                  className="p-4 border-2 border-green-200 rounded-lg text-center hover:border-green-300 hover:bg-green-50 disabled:opacity-50"
                >
                  <div className="text-green-600 font-semibold">😊 기억함</div>
                  <div className="text-sm text-gray-600 mt-1">다음 단계로</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default ReviewPage;