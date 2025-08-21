import React from 'react';

interface ErrorDashboardProps {
  onRetry: () => void;
}

const ErrorDashboard: React.FC<ErrorDashboardProps> = ({ onRetry }) => {
  return (
    <div className="max-w-md mx-auto mt-8 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
      <div className="text-4xl mb-4">😞</div>
      <h3 className="text-lg font-semibold text-red-800 dark:text-red-300 mb-2">
        데이터를 불러올 수 없습니다
      </h3>
      <p className="text-sm text-red-600 dark:text-red-400 mb-4">
        대시보드 데이터를 불러오는데 문제가 발생했습니다.
      </p>
      <button
        onClick={onRetry}
        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
      >
        다시 시도
      </button>
    </div>
  );
};

export default ErrorDashboard;