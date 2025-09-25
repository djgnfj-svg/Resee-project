import React from 'react';

const QuickActions: React.FC = () => {
  return (
    <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-6 shadow-lg dark:shadow-gray-700/20">
      <div className="flex items-center mb-4">
        <div className="text-2xl mr-3">⚡</div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">빠른 액션</h3>
      </div>
      <div className="space-y-3">
        <a
          href="/content/new"
          className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4 text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 block text-center"
        >
          <span className="mr-2">📝</span>
          새 콘텐츠 추가
        </a>
        <a
          href="/review"
          className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-green-500 to-teal-600 px-6 py-4 text-white font-semibold hover:from-green-600 hover:to-teal-700 transition-all duration-300 transform hover:scale-105 block text-center"
        >
          <span className="mr-2">🎯</span>
          오늘의 복습 시작
        </a>
      </div>
    </div>
  );
};

export default QuickActions;