import React from 'react';
import { Category } from '../../types';
import { useReviewState } from '../../hooks/useReviewState';

interface ReviewHeaderProps {
  categories: Category[];
  reviewsCompleted: number;
  totalSchedules: number;
  progress: number;
}

const ReviewHeader: React.FC<ReviewHeaderProps> = ({
  categories,
  reviewsCompleted,
  totalSchedules,
  progress,
}) => {
  const {
    selectedCategory,
    setSelectedCategory,
    resetCategoryState,
  } = useReviewState();

  const remainingReviews = totalSchedules - reviewsCompleted;

  return (
    <div className="mb-8">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">📚 복습 타임</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            에빙하우스 망각곡선을 활용한 스마트 복습 시스템으로 학습해보세요!
          </p>
        </div>
        {totalSchedules > 0 && (
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {remainingReviews}개 남음
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              완료: {reviewsCompleted}개
            </div>
            <div className="text-xs text-gray-400 dark:text-gray-500">
              전체: {totalSchedules}개
            </div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      {totalSchedules > 0 && (
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
          <span>모름 (다시 처음부터)</span>
        </div>
        <div className="flex items-center">
          <kbd className="px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded shadow text-xs mr-2 border border-gray-300 dark:border-gray-600">2</kbd>
          <span>애매함 (같은 간격)</span>
        </div>
        <div className="flex items-center">
          <kbd className="px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded shadow text-xs mr-2 border border-gray-300 dark:border-gray-600">3</kbd>
          <span>기억함 (다음 단계)</span>
        </div>
      </div>

      {/* Category filter */}
      <div className="mt-6 bg-white dark:bg-gray-800 p-4 rounded-lg shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="max-w-md">
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
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            특정 카테고리만 복습하거나 전체를 선택하세요
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReviewHeader;