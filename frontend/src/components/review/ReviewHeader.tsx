import React from 'react';

interface ReviewHeaderProps {
  reviewsCompleted: number;
  totalSchedules: number;
  progress: number;
}

const ReviewHeader: React.FC<ReviewHeaderProps> = ({
  reviewsCompleted,
  totalSchedules,
  progress,
}) => {

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


    </div>
  );
};

export default ReviewHeader;