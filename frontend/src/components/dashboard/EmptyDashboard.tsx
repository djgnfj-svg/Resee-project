import React from 'react';

const EmptyDashboard: React.FC = () => {
  return (
    <div className="max-w-md mx-auto mt-8 text-center py-16">
      <div className="text-6xl mb-4">📚</div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
        학습을 시작해보세요!
      </h3>
      <p className="text-gray-600 dark:text-gray-400 mb-6">
        첫 콘텐츠를 추가하고 복습을 시작하면<br />
        여기에 학습 현황이 표시됩니다.
      </p>
      <div className="space-x-4">
        <a 
          href="/content" 
          className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          첫 콘텐츠 추가하기
        </a>
      </div>
    </div>
  );
};

export default EmptyDashboard;