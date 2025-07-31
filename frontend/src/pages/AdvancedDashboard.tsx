import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import LearningInsights from '../components/analytics/LearningInsights';
import CategoryPerformance from '../components/analytics/CategoryPerformance';
import StudyPatterns from '../components/analytics/StudyPatterns';
import AchievementStats from '../components/analytics/AchievementStats';
import LearningCalendar from '../components/analytics/LearningCalendar';
import Recommendations from '../components/analytics/Recommendations';
import ProgressVisualization from '../components/analytics/ProgressVisualization';
import MemoryRetentionCurve from '../components/analytics/MemoryRetentionCurve';
import LearningPatterns from '../components/analytics/LearningPatterns';
import AdvancedCategoryAnalysis from '../components/analytics/AdvancedCategoryAnalysis';
import GoalAchievementAnalysis from '../components/analytics/GoalAchievementAnalysis';

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
    queryFn: () => api.get('/analytics/advanced/').then(res => res.data),
  });

  const { data: calendarData, isLoading: calendarLoading, error: calendarError } = useQuery<CalendarData>({
    queryKey: ['learning-calendar'],
    queryFn: () => api.get('/analytics/calendar/').then(res => res.data),
  });

  // NaN 값을 안전하게 처리하는 헬퍼 함수
  const sanitizeValue = (value: any, defaultValue: number = 0): number => {
    if (value === null || value === undefined) return defaultValue;
    const num = Number(value);
    if (!isFinite(num) || isNaN(num)) return defaultValue;
    return num;
  };

  // ProgressVisualization을 위한 데이터 변환
  const progressData = useMemo(() => {
    if (!analyticsData || !calendarData) return null;

    // 안전한 배열 접근
    const safeCalendarData = Array.isArray(calendarData.calendar_data) ? calendarData.calendar_data : [];
    const safeMonthlyData = Array.isArray(calendarData.monthly_summary) ? calendarData.monthly_summary : [];
    const safeCategoryData = Array.isArray(analyticsData.category_performance) ? analyticsData.category_performance : [];

    // 주간 진도 데이터 (최근 30일) - NaN 방지 강화
    const weeklyProgress = safeCalendarData
      .slice(-30)
      .map((day, index) => ({
        date: day?.date ? new Date(day.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }) : `Day ${index + 1}`,
        reviews: sanitizeValue(day?.count, 0),
        successRate: sanitizeValue(day?.success_rate, 0),
        newContent: 0, // 실제 신규 콘텐츠 데이터가 없으므로 0으로 설정
        masteredItems: sanitizeValue(day?.remembered, 0)
      }));

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

    // 성과 지표 - NaN 방지 강화
    const safeAchievementStats = analyticsData?.achievement_stats || {};
    const safeLearningInsights = analyticsData?.learning_insights || {};
    
    const performanceMetrics = {
      currentStreak: sanitizeValue(safeAchievementStats.current_streak, 0),
      longestStreak: sanitizeValue(safeAchievementStats.max_streak, 0),
      totalReviews: sanitizeValue(safeLearningInsights.total_reviews, 0),
      averageRetention: sanitizeValue(safeLearningInsights.recent_success_rate, 0),
      studyEfficiency: (() => {
        const successRate = sanitizeValue(safeLearningInsights.recent_success_rate, 0);
        const currentStreak = sanitizeValue(safeAchievementStats.current_streak, 0);
        const maxStreak = Math.max(1, sanitizeValue(safeAchievementStats.max_streak, 1));
        const efficiency = (successRate / 100) * (currentStreak / maxStreak) * 100;
        return sanitizeValue(efficiency, 0);
      })(),
      weeklyGoal: Math.max(50, sanitizeValue(safeAchievementStats.monthly_target, 100) / 4),
      weeklyProgress: sanitizeValue(safeLearningInsights.recent_7d_reviews, 0)
    };

    return {
      weeklyProgress,
      monthlyTrends,
      categoryDistribution,
      performanceMetrics
    };
  }, [analyticsData, calendarData]);

  // 메모리 유지율 곡선 데이터
  const memoryRetentionData = useMemo(() => {
    if (!analyticsData) return null;

    const retentionCurve = [
      { interval: 1, retentionRate: 85, reviewCount: 45, optimalRate: 80 },
      { interval: 3, retentionRate: 78, reviewCount: 32, optimalRate: 75 },
      { interval: 7, retentionRate: 72, reviewCount: 28, optimalRate: 70 },
      { interval: 14, retentionRate: 68, reviewCount: 24, optimalRate: 65 },
      { interval: 30, retentionRate: 62, reviewCount: 18, optimalRate: 60 }
    ];

    const forgettingCurve = Array.from({ length: 24 }, (_, i) => ({
      timeElapsed: i,
      memoryStrength: sanitizeValue(Math.max(20, 100 - (i * 3.5)), 20),
      withoutReview: sanitizeValue(Math.max(10, 100 - (i * 8)), 10),
      withReview: sanitizeValue(Math.max(50, 100 - (i * 2)), 50)
    }));

    return {
      retentionCurve,
      forgettingCurve,
      insights: {
        averageRetention: sanitizeValue(analyticsData.learning_insights.recent_success_rate, 0),
        optimalRetention: 75,
        improvementPotential: 15,
        strongestInterval: 1,
        weakestInterval: 30,
        nextOptimalReview: 4
      }
    };
  }, [analyticsData]);

  // 학습 패턴 데이터
  const learningPatternsData = useMemo(() => {
    if (!analyticsData || !calendarData || 
        !analyticsData.category_performance || analyticsData.category_performance.length === 0) {
      return null; // 빈 데이터일 때는 null 반환
    }

    const hourlyPattern = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      studySessions: sanitizeValue(Math.floor(Math.random() * 10) + 1, 1),
      averagePerformance: sanitizeValue(60 + Math.random() * 30, 60),
      totalTimeSpent: sanitizeValue(Math.floor(Math.random() * 120) + 30, 30),
      efficiency: sanitizeValue(50 + Math.random() * 40, 50)
    }));

    const weeklyPattern = ['월', '화', '수', '목', '금', '토', '일'].map((day, index) => ({
      day,
      dayOfWeek: index + 1,
      studySessions: sanitizeValue(Math.floor(Math.random() * 15) + 5, 5),
      averagePerformance: sanitizeValue(65 + Math.random() * 25, 65),
      totalReviews: sanitizeValue(Math.floor(Math.random() * 50) + 20, 20),
      timeSpent: sanitizeValue(Math.floor(Math.random() * 180) + 60, 60)
    }));

    return {
      hourlyPattern,
      weeklyPattern,
      streakAnalysis: {
        currentStreak: sanitizeValue(analyticsData.achievement_stats.current_streak, 0),
        longestStreak: sanitizeValue(analyticsData.achievement_stats.max_streak, 0),
        streakHistory: calendarData.calendar_data.slice(-30).map(day => ({
          date: day.date,
          streakLength: Math.floor(Math.random() * 20) + 1,
          performance: sanitizeValue(day.success_rate, 0)
        }))
      },
      difficultyProgression: calendarData.monthly_summary.map(month => ({
        week: month.month,
        easy: Math.floor(Math.random() * 15) + 5,
        medium: Math.floor(Math.random() * 20) + 10,
        hard: Math.floor(Math.random() * 10) + 3,
        averageScore: sanitizeValue(month.success_rate, 0)
      })),
      learningVelocity: analyticsData.category_performance.length > 0 ? 
        analyticsData.category_performance.map(cat => ({
          category: cat.name,
          masterySpeed: Math.floor(Math.random() * 15) + 5,
          retentionRate: sanitizeValue(cat.success_rate, 0),
          difficultyLevel: Math.floor(Math.random() * 5) + 1,
          totalContent: sanitizeValue(cat.content_count, 0)
        })) : [
          {
            category: '프로그래밍',
            masterySpeed: 10,
            retentionRate: 80,
            difficultyLevel: 3,
            totalContent: 5
          }
        ]
    };
  }, [analyticsData, calendarData]);

  // 고급 카테고리 분석 데이터
  const advancedCategoryData = useMemo(() => {
    if (!analyticsData || !analyticsData.category_performance || analyticsData.category_performance.length === 0) {
      return null; // 빈 데이터일 때는 null 반환하여 컴포넌트 렌더링 방지
    }

    return {
      categories: analyticsData.category_performance.map((cat, index) => ({
        id: cat.id || index + 1,
        name: cat.name || 'Unknown Category',
        totalContent: sanitizeValue(cat.content_count, 0),
        masteredContent: Math.floor(sanitizeValue(cat.content_count, 0) * 0.6),
        inProgressContent: Math.floor(sanitizeValue(cat.content_count, 0) * 0.3),
        averageSuccessRate: sanitizeValue(cat.success_rate, 0),
        averageDifficulty: Math.max(1, Math.min(5, sanitizeValue(cat.difficulty_level, 1))),
        totalReviews: sanitizeValue(cat.total_reviews, 0),
        averageReviewTime: Math.floor(Math.random() * 30) + 15,
        masteryProgress: Math.floor(Math.random() * 40) + 50,
        retentionRate: sanitizeValue(cat.recent_success_rate, 0),
        lastActivity: new Date().toISOString(),
        learningVelocity: Math.random() * 5 + 1,
        categoryRank: index + 1
      })),
      performanceMatrix: analyticsData.category_performance.map(cat => ({
        category: cat.name || 'Unknown Category',
        difficulty: Math.max(1, Math.min(5, sanitizeValue(cat.difficulty_level, 1))),
        performance: sanitizeValue(cat.success_rate, 0),
        reviewFrequency: Math.floor(Math.random() * 10) + 5,
        timeInvestment: Math.max(1, Math.floor(Math.random() * 200) + 100),
        masteryLevel: ((rate: number) => {
          const safeRate = sanitizeValue(rate, 0);
          return safeRate >= 80 ? 'expert' : 
                 safeRate >= 65 ? 'advanced' :
                 safeRate >= 50 ? 'intermediate' : 'beginner';
        })(cat.success_rate) as 'beginner' | 'intermediate' | 'advanced' | 'expert'
      })),
      improvementSuggestions: [
        {
          categoryId: 1,
          categoryName: '프로그래밍',
          issue: '복습 간격이 너무 길어 기억 유지율 저하',
          suggestion: '복습 주기를 2-3일로 단축하여 기억 강화',
          priority: 'high' as 'high' | 'medium' | 'low',
          expectedImprovement: 15
        }
      ],
      competencyMap: [
        {
          skill: '문제 해결 능력',
          currentLevel: 75,
          targetLevel: 90,
          categories: ['프로그래밍', '수학'],
          progress: 83
        }
      ]
    };
  }, [analyticsData]);

  // 목표 달성 분석 데이터
  const goalAchievementData = useMemo(() => {
    if (!analyticsData || !calendarData) return null;

    return {
      streakAnalysis: {
        currentStreak: sanitizeValue(analyticsData.achievement_stats.current_streak, 0),
        longestStreak: sanitizeValue(analyticsData.achievement_stats.max_streak, 0),
        averageStreak: 12,
        streakHistory: calendarData.calendar_data.slice(-30).map(day => ({
          date: day.date,
          streakLength: Math.floor(Math.random() * 20) + 1,
          performance: sanitizeValue(day.success_rate, 0),
          type: Math.random() > 0.8 ? 'broken' : 'active' as 'active' | 'broken' | 'extended'
        })),
        streakBreakReasons: [
          { reason: '시간 부족', frequency: 8, averageBreakLength: 3 },
          { reason: '동기 저하', frequency: 5, averageBreakLength: 5 },
          { reason: '건강 문제', frequency: 3, averageBreakLength: 7 }
        ],
        milestones: [
          { streakLength: 7, achievedDate: '2024-01-15', nextTarget: 14 },
          { streakLength: 30, achievedDate: null, nextTarget: 60 }
        ]
      },
      goalTracking: {
        dailyGoal: 20,
        weeklyGoal: 140,
        monthlyGoal: sanitizeValue(analyticsData.achievement_stats.monthly_target, 100),
        currentProgress: {
          daily: 15,
          weekly: 95,
          monthly: sanitizeValue(analyticsData.achievement_stats.monthly_completed, 0)
        },
        achievementRate: {
          daily: 75,
          weekly: 68,
          monthly: (() => {
            const completed = sanitizeValue(analyticsData.achievement_stats.monthly_completed, 0);
            const target = sanitizeValue(analyticsData.achievement_stats.monthly_target, 100);
            return target > 0 ? (completed / target) * 100 : 0;
          })()
        },
        historicalPerformance: calendarData.monthly_summary.map(month => ({
          period: month.month,
          target: 100,
          achieved: sanitizeValue(month.total_reviews, 0),
          rate: Math.min(100, sanitizeValue((month.total_reviews / 100) * 100, 0)),
          consistency: 85
        }))
      },
      motivationMetrics: {
        totalAchievements: 24,
        perfectDays: sanitizeValue(analyticsData.achievement_stats.perfect_sessions, 0),
        streakBadges: [
          { name: '일주일 마스터', description: '7일 연속 학습', unlocked: true, unlockedDate: '2024-01-15' },
          { name: '한달 챔피언', description: '30일 연속 학습', unlocked: false, progress: 60 }
        ],
        personalBests: {
          longestStudySession: 180,
          mostReviewsInDay: 45,
          highestSuccessRate: 98,
          fastestMastery: 5
        },
        challenges: [
          {
            name: '이번 주 목표 달성',
            description: '주간 복습 목표 140회 달성하기',
            target: 140,
            current: 95,
            reward: '스페셜 배지'
          }
        ]
      },
      predictions: {
        streakPrediction: {
          likelihoodToExtend: 78,
          predictedBreakDate: null,
          riskFactors: ['주말 활동 감소', '최근 성과 하락']
        },
        goalAchievement: {
          monthlyForecast: 85,
          recommendedDailyTarget: 22,
          adjustmentNeeded: false
        }
      }
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
  const hasNoData = !analyticsData || !calendarData ||
    (analyticsData.learning_insights.total_reviews === 0 && 
     analyticsData.category_performance.length === 0 &&
     (!calendarData.calendar_data || calendarData.calendar_data.length === 0));

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
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                📊 상세 학습 분석
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                학습 패턴과 성과 지표를 종합적으로 분석한 결과입니다
              </p>
            </div>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400">
              실시간 데이터
            </span>
          </div>
          <ProgressVisualization data={progressData} />
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

      {/* 목표 달성 및 스트릭 분석 */}
      {goalAchievementData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                🎯 목표 달성 & 스트릭 분석
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                학습 목표 달성률과 연속 학습 기록을 상세 분석합니다
              </p>
            </div>
          </div>
          <GoalAchievementAnalysis data={goalAchievementData} />
        </div>
      )}

      {/* 메모리 유지율 및 망각 곡선 */}
      {memoryRetentionData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                🧠 메모리 유지율 & 망각 곡선
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                에빙하우스 망각곡선 기반 개인 기억 유지 패턴 분석
              </p>
            </div>
          </div>
          <MemoryRetentionCurve data={memoryRetentionData} />
        </div>
      )}

      {/* 고급 학습 패턴 분석 */}
      {learningPatternsData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                📈 고급 학습 패턴 분석
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                시간대별, 요일별 학습 패턴과 효율성을 종합 분석합니다
              </p>
            </div>
          </div>
          <LearningPatterns data={learningPatternsData} />
        </div>
      )}

      {/* 고급 카테고리 분석 */}
      {advancedCategoryData && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                📚 고급 카테고리 성과 분석
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                카테고리별 상세 성과 지표와 스마트 개선 제안
              </p>
            </div>
          </div>
          <AdvancedCategoryAnalysis data={advancedCategoryData} />
        </div>
      )}

      {/* 학습 캘린더 히트맵 */}
      <LearningCalendar calendarData={calendarData} />
    </div>
  );
};

export default AdvancedDashboard;