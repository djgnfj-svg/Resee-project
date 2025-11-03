import React from 'react';

const QuickActions: React.FC = () => {
  return (
    <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-6 shadow-lg dark:shadow-gray-700/20">
      <div className="flex items-center mb-4">
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">빠른 액션</h3>
      </div>
      <div className="space-y-3">
        <a
          href="/content/new"
          className="w-full group relative overflow-hidden rounded-xl bg-indigo-600 hover:bg-indigo-700 px-6 py-4 text-white font-semibold transition-colors duration-150 block text-center focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          새 콘텐츠 추가
        </a>
        <a
          href="/review"
          className="w-full group relative overflow-hidden rounded-xl bg-green-600 hover:bg-green-700 px-6 py-4 text-white font-semibold transition-colors duration-150 block text-center focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
        >
          오늘의 복습 시작
        </a>
      </div>
    </div>
  );
};

export default QuickActions;