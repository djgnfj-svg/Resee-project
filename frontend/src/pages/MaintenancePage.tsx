import React from 'react';

const MaintenancePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-6">
          {/* Icon */}
          <div className="mx-auto w-20 h-20 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center">
            <svg
              className="w-10 h-10 text-yellow-600 dark:text-yellow-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            서비스 점검 중
          </h1>

          {/* Description */}
          <p className="text-gray-600 dark:text-gray-300">
            더 나은 서비스를 위해 시스템 점검을 진행하고 있습니다.
            <br />
            잠시 후 다시 방문해 주세요.
          </p>

          {/* Maintenance Period */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
              점검 예정 완료 시간
            </p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              2025년 11월 29일
            </p>
          </div>

          {/* Contact */}
          <p className="text-sm text-gray-500 dark:text-gray-400">
            문의사항이 있으시면{' '}
            <a
              href="mailto:reseeall2025@gmail.com"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              reseeall2025@gmail.com
            </a>
            으로 연락해 주세요.
          </p>
        </div>

        {/* Footer */}
        <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
          Resee - 효율적인 학습을 위한 복습 플랫폼
        </p>
      </div>
    </div>
  );
};

export default MaintenancePage;
