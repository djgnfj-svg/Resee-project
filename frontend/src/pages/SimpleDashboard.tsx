import React, { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { analyticsAPI, contentAPI } from '../utils/api';
import api, { weeklyGoalAPI } from '../utils/api';
import { DashboardData, ContentUsage, CategoryUsage } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyDashboard from '../components/dashboard/EmptyDashboard';
import ErrorDashboard from '../components/dashboard/ErrorDashboard';
import DashboardStats from '../components/dashboard/DashboardStats';
import QuickActions from '../components/dashboard/QuickActions';
import LearningTips from '../components/dashboard/LearningTips';
import ProgressVisualization from '../components/analytics/ProgressVisualization';
import LearningCalendar from '../components/analytics/LearningCalendar';

interface AdvancedAnalyticsData {
  learning_insights: {
    total_content: number;
    total_reviews: number;
    recent_30d_reviews: number;
    recent_7d_reviews: number;
    recent_success_rate: number;
    week_success_rate: number;
    average_interval_days: number;
    streak_days: number;
  };
  category_performance: Array<{
    id: number;
    name: string;
    slug: string;
    content_count: number;
    total_reviews: number;
    success_rate: number;
    recent_success_rate: number;
    difficulty_level: number;
    mastery_level: string;
  }>;
  study_patterns: {
    hourly_pattern: Array<{ hour: number; count: number }>;
    daily_pattern: Array<{ day: string; count: number }>;
    recommended_hour: number;
    recommended_day: string;
    total_study_sessions: number;
  };
  achievement_stats: {
    current_streak: number;
    max_streak: number;
    perfect_sessions: number;
    mastered_categories: number;
    monthly_progress: number;
    monthly_target: number;
    monthly_completed: number;
  };
  performance_metrics?: {
    currentStreak: number;
    longestStreak: number;
    totalReviews: number;
    averageRetention: number;
    studyEfficiency: number;
    weeklyGoal: number;
    weeklyProgress: number;
  };
  recommendations: Array<{
    type: string;
    title: string;
    message: string;
    action: string;
    category_id?: number;
    hour?: number;
  }>;
}

interface CalendarData {
  calendar_data: Array<{
    date: string;
    count: number;
    success_rate: number;
    intensity: number;
    remembered: number;
    partial: number;
    forgot: number;
  }>;
  monthly_summary: Array<{
    month: string;
    total_reviews: number;
    active_days: number;
    success_rate: number;
  }>;
  total_active_days: number;
  best_day: {
    date: string;
    count: number;
    success_rate: number;
  } | null;
}

const SimpleDashboard: React.FC = () => {
  const queryClient = useQueryClient();

  const { data: dashboardData, isLoading, error, refetch } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
  });

  const { data: analyticsData, isLoading: analyticsLoading } = useQuery<AdvancedAnalyticsData>({
    queryKey: ['advanced-analytics'],
    queryFn: () => api.get('/analytics/advanced/').then(res => res.data),
    enabled: false, // Temporarily disable until backend endpoint is implemented
  });

  const { data: calendarData, isLoading: calendarLoading } = useQuery<CalendarData>({
    queryKey: ['learning-calendar'],
    queryFn: () => api.get('/analytics/calendar/').then(res => res.data),
    enabled: false, // Temporarily disable until backend endpoint is implemented
    retry: 3,
    retryDelay: 1000,
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

  // 주간 목표 업데이트 함수
  const handleGoalUpdate = async (newGoal: number): Promise<void> => {
    try {
      await weeklyGoalAPI.updateWeeklyGoal(newGoal);
      // 데이터 새로고침
      await queryClient.invalidateQueries({ queryKey: ['advanced-analytics'] });
    } catch (error: any) {
      throw new Error(error.response?.data?.error || '목표 업데이트에 실패했습니다.');
    }
  };

  // NaN 값을 안전하게 처리하는 헬퍼 함수
  const sanitizeValue = (value: any, defaultValue: number = 0): number => {
    if (value === null || value === undefined) return defaultValue;
    const num = Number(value);
    if (!isFinite(num) || isNaN(num)) return defaultValue;
    return num;
  };

  // ProgressVisualization을 위한 데이터 변환
  const progressData = useMemo(() => {
    if (!analyticsData) return null;

    // 안전한 배열 접근 - calendarData가 없어도 동작하도록
    const safeCalendarData = (calendarData && Array.isArray(calendarData.calendar_data)) ? calendarData.calendar_data : [];
    const safeMonthlyData = (calendarData && Array.isArray(calendarData.monthly_summary)) ? calendarData.monthly_summary : [];
    const safeCategoryData = Array.isArray(analyticsData.category_performance) ? analyticsData.category_performance : [];

    // 주간 진도 데이터 (최근 8주) - NaN 방지 강화
    const weeklyProgress = (() => {
      if (!Array.isArray(safeCalendarData) || safeCalendarData.length === 0) {
        return [];
      }
      
      // 주별로 데이터 그룹화
      const weeklyData = [];
      const today = new Date();
      
      for (let weekOffset = 7; weekOffset >= 0; weekOffset--) {
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - (weekOffset * 7) - today.getDay());
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        // 해당 주의 데이터 필터링
        const weekData = safeCalendarData.filter(day => {
          const dayDate = new Date(day.date);
          return dayDate >= weekStart && dayDate <= weekEnd;
        });
        
        // 주별 합계 계산
        const totalReviews = weekData.reduce((sum, day) => sum + sanitizeValue(day?.count, 0), 0);
        const totalRemembered = weekData.reduce((sum, day) => sum + sanitizeValue(day?.remembered, 0), 0);
        const successRate = totalReviews > 0 ? (totalRemembered / totalReviews * 100) : 0;
        
        weeklyData.push({
          date: `${weekStart.getMonth() + 1}/${weekStart.getDate()} 주`,
          reviews: totalReviews,
          successRate: sanitizeValue(successRate, 0),
          newContent: 0,
          masteredItems: totalRemembered
        });
      }
      
      return weeklyData;
    })();

    // 월간 트렌드 데이터 - NaN 방지 강화
    const monthlyTrends = safeMonthlyData.map(month => ({
      month: month?.month || 'Unknown',
      totalReviews: sanitizeValue(month?.total_reviews, 0),
      averageScore: sanitizeValue(month?.success_rate, 0),
      contentAdded: 0,
      timeSpent: sanitizeValue((month?.total_reviews || 0) * 2.5, 0)
    }));

    // 카테고리별 분포 - NaN 방지 강화
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6'];
    const categoryDistribution = safeCategoryData.map((category, index) => ({
      name: category?.name || 'Unknown',
      value: sanitizeValue(category?.content_count, 0),
      color: colors[index % colors.length],
      masteryLevel: sanitizeValue(category?.success_rate, 0)
    }));

    // 성과 지표 - 백엔드 데이터 우선 사용
    const performanceMetrics = analyticsData?.performance_metrics ? {
      currentStreak: sanitizeValue(analyticsData.performance_metrics.currentStreak, 0),
      longestStreak: sanitizeValue(analyticsData.performance_metrics.longestStreak, 0),
      totalReviews: sanitizeValue(analyticsData.performance_metrics.totalReviews, 0),
      averageRetention: sanitizeValue(analyticsData.performance_metrics.averageRetention, 0),
      studyEfficiency: sanitizeValue(analyticsData.performance_metrics.studyEfficiency, 0),
      weeklyGoal: sanitizeValue(analyticsData.performance_metrics.weeklyGoal, 7),
      weeklyProgress: sanitizeValue(analyticsData.performance_metrics.weeklyProgress, 0)
    } : {
      // 폴백 로직 (백엔드 데이터가 없는 경우)
      currentStreak: sanitizeValue(analyticsData?.achievement_stats?.current_streak, 0),
      longestStreak: sanitizeValue(analyticsData?.achievement_stats?.max_streak, 0),
      totalReviews: sanitizeValue(analyticsData?.learning_insights?.total_reviews, 0),
      averageRetention: sanitizeValue(analyticsData?.learning_insights?.recent_success_rate, 0),
      studyEfficiency: (() => {
        const successRate = sanitizeValue(analyticsData?.learning_insights?.recent_success_rate, 0);
        const currentStreak = sanitizeValue(analyticsData?.achievement_stats?.current_streak, 0);
        const maxStreak = Math.max(1, sanitizeValue(analyticsData?.achievement_stats?.max_streak, 1));
        const efficiency = (successRate / 100) * (currentStreak / maxStreak) * 100;
        return sanitizeValue(efficiency, 0);
      })(),
      weeklyGoal: Math.max(7, sanitizeValue(analyticsData?.achievement_stats?.monthly_target, 28) / 4),
      weeklyProgress: sanitizeValue(analyticsData?.learning_insights?.recent_7d_reviews, 0)
    };

    return {
      weeklyProgress,
      monthlyTrends,
      categoryDistribution,
      performanceMetrics
    };
  }, [analyticsData, calendarData]);

  if (isLoading || analyticsLoading || calendarLoading) {
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
        streakDays={dashboardData?.streak_days || 0}
        totalContent={dashboardData?.total_content || 0}
        successRate={dashboardData?.success_rate || 0}
      />

      {/* Quick Actions & Tips */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        <QuickActions />
        <LearningTips />
      </div>
      
      {/* 상세 학습 분석 */}
      {progressData && (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl shadow-xl border border-gray-200/60 dark:border-gray-700/60 p-8 hover:shadow-2xl transition-all duration-300 mb-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
                <span className="text-3xl mr-3">📊</span>
                상세 학습 분석
              </h2>
              <p className="text-gray-600 dark:text-gray-300 mt-2 text-base">
                학습 패턴과 성과 지표를 종합적으로 분석한 결과입니다
              </p>
            </div>
            <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 dark:from-blue-900/50 dark:to-indigo-900/50 text-blue-900 dark:text-blue-200 border border-blue-200 dark:border-blue-700/50 shadow-md">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></div>
              실시간 데이터
            </span>
          </div>
          <ProgressVisualization data={progressData} onGoalUpdate={handleGoalUpdate} />
        </div>
      )}
      
      {/* 학습 캘린더 */}
      {calendarData && calendarData.calendar_data && (
        <div className="mb-8">
          <LearningCalendar calendarData={calendarData} />
        </div>
      )}

    </div>
  );
};

export default SimpleDashboard;