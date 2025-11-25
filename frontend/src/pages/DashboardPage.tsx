import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { reviewAPI, contentAPI } from '../utils/api';
import { DashboardData, ContentUsage, CategoryUsage } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EmptyDashboard from '../components/dashboard/EmptyDashboard';
import ErrorDashboard from '../components/dashboard/ErrorDashboard';
import { useAuth } from '../contexts/AuthContext';



const SimpleDashboard: React.FC = () => {
  const { user } = useAuth();

  useEffect(() => {
    document.title = '대시보드 - Resee';
  }, []);

  const { data: dashboardData, isLoading, error, refetch } = useQuery<DashboardData>({
    queryKey: ['dashboard', user?.id],
    queryFn: reviewAPI.getDashboard,
    enabled: !!user,
  });



  // Fetch content usage stats
  const { data: contentUsage } = useQuery<ContentUsage>({
    queryKey: ['content-usage', user?.id],
    queryFn: async () => {
      const response = await contentAPI.getContents();
      return response.usage || null;
    },
    enabled: !!user,
  });

  // Fetch category usage stats
  const { data: categoryUsage } = useQuery<CategoryUsage>({
    queryKey: ['category-usage', user?.id],
    queryFn: async () => {
      const response = await contentAPI.getCategories();
      return response.usage || null;
    },
    enabled: !!user,
  });




  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="대시보드 데이터를 불러오는 중..." />
      </div>
    );
  }

  // 데이터가 없는 경우 처리
  const hasNoData = !dashboardData ||
    (dashboardData.today_reviews === 0 &&
     dashboardData.total_content === 0 &&
     dashboardData.total_reviews_30_days === 0);

  if (error) {
    return <ErrorDashboard onRetry={() => refetch()} />;
  }

  if (hasNoData) {
    return <EmptyDashboard />;
  }

  // Get current hour for greeting
  const currentHour = new Date().getHours();
  const greeting = currentHour < 12 ? '좋은 아침이에요' :
                   currentHour < 18 ? '좋은 오후에요' :
                   '좋은 저녁이에요';

  return (
    <div className="space-y-8">
      {/* Hero Section with Gradient */}
      <div className="relative overflow-hidden bg-gradient-to-br from-indigo-500 via-indigo-600 to-purple-700 rounded-2xl p-8 shadow-2xl">
        <div className="relative z-10">
          <h1 className="text-3xl font-bold text-white mb-2">
            {greeting}, {user?.email?.split('@')[0]}님! 👋
          </h1>
          <p className="text-indigo-100 text-lg">
            오늘도 꾸준한 학습으로 목표를 향해 나아가세요
          </p>
        </div>
        {/* Decorative circles */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-5 rounded-full -mr-32 -mt-32"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white opacity-5 rounded-full -ml-24 -mb-24"></div>
      </div>

      {/* Main Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Today's Review Card - Primary Action */}
        <div className="relative group bg-gradient-to-br from-indigo-50 to-white dark:from-gray-800 dark:to-gray-850 rounded-2xl p-6 shadow-lg border-2 border-indigo-200 dark:border-indigo-900 hover:shadow-xl transition-all duration-200">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                {/* Calendar Icon */}
                <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">오늘의 복습</h3>
              </div>
              <div className="text-5xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">
                {dashboardData?.today_reviews || 0}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {dashboardData?.today_reviews === 0 ? '복습할 항목이 없어요' : '개의 항목이 대기 중'}
              </p>
            </div>
            {/* Badge */}
            {dashboardData?.today_reviews > 0 && (
              <span className="px-3 py-1 bg-indigo-600 text-white text-xs font-semibold rounded-full">
                NEW
              </span>
            )}
          </div>
          <Link
            to="/review"
            className="block w-full text-center px-6 py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-all duration-150 shadow-lg hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            {dashboardData?.today_reviews === 0 ? '콘텐츠 만들러 가기' : '지금 복습 시작하기'} →
          </Link>
        </div>

        {/* Content Management Card */}
        <div className="relative group bg-gradient-to-br from-gray-50 to-white dark:from-gray-800 dark:to-gray-850 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-700">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                {/* Book Icon */}
                <svg className="w-6 h-6 text-gray-700 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">학습 콘텐츠</h3>
              </div>
              <div className="text-5xl font-bold text-gray-900 dark:text-white mb-1">
                {dashboardData?.total_content || 0}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                개의 콘텐츠 보유 중
              </p>
            </div>
          </div>
          <Link
            to="/content/new"
            className="block w-full text-center px-6 py-4 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-indigo-600 hover:bg-indigo-50 dark:hover:bg-gray-700 dark:hover:border-indigo-500 font-semibold rounded-xl transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            + 새 콘텐츠 추가하기
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Success Rate */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            {/* Trophy Icon */}
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">성공률</h3>
          </div>
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">
            {Math.round(dashboardData?.success_rate || 0)}%
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            평균 복습 성공률
          </p>
        </div>

        {/* 30 Days Reviews */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            {/* Chart Icon */}
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900 rounded-lg">
              <svg className="w-6 h-6 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">이번 달</h3>
          </div>
          <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
            {dashboardData?.total_reviews_30_days || 0}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            최근 30일 복습 횟수
          </p>
        </div>

        {/* Subscription Info */}
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-gray-800 dark:to-gray-850 rounded-xl p-6 shadow-md border border-purple-200 dark:border-purple-900">
          <div className="flex items-center gap-3 mb-3">
            {/* Star Icon */}
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
              </svg>
            </div>
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400">구독 플랜</h3>
          </div>
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-2">
            {user?.subscription?.tier === 'pro' ? 'PRO' :
             user?.subscription?.tier === 'basic' ? 'BASIC' : 'FREE'}
          </div>
          <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
            {contentUsage && (
              <div className="flex justify-between">
                <span>콘텐츠</span>
                <span className="font-medium">{contentUsage.current} / {contentUsage.limit === 999999 ? '∞' : contentUsage.limit}</span>
              </div>
            )}
            {categoryUsage && (
              <div className="flex justify-between">
                <span>카테고리</span>
                <span className="font-medium">{categoryUsage.current} / {categoryUsage.limit === 999999 ? '∞' : categoryUsage.limit}</span>
              </div>
            )}
          </div>
          <Link
            to="/subscription"
            className="block mt-3 text-center text-xs font-semibold text-purple-600 dark:text-purple-400 hover:underline"
          >
            플랜 변경하기 →
          </Link>
        </div>
      </div>

    </div>
  );
};

export default SimpleDashboard;
