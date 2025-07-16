import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewAPI, contentAPI } from '../utils/api';
import { ReviewSchedule, Category } from '../types';
import { extractResults } from '../utils/helpers';
import toast from 'react-hot-toast';

const ReviewPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [reviewsCompleted, setReviewsCompleted] = useState(0);

  // Fetch today's reviews
  const { data: reviews = [], isLoading, refetch } = useQuery<ReviewSchedule[]>({
    queryKey: ['todayReviews', selectedCategory],
    queryFn: () => {
      const params = selectedCategory !== 'all' ? `?category_slug=${selectedCategory}` : '';
      return reviewAPI.getTodayReviews(params).then(extractResults);
    },
  });

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
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
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      completeReviewMutation.mutate({
        content_id: currentReview.content.id,
        result: result,
        time_spent: timeSpent,
      });
      
      // Show appropriate toast message
      const messages = {
        'remembered': '✅ 잘 기억하고 있어요!',
        'partial': '🤔 애매하군요, 다시 복습할게요.',
        'forgot': '😅 괜찮아요, 다시 배워봐요!'
      };
      toast.success(messages[result]);
      
      setReviewsCompleted(prev => prev + 1);
      setStartTime(Date.now());
    }
  };

  const currentReview = reviews[currentReviewIndex];
  const progress = reviews.length > 0 ? ((currentReviewIndex + 1) / reviews.length) * 100 : 0;
  
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
    <div>
      {/* Header with Progress */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">📚 복습 타임</h1>
            <p className="mt-2 text-gray-600">
              집중해서 복습을 진행해보세요! 스페이스바로 내용을 확인할 수 있어요.
            </p>
          </div>
          {reviews.length > 0 && (
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {currentReviewIndex + 1} / {reviews.length}
              </div>
              <div className="text-sm text-gray-500">
                완료: {reviewsCompleted}개
              </div>
            </div>
          )}
        </div>
        
        {/* Progress Bar */}
        {reviews.length > 0 && (
          <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        )}
        
        {/* Keyboard Shortcuts Info */}
        <div className="flex items-center justify-center space-x-6 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white rounded shadow text-xs mr-2">Space</kbd>
            <span>내용 보기</span>
          </div>
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white rounded shadow text-xs mr-2">1</kbd>
            <span>모름</span>
          </div>
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white rounded shadow text-xs mr-2">2</kbd>
            <span>애매함</span>
          </div>
          <div className="flex items-center">
            <kbd className="px-2 py-1 bg-white rounded shadow text-xs mr-2">3</kbd>
            <span>기억함</span>
          </div>
        </div>
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
        <div className="max-w-4xl mx-auto">
          {/* Review Card with Flip Animation */}
          <div className="relative h-96 mb-8">
            <div className={`absolute inset-0 w-full h-full transition-transform duration-700 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
              {/* Front of Card */}
              <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl shadow-xl backface-hidden border-2 border-blue-200">
                <div className="p-8 h-full flex flex-col justify-center items-center text-center">
                  <div className="mb-6">
                    <div className="text-4xl mb-4">🧠</div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-4">
                      {currentReview.content.title}
                    </h2>
                    <div className="flex items-center justify-center space-x-4 text-sm">
                      {currentReview.content.category && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {currentReview.content.category.name}
                        </span>
                      )}
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                        currentReview.content.priority === 'high' ? 'text-red-600 bg-red-50' :
                        currentReview.content.priority === 'medium' ? 'text-yellow-600 bg-yellow-50' :
                        'text-green-600 bg-green-50'
                      }`}>
                        {currentReview.content.priority === 'high' ? '높음' :
                         currentReview.content.priority === 'medium' ? '보통' : '낮음'}
                      </span>
                      <span className="text-gray-500 text-xs">
                        {currentReview.initial_review_completed ? 
                          `${currentReview.interval_index + 1}번째 복습` : 
                          '첫 번째 복습'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="text-gray-600 mb-8">
                    이 내용을 얼마나 잘 기억하고 있나요?
                  </div>
                  
                  <button
                    onClick={() => {
                      setIsFlipped(true);
                      setShowContent(true);
                    }}
                    className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg"
                  >
                    내용 확인하기 (Space)
                  </button>
                </div>
              </div>
              
              {/* Back of Card */}
              <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-green-50 to-teal-50 rounded-2xl shadow-xl backface-hidden rotate-y-180 border-2 border-green-200">
                <div className="p-8 h-full flex flex-col">
                  <div className="flex-1 overflow-y-auto">
                    <div className="prose prose-lg max-w-none">
                      <div 
                        dangerouslySetInnerHTML={{ __html: currentReview.content.content }}
                      />
                    </div>
                    {currentReview.content.tags.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {currentReview.content.tags.map((tag) => (
                          <span key={tag.id} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            {tag.name}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-6 text-center">
                    <button
                      onClick={() => {
                        setIsFlipped(false);
                        setShowContent(false);
                      }}
                      className="text-gray-600 hover:text-gray-800 text-sm mb-4"
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
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="text-center">
                <p className="text-lg font-medium text-gray-900 mb-6">
                  이 내용을 얼마나 잘 기억하고 있나요?
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <button
                    onClick={() => handleReviewComplete('forgot')}
                    disabled={completeReviewMutation.isPending}
                    className="group p-6 border-2 border-red-200 rounded-xl text-center hover:border-red-300 hover:bg-red-50 disabled:opacity-50 transition-all duration-300 transform hover:scale-105"
                  >
                    <div className="text-3xl mb-2">😔</div>
                    <div className="text-red-600 font-semibold text-lg">모름</div>
                    <div className="text-sm text-gray-600 mt-1">다시 처음부터</div>
                    <div className="text-xs text-gray-500 mt-2">키보드: 1</div>
                  </button>
                  
                  <button
                    onClick={() => handleReviewComplete('partial')}
                    disabled={completeReviewMutation.isPending}
                    className="group p-6 border-2 border-yellow-200 rounded-xl text-center hover:border-yellow-300 hover:bg-yellow-50 disabled:opacity-50 transition-all duration-300 transform hover:scale-105"
                  >
                    <div className="text-3xl mb-2">🤔</div>
                    <div className="text-yellow-600 font-semibold text-lg">애매함</div>
                    <div className="text-sm text-gray-600 mt-1">같은 간격으로</div>
                    <div className="text-xs text-gray-500 mt-2">키보드: 2</div>
                  </button>
                  
                  <button
                    onClick={() => handleReviewComplete('remembered')}
                    disabled={completeReviewMutation.isPending}
                    className="group p-6 border-2 border-green-200 rounded-xl text-center hover:border-green-300 hover:bg-green-50 disabled:opacity-50 transition-all duration-300 transform hover:scale-105"
                  >
                    <div className="text-3xl mb-2">😊</div>
                    <div className="text-green-600 font-semibold text-lg">기억함</div>
                    <div className="text-sm text-gray-600 mt-1">다음 단계로</div>
                    <div className="text-xs text-gray-500 mt-2">키보드: 3</div>
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