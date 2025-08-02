import React, { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import api, { weeklyGoalAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import LearningInsights from '../components/analytics/LearningInsights';
import CategoryPerformance from '../components/analytics/CategoryPerformance';
import StudyPatterns from '../components/analytics/StudyPatterns';
import AchievementStats from '../components/analytics/AchievementStats';
import LearningCalendar from '../components/analytics/LearningCalendar';
import Recommendations from '../components/analytics/Recommendations';
import ProgressVisualization from '../components/analytics/ProgressVisualization';
import WeeklyGoalEditor from '../components/WeeklyGoalEditor';

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

const AdvancedDashboard: React.FC = () => {
  const queryClient = useQueryClient();
  
  const { data: analyticsData, isLoading: analyticsLoading, error: analyticsError } = useQuery<AdvancedAnalyticsData>({
    queryKey: ['advanced-analytics'],
    queryFn: () => api.get('/analytics/advanced/').then(res => res.data),
  });

  const { data: calendarData, isLoading: calendarLoading, error: calendarError } = useQuery<CalendarData>({
    queryKey: ['learning-calendar'],
    queryFn: () => api.get('/analytics/calendar/').then(res => {
      console.log('캘린더 API 응답:', res.data);
      return res.data;
    }),
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
          newContent: 0, // 실제 신규 콘텐츠 데이터가 없으므로 0으로 설정
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
      contentAdded: 0, // 실제 월간 콘텐츠 추가 데이터가 없으므로 0으로 설정
      timeSpent: sanitizeValue((month?.total_reviews || 0) * 2.5, 0) // 복습 횟수 기반 추정
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


  if (analyticsLoading || calendarLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner />
      </div>
    );
  }

  // 데이터가 없는 경우 처리
  const hasNoData = !analyticsData ||
    (analyticsData.learning_insights.total_reviews === 0 && 
     analyticsData.category_performance.length === 0);

  if (hasNoData) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-16">
          <div className="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-6">
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            분석할 데이터가 없습니다
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            콘텐츠를 추가하고 복습을 시작하면 상세한 학습 분석을 확인할 수 있습니다.
          </p>
          <div className="space-x-4">
            <a 
              href="/content" 
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              콘텐츠 추가하기
            </a>
            <a 
              href="/review" 
              className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              복습 시작하기
            </a>
          </div>
        </div>
      </div>
    );
  }

  if (analyticsError || calendarError) {
    return (
      <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 border border-red-200 dark:border-red-700/50 rounded-xl p-6 shadow-lg backdrop-blur-sm">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-red-500 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="ml-4">
            <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">
              데이터를 불러오는 중 오류가 발생했습니다
            </h3>
            <div className="mt-2 text-red-700 dark:text-red-300">
              잠시 후 다시 시도해 주세요.
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="text-center py-16">
        <div className="mx-auto w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
          <svg className="w-12 h-12 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <div className="text-xl font-semibold text-gray-600 dark:text-gray-300">데이터가 없습니다.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 페이지 헤더 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              스마트 학습 분석
            </h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              데이터 기반 개인화된 학습 인사이트와 추천
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400">
              실시간 업데이트
            </span>
          </div>
        </div>
      </div>

      {/* 추천 시스템 */}
      {analyticsData.recommendations.length > 0 && (
        <Recommendations recommendations={analyticsData.recommendations} />
      )}

      {/* 고급 진도 시각화 */}
      {progressData && (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl shadow-xl border border-gray-200/60 dark:border-gray-700/60 p-8 hover:shadow-2xl transition-all duration-300">
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

      {/* 학습 인사이트 */}
      <LearningInsights insights={analyticsData.learning_insights} />

      {/* 성취 통계 */}
      <AchievementStats achievements={analyticsData.achievement_stats} />

      {/* 카테고리별 성과와 학습 패턴 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CategoryPerformance categories={analyticsData.category_performance} />
        <StudyPatterns patterns={analyticsData.study_patterns} />
      </div>




      {/* 학습 캘린더 히트맵 */}
      {process.env.NODE_ENV === 'development' && (
        <div className="mb-4 p-3 bg-gray-100 dark:bg-gray-800 rounded text-xs">
          <div>캘린더 로딩: {calendarLoading ? 'true' : 'false'}</div>
          <div>캘린더 에러: {calendarError ? 'true' : 'false'}</div>
          <div>캘린더 데이터 존재: {calendarData ? 'true' : 'false'}</div>
          <div>캘린더 데이터 배열 길이: {calendarData?.calendar_data?.length || 0}</div>
        </div>
      )}
      {calendarData && calendarData.calendar_data ? (
        <LearningCalendar calendarData={calendarData} />
      ) : calendarLoading ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
          </div>
        </div>
      ) : calendarError ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-red-200 dark:border-red-700 p-6">
          <div className="text-center py-8">
            <div className="text-red-600 dark:text-red-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.314 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              캘린더 로딩 실패
            </h3>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              캘린더 데이터를 불러오는 중 오류가 발생했습니다.
            </div>
            <button 
              onClick={() => queryClient.invalidateQueries({ queryKey: ['learning-calendar'] })}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
            >
              다시 시도
            </button>
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg text-left">
                <div className="text-xs text-red-800 dark:text-red-200 font-mono">
                  Error: {(calendarError as any)?.message || calendarError?.toString() || 'Unknown error'}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="text-center py-12">
            <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              캘린더가 비어있습니다
            </h3>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              복습을 시작하면 캘린더에 학습 기록이 표시됩니다!
            </div>
            <div className="space-x-3">
              <a 
                href="/content" 
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
              >
                콘텐츠 추가
              </a>
              <a 
                href="/review" 
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                복습 시작
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdvancedDashboard;