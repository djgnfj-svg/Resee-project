import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI, contentAPI } from '../utils/api';
import { DashboardData, ContentUsage, CategoryUsage } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyDashboard from '../components/dashboard/EmptyDashboard';
import ErrorDashboard from '../components/dashboard/ErrorDashboard';
import DashboardStats from '../components/dashboard/DashboardStats';
import QuickActions from '../components/dashboard/QuickActions';
import LearningTips from '../components/dashboard/LearningTips';



const SimpleDashboard: React.FC = () => {

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
      {/* Hero Section */}
      <div className="mb-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">안녕하세요! 📚</h1>
            <p className="text-blue-100 text-lg">
              오늘도 성실하게 학습하는 당신을 응원합니다.
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">
              {new Date().toLocaleDateString('ko-KR', { 
                month: 'long', 
                day: 'numeric', 
                weekday: 'short' 
              })}
            </div>
            <div className="text-blue-100 mt-1">
              {new Date().toLocaleTimeString('ko-KR', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Usage Cards */}
      {(contentUsage || categoryUsage) && (
        <div className="mb-6 grid gap-4 md:grid-cols-2">
          {/* Content Usage Card */}
          {contentUsage && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                    <span className="text-2xl mr-2">📝</span>
                    콘텐츠
                  </h3>
                  <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                    contentUsage.tier === 'free' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' :
                    contentUsage.tier === 'basic' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                    'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                  }`}>
                    {contentUsage.tier === 'free' ? '무료' : contentUsage.tier === 'basic' ? '베이직' : '프로'} 플랜
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      사용량
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {contentUsage.current} / {contentUsage.limit}개
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all duration-300 ${
                        contentUsage.percentage >= 90 ? 'bg-red-500' :
                        contentUsage.percentage >= 70 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(contentUsage.percentage, 100)}%` }}
                    />
                  </div>
                  {contentUsage.percentage >= 90 && (
                    <div className="flex items-center justify-between pt-2">
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {contentUsage.remaining === 0 ? '제한에 도달' : `${contentUsage.remaining}개 남음`}
                      </p>
                      {contentUsage.tier !== 'pro' && (
                        <a
                          href="/settings#subscription"
                          className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          업그레이드 →
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Category Usage Card */}
          {categoryUsage && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                    <span className="text-2xl mr-2">📁</span>
                    카테고리
                  </h3>
                  <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                    categoryUsage.tier === 'free' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' :
                    categoryUsage.tier === 'basic' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                    'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                  }`}>
                    {categoryUsage.tier === 'free' ? '무료' : categoryUsage.tier === 'basic' ? '베이직' : '프로'} 플랜
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      사용량
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {categoryUsage.current} / {categoryUsage.limit}개
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all duration-300 ${
                        categoryUsage.percentage >= 90 ? 'bg-red-500' :
                        categoryUsage.percentage >= 70 ? 'bg-yellow-500' :
                        'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(categoryUsage.percentage, 100)}%` }}
                    />
                  </div>
                  {categoryUsage.percentage >= 90 && (
                    <div className="flex items-center justify-between pt-2">
                      <p className="text-xs text-red-600 dark:text-red-400">
                        {categoryUsage.remaining === 0 ? '제한에 도달' : `${categoryUsage.remaining}개 남음`}
                      </p>
                      {categoryUsage.tier !== 'pro' && (
                        <a
                          href="/settings#subscription"
                          className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          업그레이드 →
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats Cards */}
      <DashboardStats
        todayReviews={dashboardData?.today_reviews || 0}
        totalContent={dashboardData?.total_content || 0}
        successRate={dashboardData?.success_rate || 0}
      />

      {/* Quick Actions & Tips */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        <QuickActions />
        <LearningTips />
      </div>
      
      

    </div>
  );
};

export default SimpleDashboard;