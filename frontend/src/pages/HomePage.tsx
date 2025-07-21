import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="text-center">
      <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-6xl">
          과학적 복습 플랫폼
          <span className="text-primary-600"> Resee</span>
        </h1>
        <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-gray-400">
          에빙하우스 망각곡선 이론을 기반으로 한 스마트 복습 시스템으로
          학습 효율을 극대화하세요.
        </p>
        <div className="mt-10 flex items-center justify-center gap-x-6">
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="rounded-md bg-primary-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-500"
            >
              대시보드로 이동
            </Link>
          ) : (
            <>
              <Link
                to="/register"
                className="rounded-md bg-primary-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary-500"
              >
                시작하기
              </Link>
              <Link
                to="/login"
                className="text-sm font-semibold leading-6 text-gray-900 dark:text-gray-100"
              >
                로그인 <span aria-hidden="true">→</span>
              </Link>
            </>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-4xl">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-12">주요 기능</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-700/20">
            <div className="mx-auto h-12 w-12 bg-primary-100 dark:bg-primary-900/20 rounded-lg flex items-center justify-center mb-4">
              <svg className="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0118 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              스마트 복습 스케줄링
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              1일 → 3일 → 7일 → 14일 → 30일 간격으로 
              과학적 복습 일정을 자동 관리
            </p>
          </div>

          <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-700/20">
            <div className="mx-auto h-12 w-12 bg-primary-100 dark:bg-primary-900/20 rounded-lg flex items-center justify-center mb-4">
              <svg className="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 009.568 3z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              마크다운 지원
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              마크다운으로 학습 내용을 정리하고
              카테고리와 태그로 체계적 관리
            </p>
          </div>

          <div className="text-center p-6 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-700/20">
            <div className="mx-auto h-12 w-12 bg-primary-100 dark:bg-primary-900/20 rounded-lg flex items-center justify-center mb-4">
              <svg className="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              학습 분석
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              복습 성공률과 학습 패턴을 시각화하여
              개인 맞춤형 학습 인사이트 제공
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;