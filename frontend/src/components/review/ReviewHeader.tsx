import React from 'react';
import { Category } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { useReviewState } from '../../hooks/useReviewState';

interface ReviewHeaderProps {
  reviews: any[];
  reviewsCompleted: number;
  totalSchedules: number;
  currentReviewIndex: number;
  progress: number;
  categories: Category[];
}

const ReviewHeader: React.FC<ReviewHeaderProps> = ({
  reviews,
  reviewsCompleted,
  totalSchedules,
  currentReviewIndex,
  progress,
  categories,
}) => {
  const { user, refreshUser } = useAuth();
  const {
    selectedCategory,
    setSelectedCategory,
    reviewMode,
    setReviewMode,
    setCurrentReviewIndex,
    setShowContent,
    setIsFlipped,
    setReviewsCompleted,
    setShowUpgradeModal,
    resetCategoryState,
  } = useReviewState();

  const canUseExplanation = user?.subscription?.tier !== 'free';

  return (
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
              완료: {reviewsCompleted}개
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

      {/* Category filter and Review Mode */}
      <div className="mt-6 bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="flex flex-col md:flex-row md:items-end md:space-x-6 space-y-4 md:space-y-0">
          <div className="flex-1 max-w-md">
            <label htmlFor="category-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              카테고리별 복습
            </label>
            <select
              id="category-filter"
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                resetCategoryState();
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
          
          <div className="flex-1 max-w-md">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              학습 모드
            </label>
            <div className="flex rounded-md shadow-sm" role="group">
              <button
                type="button"
                onClick={() => setReviewMode('card')}
                className={`px-4 py-2 text-sm font-medium rounded-l-md border ${
                  reviewMode === 'card'
                    ? 'bg-blue-600 dark:bg-blue-500 text-white border-blue-600 dark:border-blue-500'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
              >
                🃏 카드 모드
              </button>
              <button
                type="button"
                onClick={async () => {
                  await refreshUser();
                  const updatedCanUseExplanation = user?.subscription?.tier !== 'free';
                  
                  if (updatedCanUseExplanation || canUseExplanation) {
                    setReviewMode('explanation');
                  } else {
                    setShowUpgradeModal(true);
                  }
                }}
                disabled={!canUseExplanation}
                className={`px-4 py-2 text-sm font-medium rounded-r-md border-t border-r border-b relative ${
                  reviewMode === 'explanation'
                    ? 'bg-blue-600 dark:bg-blue-500 text-white border-blue-600 dark:border-blue-500'
                    : canUseExplanation
                    ? 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-700 cursor-pointer'
                }`}
                title={!canUseExplanation ? 'BASIC 이상 구독이 필요합니다 (클릭하여 최신 구독 정보 확인)' : ''}
              >
                <div className="flex items-center space-x-1">
                  <span>✍️ 서술형 모드</span>
                  {!canUseExplanation && <span className="text-xs">🔒</span>}
                </div>
              </button>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {reviewMode === 'card' 
                ? '카드를 뒤집어 내용을 확인' 
                : canUseExplanation 
                  ? 'AI가 설명을 평가해드려요' 
                  : 'BASIC 이상 구독에서 사용 가능'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewHeader;