import React from 'react';

interface ReviewControlsProps {
  showContent: boolean;
  onReviewComplete: (result: 'remembered' | 'partial' | 'forgot') => void;
  isPending: boolean;
}

const ReviewControls: React.FC<ReviewControlsProps> = ({
  showContent,
  onReviewComplete,
  isPending,
}) => {
  if (!showContent) return null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6">
      <div className="text-center">
        <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">
          이 내용을 얼마나 잘 기억하고 있나요?
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onReviewComplete('forgot')}
            disabled={isPending}
            className="group p-6 border-2 border-red-200 dark:border-red-700 rounded-xl text-center hover:border-red-300 dark:hover:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
          >
            <div className="text-3xl mb-2">😔</div>
            <div className="text-red-600 dark:text-red-400 font-semibold text-lg">모름</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">다시 처음부터</div>
            <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">키보드: 1</div>
          </button>
          
          <button
            onClick={() => onReviewComplete('partial')}
            disabled={isPending}
            className="group p-6 border-2 border-yellow-200 dark:border-yellow-700 rounded-xl text-center hover:border-yellow-300 dark:hover:border-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 disabled:opacity-50 transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
          >
            <div className="text-3xl mb-2">🤔</div>
            <div className="text-yellow-600 dark:text-yellow-400 font-semibold text-lg">애매함</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">같은 간격으로</div>
            <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">키보드: 2</div>
          </button>
          
          <button
            onClick={() => onReviewComplete('remembered')}
            disabled={isPending}
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
  );
};

export default ReviewControls;