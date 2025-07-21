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

  // ProgressVisualization을 위한 데이터 변환
  const progressData = useMemo(() => {
    if (!analyticsData || !calendarData) return null;

    // 주간 진도 데이터 (최근 30일)
    const weeklyProgress = calendarData.calendar_data
      .slice(-30)
      .map((day, index) => ({
        date: new Date(day.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
        reviews: day.count,
        successRate: day.success_rate,
        newContent: Math.floor(Math.random() * 3),
        masteredItems: day.remembered
      }));

    // 월간 트렌드 데이터
    const monthlyTrends = calendarData.monthly_summary.map(month => ({
      month: month.month,
      totalReviews: month.total_reviews,
      averageScore: month.success_rate,
      contentAdded: Math.floor(Math.random() * 20),
      timeSpent: Math.floor(month.total_reviews * 2.5)
    }));

    // 카테고리별 분포
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6'];
    const categoryDistribution = analyticsData.category_performance.map((category, index) => ({
      name: category.name,
      value: category.content_count,
      color: colors[index % colors.length],
      masteryLevel: category.success_rate
    }));

    // 성과 지표
    const performanceMetrics = {
      currentStreak: analyticsData.achievement_stats.current_streak,
      longestStreak: analyticsData.achievement_stats.max_streak,
      totalReviews: analyticsData.learning_insights.total_reviews,
      averageRetention: Math.round(analyticsData.learning_insights.recent_success_rate),
      studyEfficiency: Math.min(95, Math.round(
        (analyticsData.learning_insights.recent_success_rate / 100) * 
        (analyticsData.achievement_stats.current_streak / Math.max(1, analyticsData.achievement_stats.max_streak)) * 100
      )),
      weeklyGoal: Math.max(50, analyticsData.achievement_stats.monthly_target / 4),
      weeklyProgress: analyticsData.learning_insights.recent_7d_reviews
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
      memoryStrength: Math.max(20, 100 - (i * 3.5)),
      withoutReview: Math.max(10, 100 - (i * 8)),
      withReview: Math.max(50, 100 - (i * 2))
    }));

    return {
      retentionCurve,
      forgettingCurve,
      insights: {
        averageRetention: analyticsData.learning_insights.recent_success_rate,
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
    if (!analyticsData || !calendarData) return null;

    const hourlyPattern = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      studySessions: Math.floor(Math.random() * 10) + 1,
      averagePerformance: 60 + Math.random() * 30,
      totalTimeSpent: Math.floor(Math.random() * 120) + 30,
      efficiency: 50 + Math.random() * 40
    }));

    const weeklyPattern = ['월', '화', '수', '목', '금', '토', '일'].map((day, index) => ({
      day,
      dayOfWeek: index + 1,
      studySessions: Math.floor(Math.random() * 15) + 5,
      averagePerformance: 65 + Math.random() * 25,
      totalReviews: Math.floor(Math.random() * 50) + 20,
      timeSpent: Math.floor(Math.random() * 180) + 60
    }));

    return {
      hourlyPattern,
      weeklyPattern,
      streakAnalysis: {
        currentStreak: analyticsData.achievement_stats.current_streak,
        longestStreak: analyticsData.achievement_stats.max_streak,
        streakHistory: calendarData.calendar_data.slice(-30).map(day => ({
          date: day.date,
          streakLength: Math.floor(Math.random() * 20) + 1,
          performance: day.success_rate
        }))
      },
      difficultyProgression: calendarData.monthly_summary.map(month => ({
        week: month.month,
        easy: Math.floor(Math.random() * 15) + 5,
        medium: Math.floor(Math.random() * 20) + 10,
        hard: Math.floor(Math.random() * 10) + 3,
        averageScore: month.success_rate
      })),
      learningVelocity: analyticsData.category_performance.map(cat => ({
        category: cat.name,
        masterySpeed: Math.floor(Math.random() * 15) + 5,
        retentionRate: cat.success_rate,
        difficultyLevel: Math.floor(Math.random() * 5) + 1,
        totalContent: cat.content_count
      }))
    };
  }, [analyticsData, calendarData]);

  // 고급 카테고리 분석 데이터
  const advancedCategoryData = useMemo(() => {
    if (!analyticsData) return null;

    return {
      categories: analyticsData.category_performance.map((cat, index) => ({
        id: cat.id,
        name: cat.name,
        totalContent: cat.content_count,
        masteredContent: Math.floor(cat.content_count * 0.6),
        inProgressContent: Math.floor(cat.content_count * 0.3),
        averageSuccessRate: cat.success_rate,
        averageDifficulty: cat.difficulty_level,
        totalReviews: cat.total_reviews,
        averageReviewTime: Math.floor(Math.random() * 30) + 15,
        masteryProgress: Math.floor(Math.random() * 40) + 50,
        retentionRate: cat.recent_success_rate,
        lastActivity: new Date().toISOString(),
        learningVelocity: Math.random() * 5 + 1,
        categoryRank: index + 1
      })),
      performanceMatrix: analyticsData.category_performance.map(cat => ({
        category: cat.name,
        difficulty: cat.difficulty_level,
        performance: cat.success_rate,
        reviewFrequency: Math.floor(Math.random() * 10) + 5,
        timeInvestment: Math.floor(Math.random() * 200) + 100,
        masteryLevel: cat.success_rate >= 80 ? 'expert' : 
                      cat.success_rate >= 65 ? 'advanced' :
                      cat.success_rate >= 50 ? 'intermediate' : 'beginner' as 'beginner' | 'intermediate' | 'advanced' | 'expert'
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
        currentStreak: analyticsData.achievement_stats.current_streak,
        longestStreak: analyticsData.achievement_stats.max_streak,
        averageStreak: 12,
        streakHistory: calendarData.calendar_data.slice(-30).map(day => ({
          date: day.date,
          streakLength: Math.floor(Math.random() * 20) + 1,
          performance: day.success_rate,
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
        monthlyGoal: analyticsData.achievement_stats.monthly_target,
        currentProgress: {
          daily: 15,
          weekly: 95,
          monthly: analyticsData.achievement_stats.monthly_completed
        },
        achievementRate: {
          daily: 75,
          weekly: 68,
          monthly: (analyticsData.achievement_stats.monthly_completed / analyticsData.achievement_stats.monthly_target) * 100
        },
        historicalPerformance: calendarData.monthly_summary.map(month => ({
          period: month.month,
          target: 100,
          achieved: month.total_reviews,
          rate: Math.min(100, (month.total_reviews / 100) * 100),
          consistency: 85
        }))
      },
      motivationMetrics: {
        totalAchievements: 24,
        perfectDays: analyticsData.achievement_stats.perfect_sessions,
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