import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import ReactMarkdown from 'react-markdown';
import { reviewAPI, contentAPI } from '../utils/api';
import { ReviewSchedule, Category, TodayReviewsResponse } from '../types';
import { extractResults } from '../utils/helpers';

const ReviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [reviewsCompleted, setReviewsCompleted] = useState(0);
  const [totalSchedules, setTotalSchedules] = useState(0);

  // Type guard function
  const isTodayReviewsResponse = (data: any): data is TodayReviewsResponse => {
    return data && 
           typeof data === 'object' && 
           'results' in data && 
           'total_count' in data &&
           'count' in data &&
           Array.isArray(data.results);
  };

  // Fetch today's reviews
  const { data: reviewData, isLoading, refetch } = useQuery<ReviewSchedule[]>({
    queryKey: ['todayReviews', selectedCategory],
    queryFn: async () => {
      const params = selectedCategory !== 'all' ? `?category_slug=${selectedCategory}` : '';
      const data = await reviewAPI.getTodayReviews(params);
      
      // Handle both old and new API response formats
      if (isTodayReviewsResponse(data)) {
        // New format with metadata
        setTotalSchedules(data.total_count || 0);
        return data.results;
      } else {
        // Old format (fallback)
        return extractResults(data) as ReviewSchedule[];
      }
    }
  });

  const reviews: ReviewSchedule[] = reviewData || [];

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Complete review mutation
  const completeReviewMutation = useMutation({
    mutationFn: reviewAPI.completeReview,
    onSuccess: async () => {
      setReviewsCompleted(prev => prev + 1);
      setShowContent(false);
      setIsFlipped(false);
      
      // Invalidate cache and refetch to get updated review list
      queryClient.invalidateQueries({ queryKey: ['todayReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      // 캘린더 및 분석 데이터도 무효화하여 실시간 업데이트
      queryClient.invalidateQueries({ queryKey: ['learning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['advanced-analytics'] });
      
      // Wait for data to be refreshed
      const { data: updatedReviews } = await refetch();
      
      // Update state based on new review list
      if (updatedReviews && updatedReviews.length > 0) {
        // If there are still reviews left, stay at current index or adjust
        const newIndex = Math.min(currentReviewIndex, updatedReviews.length - 1);
        setCurrentReviewIndex(newIndex);
      } else {
        // No more reviews, reset to 0
        setCurrentReviewIndex(0);
      }
      
      setStartTime(Date.now());
    },
  });

  const handleReviewComplete = React.useCallback((result: 'remembered' | 'partial' | 'forgot') => {
    const currentReview = reviews[currentReviewIndex];
    if (currentReview) {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      
      // Show appropriate toast message
      const messages = {
        'remembered': '✅ 잘 기억하고 있어요!',
        'partial': '🤔 애매하군요, 다시 복습할게요.',
        'forgot': '😅 괜찮아요, 다시 배워봐요!'
      };
      alert('Success: ' + messages[result]);
      
      completeReviewMutation.mutate({
        content_id: currentReview.content.id,
        result: result,
        time_spent: timeSpent,
      });
    }
  }, [reviews, currentReviewIndex, startTime, completeReviewMutation]);

  const currentReview = reviews[currentReviewIndex];
  const progress = reviews.length > 0 ? (reviewsCompleted / (reviews.length + reviewsCompleted)) * 100 : 0;
  
  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      switch (e.key) {
        case ' ':
          e.preventDefault();
          setIsFlipped(!isFlipped);
          setShowContent(!showContent);
          break;
        case '1':
          e.preventDefault();
          if (showContent) handleReviewComplete('forgot');
          break;
        case '2':
          e.preventDefault();
          if (showContent) handleReviewComplete('partial');
          break;
        case '3':
          e.preventDefault();
          if (showContent) handleReviewComplete('remembered');
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showContent, isFlipped, handleReviewComplete]);
  
  // Reset flip state when review changes
  useEffect(() => {
    setIsFlipped(false);
    setShowContent(false);
    setStartTime(Date.now());
  }, [currentReviewIndex]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header with Progress */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">📚 복습 타임</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              집중해서 복습을 진행해보세요! 스페이스바로 내용을 확인할 수 있어요.
            </p>
          </div>
          {reviews.length > 0 && (
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {reviews.length - reviewsCompleted}개 남음
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                전체: {totalSchedules}개 | 완료: {reviewsCompleted}개
              </div>
              <div className="text-xs text-gray-400 dark:text-gray-500">
                {currentReviewIndex + 1}번째 학습 중
              </div>
            </div>
          )}
        </div>
        
        {/* Progress Bar */}
        {reviews.length > 0 && (
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        )}
        
        {/* Keyboard Shortcuts Info */}
        <div className="flex items-center justify-center space-x-6 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded shadow text-xs mr-2 border border-gray-300 dark:border-gray-600">Space</kbd>
            <span>내용 보기</span>
          </div>
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded shadow text-xs mr-2 border border-gray-300 dark:border-gray-600">1</kbd>
            <span>모름</span>
          </div>
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded shadow text-xs mr-2 border border-gray-300 dark:border-gray-600">2</kbd>
            <span>애매함</span>
          </div>
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded shadow text-xs mr-2 border border-gray-300 dark:border-gray-600">3</kbd>
            <span>기억함</span>
          </div>
        </div>
      </div>

      {/* Category filter */}
      <div className="mb-6 bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="max-w-md">
          <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            카테고리별 복습
          </label>
          <select
            id="category-filter"
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setCurrentReviewIndex(0);
              setShowContent(false);
              setIsFlipped(false);
              setReviewsCompleted(0);
            }}
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-400 dark:focus:ring-primary-400"
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
          <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">복습할 항목 없음</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {selectedCategory === 'all' 
              ? '오늘 복습할 콘텐츠가 없습니다.' 
              : '이 카테고리에 복습할 콘텐츠가 없습니다.'}
          </p>
        </div>
      ) : currentReview ? (
        <div className="max-w-4xl mx-auto">
          {/* Review Card with Flip Animation */}
          <div className="relative h-96 mb-8">
            <div className={`absolute inset-0 w-full h-full transition-transform duration-700 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
              {/* Front of Card */}
              <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden border-2 border-blue-200 dark:border-blue-700">
                <div className="p-8 h-full flex flex-col justify-center items-center text-center">
                  <div className="mb-6">
                    <div className="text-4xl mb-4">🧠</div>
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                      {currentReview.content.title}
                    </h2>
                    <div className="flex items-center justify-center space-x-4 text-sm">
                      {currentReview.content.category && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                          {currentReview.content.category.name}
                        </span>
                      )}
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                        currentReview.content.priority === 'high' ? 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20' :
                        currentReview.content.priority === 'medium' ? 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20' :
                        'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20'
                      }`}>
                        {currentReview.content.priority === 'high' ? '높음' :
                         currentReview.content.priority === 'medium' ? '보통' : '낮음'}
                      </span>
                      <span className="text-gray-500 dark:text-gray-400 text-xs">
                        {currentReview.initial_review_completed ? 
                          `${currentReview.interval_index + 1}번째 복습` : 
                          '첫 번째 복습'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="text-gray-600 dark:text-gray-400 mb-8">
                    이 내용을 얼마나 잘 기억하고 있나요?
                  </div>
                  
                  <button
                    onClick={() => {
                      setIsFlipped(true);
                      setShowContent(true);
                    }}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 dark:hover:from-blue-500 dark:hover:to-purple-600 transition-all duration-300 transform hover:scale-105 shadow-lg dark:shadow-gray-900/40"
                  >
                    내용 확인하기 (Space)
                  </button>
                </div>
              </div>
              
              {/* Back of Card */}
              <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden rotate-y-180 border-2 border-green-200 dark:border-green-700">
                <div className="p-8 h-full flex flex-col">
                  <div className="flex-1 overflow-y-auto">
                    <div className="prose prose-lg dark:prose-invert max-w-none">
                      <ReactMarkdown>
                        {currentReview.content.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                  
                  <div className="mt-6 text-center">
                    <button
                      onClick={() => {
                        setIsFlipped(false);
                        setShowContent(false);
                      }}
                      className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 text-sm mb-4 transition-colors"
                    >
                      ← 뒤로가기
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Review Actions */}
          {showContent && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6">
              <div className="text-center">
                <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">
                  이 내용을 얼마나 잘 기억하고 있나요?
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => handleReviewComplete('forgot')}
                    disabled={completeReviewMutation.isPending}
                    className="group p-6 border-2 border-red-200 dark:border-red-700 rounded-xl text-center hover:border-red-300 dark:hover:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
                  >
                    <div className="text-3xl mb-2">😔</div>
                    <div className="text-red-600 dark:text-red-400 font-semibold text-lg">모름</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">다시 처음부터</div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">키보드: 1</div>
                  </button>
                  
                  <button
                    onClick={() => handleReviewComplete('partial')}
                    disabled={completeReviewMutation.isPending}
                    className="group p-6 border-2 border-yellow-200 dark:border-yellow-700 rounded-xl text-center hover:border-yellow-300 dark:hover:border-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 disabled:opacity-50 transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
                  >
                    <div className="text-3xl mb-2">🤔</div>
                    <div className="text-yellow-600 dark:text-yellow-400 font-semibold text-lg">애매함</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">같은 간격으로</div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">키보드: 2</div>
                  </button>
                  
                  <button
                    onClick={() => handleReviewComplete('remembered')}
                    disabled={completeReviewMutation.isPending}
                    className="group p-6 border-2 border-green-200 dark:border-green-700 rounded-xl text-center hover:border-green-300 dark:hover:border-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50 transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
                  >
                    <div className="text-3xl mb-2">😊</div>
                    <div className="text-green-600 dark:text-green-400 font-semibold text-lg">기억함</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">다음 단계로</div>
                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">키보드: 3</div>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};

export default ReviewPage;