import React from 'react';

interface ReviewControlsProps {
  showContent: boolean;
  onReviewComplete: (result: 'remembered' | 'forgot') => void;
  isPending: boolean;
  isSubjectiveMode?: boolean;
  onNext?: () => void;
}

const ReviewControls: React.FC<ReviewControlsProps> = ({
  showContent,
  onReviewComplete,
  isPending,
  isSubjectiveMode = false,
  onNext,
}) => {
  const isDisabled = !showContent || isPending;

  // 주관식 평가: 단일 "다음으로" 버튼
  if (isSubjectiveMode) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6 transition-opacity duration-300 ${!showContent ? 'opacity-50' : 'opacity-100'}`}>
        <div className="text-center">
          <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">
            AI 평가 결과를 확인하셨나요?
          </p>
          <button
            onClick={onNext}
            disabled={isDisabled}
            className="px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 shadow-lg dark:shadow-gray-900/40 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            다음으로
          </button>
        </div>
      </div>
    );
  }

  // 기억 확인 모드: 기존 "모름"/"기억함" 버튼
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6 transition-opacity duration-300 ${!showContent ? 'opacity-50' : 'opacity-100'}`}>
      <div className="text-center">
        <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">
          {showContent ? '이 내용을 얼마나 잘 기억하고 있나요?' : '먼저 내용을 확인해주세요'}
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-lg mx-auto">
          <button
            onClick={() => showContent && onReviewComplete('forgot')}
            disabled={isDisabled}
            className="group p-8 border-2 border-red-200 dark:border-red-700 rounded-xl text-center hover:border-red-300 dark:hover:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
          >
            <div className="text-4xl mb-3">😔</div>
            <div className="text-red-600 dark:text-red-400 font-semibold text-xl">모름</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">다시 처음부터</div>
          </button>

          <button
            onClick={() => showContent && onReviewComplete('remembered')}
            disabled={isDisabled}
            className="group p-8 border-2 border-green-200 dark:border-green-700 rounded-xl text-center hover:border-green-300 dark:hover:border-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 bg-white dark:bg-gray-800"
          >
            <div className="text-4xl mb-3">😊</div>
            <div className="text-green-600 dark:text-green-400 font-semibold text-xl">기억함</div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">다음 단계로</div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReviewControls;