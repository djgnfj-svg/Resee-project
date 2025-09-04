import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const NotFoundPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
      <div className="max-w-lg mx-auto text-center">
        {/* 404 숫자 */}
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 animate-pulse">
            404
          </h1>
        </div>

        {/* 아이콘과 메시지 */}
        <div className="mb-8">
          <div className="text-6xl mb-6 animate-bounce">📚</div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            페이지를 찾을 수 없습니다
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
            요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-500">
            URL을 다시 확인해주시거나 다른 페이지로 이동해보세요.
          </p>
        </div>

        {/* 액션 버튼들 */}
        <div className="space-y-4">
          {/* 주요 액션 버튼 */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to={isAuthenticated ? "/dashboard" : "/"}
              className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg"
            >
              <span className="mr-2">🏠</span>
              {isAuthenticated ? '대시보드로' : '홈으로'} 돌아가기
            </Link>
            
            <button
              onClick={handleGoBack}
              className="inline-flex items-center justify-center px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-semibold rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-all duration-300 transform hover:scale-105 shadow-lg border border-gray-200 dark:border-gray-600"
            >
              <span className="mr-2">⬅️</span>
              이전 페이지로
            </button>
          </div>

          {/* 추천 링크들 */}
          {isAuthenticated && (
            <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                다음 페이지들을 확인해보세요:
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-sm mx-auto">
                <Link
                  to="/content"
                  className="inline-flex items-center justify-center px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <span className="mr-1">📝</span>
                  콘텐츠
                </Link>
                <Link
                  to="/review"
                  className="inline-flex items-center justify-center px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <span className="mr-1">🎯</span>
                  복습
                </Link>
                <Link
                  to="/weekly-test"
                  className="inline-flex items-center justify-center px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <span className="mr-1">📋</span>
                  주간시험
                </Link>
                <Link
                  to="/profile"
                  className="inline-flex items-center justify-center px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <span className="mr-1">👤</span>
                  프로필
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* 하단 장식 */}
        <div className="mt-12 text-xs text-gray-400 dark:text-gray-600">
          <p>Resee - 스마트 복습 플랫폼</p>
        </div>
      </div>

      {/* 배경 장식 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-r from-blue-400/10 to-purple-400/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-r from-purple-400/10 to-pink-400/10 rounded-full blur-3xl"></div>
      </div>
    </div>
  );
};

export default NotFoundPage;