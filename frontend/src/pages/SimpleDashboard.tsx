import React, { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { analyticsAPI } from '../utils/api';
import api, { weeklyGoalAPI } from '../utils/api';
import { DashboardData } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';
import EmptyDashboard from '../components/dashboard/EmptyDashboard';
import ErrorDashboard from '../components/dashboard/ErrorDashboard';
import DashboardHero from '../components/dashboard/DashboardHero';
import StatsCard from '../components/dashboard/StatsCard';
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
  });

  const { data: calendarData, isLoading: calendarLoading } = useQuery<CalendarData>({
    queryKey: ['learning-calendar'],
    queryFn: () => api.get('/analytics/calendar/').then(res => res.data),
    retry: 3,
    retryDelay: 1000,
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


  const stats = [
    {
      name: '오늘의 복습',
      value: dashboardData?.today_reviews || 0,
      unit: '개',
      icon: '🎯',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      name: '복습 연속일',
      value: dashboardData?.streak_days || 0,
      unit: '일',
      icon: '🔥',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50 dark:bg-orange-900/20',
    },
    {
      name: '전체 콘텐츠',
      value: dashboardData?.total_content || 0,
      unit: '개',
      icon: '📖',
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
    },
    {
      name: '복습 성공률',
      value: dashboardData?.success_rate || 0,
      unit: '%',
      icon: '🎉',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    },
  ];

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

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat, index) => (
          <div
            key={`dashboard-stat-${index}`}
            className="relative overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 shadow-lg dark:shadow-gray-700/20 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div className="text-2xl mb-2">{stat.icon}</div>
              <div className="text-right">
                <div className={`text-2xl font-bold ${stat.color}`}>
                  {stat.value}{stat.unit}
                </div>
              </div>
            </div>
            <h3 className="text-gray-700 dark:text-gray-300 font-semibold text-lg">{stat.name}</h3>
            <div className="h-2 bg-gray-100 rounded-full mt-3 overflow-hidden">
              <div 
                className={`h-full ${stat.bgColor} rounded-full transition-all duration-500`}
                style={{width: `${Math.min(stat.value, 100)}%`}}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions & Tips */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-6 shadow-lg dark:shadow-gray-700/20">
          <div className="flex items-center mb-4">
            <div className="text-2xl mr-3">⚡</div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">빠른 액션</h3>
          </div>
          <div className="space-y-3">
            <a 
              href="/content"
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
            <a 
              href="/weekly-test"
              className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-orange-500 to-red-600 px-6 py-4 text-white font-semibold hover:from-orange-600 hover:to-red-700 transition-all duration-300 transform hover:scale-105 block text-center"
            >
              <span className="mr-2">📝</span>
              주간 시험
            </a>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-6 shadow-lg dark:shadow-gray-700/20">
          <div className="flex items-center mb-4">
            <div className="text-2xl mr-3">💡</div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">학습 팁</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-start">
              <div className="text-green-500 mr-3 mt-1">•</div>
              <p className="text-gray-700 dark:text-gray-300">복습은 하루에 조금씩이라도 꾸준히 하는 것이 중요합니다.</p>
            </div>
            <div className="flex items-start">
              <div className="text-yellow-500 mr-3 mt-1">•</div>
              <p className="text-gray-700 dark:text-gray-300">기억이 애매하다면 '애매함'으로 표시하여 더 자주 복습하세요.</p>
            </div>
            <div className="flex items-start">
              <div className="text-purple-500 mr-3 mt-1">•</div>
              <p className="text-gray-700 dark:text-gray-300">카테고리와 태그를 활용하여 체계적으로 정리하세요.</p>
            </div>
          </div>
        </div>
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