import React from 'react';

const WeeklyTestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-12">
          {/* Icon */}
          <div className="text-6xl mb-6"></div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            주간 시험
          </h1>

          {/* Description */}
          <p className="text-gray-600 dark:text-gray-400 mb-8 leading-relaxed">
            주간 단위로 학습한 내용을 종합적으로<br />
            테스트할 수 있는 기능을 준비 중입니다.
          </p>

          {/* Coming Soon Badge */}
          <div className="inline-flex items-center px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-full">
            <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 animate-pulse"></div>
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
              곧 출시 예정
            </span>
          </div>

          {/* Features Preview */}
          <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
              예정 기능
            </h3>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-2">
              <li className="flex items-center">
                <span className="text-green-500 mr-2">•</span>
                주간 학습 내용 종합 테스트
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">•</span>
                객관식 및 주관식 문제
              </li>
              <li className="flex items-center">
                <span className="text-green-500 mr-2">•</span>
                성취도 분석 리포트
              </li>
            </ul>
          </div>
        </div>

        {/* Back to Dashboard */}
        <button
          onClick={() => window.location.href = '/dashboard'}
          className="mt-6 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium transition-colors"
        >
          ← 대시보드로 돌아가기
        </button>
      </div>
    </div>
  );
};

export default WeeklyTestPage;