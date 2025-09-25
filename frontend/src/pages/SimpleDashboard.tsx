import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI, contentAPI } from '../utils/api';
import { DashboardData, ContentUsage, CategoryUsage } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyDashboard from '../components/dashboard/EmptyDashboard';
import ErrorDashboard from '../components/dashboard/ErrorDashboard';
import QuickActions from '../components/dashboard/QuickActions';
import { useAuth } from '../contexts/AuthContext';



const SimpleDashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: dashboardData, isLoading, error, refetch } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
  });



  // Fetch content usage stats
  const { data: contentUsage } = useQuery<ContentUsage>({
    queryKey: ['content-usage'],
    queryFn: async () => {
      const response = await contentAPI.getContents();
      return response.usage || null;
    },
  });

  // Fetch category usage stats
  const { data: categoryUsage } = useQuery<CategoryUsage>({
    queryKey: ['category-usage'],
    queryFn: async () => {
      const response = await contentAPI.getCategories();
      return response.usage || null;
    },
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



  return (
    <div>
      {/* Quick Actions */}
      <div className="mb-8">
        <QuickActions />
      </div>

      {/* Simplified Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 mb-8">
        {/* 오늘의 복습 - 남은 개수만 표시 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl mb-2">🎯</div>
              <h3 className="text-gray-700 dark:text-gray-300 font-semibold text-lg">오늘의 복습</h3>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-blue-600">
                {dashboardData?.today_reviews || 0}개 남음
              </div>
            </div>
          </div>
        </div>

        {/* 전체 콘텐츠 - 프로그레스바 제거 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl mb-2">📖</div>
              <h3 className="text-gray-700 dark:text-gray-300 font-semibold text-lg">전체 콘텐츠</h3>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">
                {dashboardData?.total_content || 0}개
              </div>
            </div>
          </div>
        </div>

        {/* Usage & Subscription Card - 사용량과 구독 정보 */}
        {(contentUsage || categoryUsage || user) && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
            <div className="text-2xl mb-2">💎</div>
            <h3 className="text-gray-700 dark:text-gray-300 font-semibold text-lg mb-3">구독 & 사용량</h3>

            {/* 구독 정보 */}
            <div className="mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
              <div className="flex justify-between items-center">
                <span className="text-gray-600 dark:text-gray-400 text-sm">현재 플랜:</span>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  user?.subscription?.tier === 'pro' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
                  user?.subscription?.tier === 'basic' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                  'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                }`}>
                  {user?.subscription?.tier === 'pro' ? 'PRO' :
                   user?.subscription?.tier === 'basic' ? 'BASIC' : 'FREE'}
                </span>
              </div>
            </div>

            {/* 사용량 정보 */}
            <div className="space-y-2 text-sm">
              {contentUsage && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">콘텐츠:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {contentUsage.current} / {contentUsage.limit === 999999 ? '무제한' : `${contentUsage.limit}개`}
                  </span>
                </div>
              )}
              {categoryUsage && (
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">카테고리:</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {categoryUsage.current} / {categoryUsage.limit === 999999 ? '무제한' : `${categoryUsage.limit}개`}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default SimpleDashboard;