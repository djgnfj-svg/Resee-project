import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import LearningInsights from '../components/analytics/LearningInsights';
import CategoryPerformance from '../components/analytics/CategoryPerformance';
import StudyPatterns from '../components/analytics/StudyPatterns';
import AchievementStats from '../components/analytics/AchievementStats';
import LearningCalendar from '../components/analytics/LearningCalendar';
import Recommendations from '../components/analytics/Recommendations';

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
  const { data: analyticsData, isLoading: analyticsLoading, error: analyticsError } = useQuery<AdvancedAnalyticsData>({
    queryKey: ['advanced-analytics'],
    queryFn: () => api.get('/analytics/advanced/').then((res: any) => res.data),
  });

  const { data: calendarData, isLoading: calendarLoading, error: calendarError } = useQuery<CalendarData>({
    queryKey: ['learning-calendar'],
    queryFn: () => api.get('/analytics/calendar/').then((res: any) => res.data),
  });

  if (analyticsLoading || calendarLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner />
      </div>
    );
  }

  if (analyticsError || calendarError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
              데이터를 불러오는 중 오류가 발생했습니다
            </h3>
            <div className="mt-2 text-sm text-red-700 dark:text-red-300">
              잠시 후 다시 시도해 주세요.
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analyticsData || !calendarData) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 dark:text-gray-400">데이터가 없습니다.</div>
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
              AI 기반 개인화된 학습 인사이트와 추천
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
      <LearningCalendar calendarData={calendarData} />
    </div>
  );
};

export default AdvancedDashboard;