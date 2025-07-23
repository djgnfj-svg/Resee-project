import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  // BarChart,
  // Bar,
  PieChart,
  Pie,
  Cell,
  // RadialBarChart,
  // RadialBar
} from 'recharts';
import { 
  FireIcon,
  TrophyIcon,
  // CalendarIcon,
  ClockIcon,
  CheckCircleIcon,
  // ExclamationTriangleIcon,
  ChartBarIcon,
  StarIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

interface GoalAchievementAnalysisProps {
  data: {
    streakAnalysis: {
      currentStreak: number;
      longestStreak: number;
      averageStreak: number;
      streakHistory: Array<{
        date: string;
        streakLength: number;
        performance: number;
        type: 'active' | 'broken' | 'extended';
      }>;
      streakBreakReasons: Array<{
        reason: string;
        frequency: number;
        averageBreakLength: number; // 일 단위
      }>;
      milestones: Array<{
        streakLength: number;
        achievedDate: string | null;
        nextTarget: number;
      }>;
    };
    goalTracking: {
      dailyGoal: number; // 목표 복습 수
      weeklyGoal: number;
      monthlyGoal: number;
      currentProgress: {
        daily: number;
        weekly: number;
        monthly: number;
      };
      achievementRate: {
        daily: number; // %
        weekly: number; // %
        monthly: number; // %
      };
      historicalPerformance: Array<{
        period: string; // 날짜/주/월
        target: number;
        achieved: number;
        rate: number;
        consistency: number; // 일관성 점수
      }>;
    };
    motivationMetrics: {
      totalAchievements: number;
      perfectDays: number; // 100% 목표 달성한 날
      streakBadges: Array<{
        name: string;
        description: string;
        unlocked: boolean;
        unlockedDate?: string;
        progress?: number; // 0-100%
      }>;
      personalBests: {
        longestStudySession: number; // 분
        mostReviewsInDay: number;
        highestSuccessRate: number; // %
        fastestMastery: number; // 콘텐츠 숙달까지 일 수
      };
      challenges: Array<{
        name: string;
        description: string;
        target: number;
        current: number;
        deadline?: string;
        reward: string;
      }>;
    };
    predictions: {
      streakPrediction: {
        likelihoodToExtend: number; // 0-100%
        predictedBreakDate: string | null;
        riskFactors: string[];
      };
      goalAchievement: {
        monthlyForecast: number; // 예상 달성률 %
        recommendedDailyTarget: number;
        adjustmentNeeded: boolean;
      };
    };
  };
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const STREAK_COLORS = {
  active: '#10b981',
  broken: '#ef4444',
  extended: '#3b82f6'
};

const ACHIEVEMENT_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6'];

const GoalAchievementAnalysis: React.FC<GoalAchievementAnalysisProps> = ({ data }) => {
  const { streakAnalysis, goalTracking, motivationMetrics, predictions } = data;

  // NaN 방지를 위한 숫자 정리 유틸리티
  const sanitizeNumber = (value: any, fallback: number = 0): number => {
    if (value === null || value === undefined) return fallback;
    const num = Number(value);
    return isNaN(num) || !isFinite(num) ? fallback : num;
  };

  // 배열 안전 체크
  const safeArray = (arr: any[], fallback: any[] = []): any[] => {
    return Array.isArray(arr) ? arr : fallback;
  };

  // 스트릭 성과 지표 계산
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const streakPerformance = useMemo(() => {
    const safeStreakHistory = safeArray(streakAnalysis.streakHistory);
    const recentStreaks = safeStreakHistory.slice(-30);
    
    // 빈 배열 처리
    const averagePerformance = recentStreaks.length > 0 
      ? sanitizeNumber(recentStreaks.reduce((sum, streak) => sum + sanitizeNumber(streak.performance, 0), 0) / recentStreaks.length)
      : 0;
      
    const consistencyScore = recentStreaks.length > 0 
      ? sanitizeNumber(100 - (recentStreaks.reduce((acc, streak) => {
          return acc + Math.abs(sanitizeNumber(streak.performance, 0) - averagePerformance);
        }, 0) / recentStreaks.length))
      : 100;

    const currentStreak = sanitizeNumber(streakAnalysis.currentStreak);
    const longestStreak = sanitizeNumber(streakAnalysis.longestStreak, 1); // 1로 fallback로 나누기 0 방지
    
    return {
      averagePerformance: Math.round(sanitizeNumber(averagePerformance)),
      consistencyScore: Math.round(Math.max(0, sanitizeNumber(consistencyScore))),
      streakEfficiency: Math.round(sanitizeNumber((currentStreak / longestStreak) * 100)),
      breakRisk: sanitizeNumber(predictions.streakPrediction?.likelihoodToExtend, 50)
    };
  }, [streakAnalysis, predictions]);

  // 목표 달성 트렌드
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const goalTrends = useMemo(() => {
    const safeHistoricalPerformance = safeArray(goalTracking.historicalPerformance);
    const recent = safeHistoricalPerformance.slice(-12);
    
    // 빈 배열이나 비교 불가능한 경우 처리
    const trendSlope = recent.length > 1 ? 
      sanitizeNumber((sanitizeNumber(recent[recent.length - 1].rate) - sanitizeNumber(recent[0].rate)) / recent.length) : 0;
    
    const averageConsistency = recent.length > 0 
      ? sanitizeNumber(recent.reduce((sum, p) => sum + sanitizeNumber(p.consistency, 0), 0) / recent.length)
      : 0;
    
    return {
      trend: trendSlope > 2 ? 'improving' : trendSlope < -2 ? 'declining' : 'stable',
      trendValue: sanitizeNumber(Math.abs(trendSlope)).toFixed(1),
      averageConsistency: Math.round(averageConsistency)
    };
  }, [goalTracking.historicalPerformance]);

  // 배지 진행률 계산
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const badgeProgress = motivationMetrics.streakBadges.filter(badge => !badge.unlocked);
  const unlockedBadges = motivationMetrics.streakBadges.filter(badge => badge.unlocked);

  const formatTooltip = (value: number, name: string) => {
    if (name.includes('Rate') || name.includes('률') || name.includes('%')) {
      return [`${value}%`, name];
    }
    if (name.includes('Day') || name.includes('일')) {
      return [`${value}일`, name];
    }
    return [value, name];
  };

  return (
    <div className="space-y-6">
      {/* 핵심 성과 지표 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-xl p-4 text-white shadow-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100 text-sm">현재 스트릭</p>
              <p className="text-2xl font-bold">{streakAnalysis.currentStreak}일</p>
            </div>
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <FireIcon className="w-6 h-6" />
            </div>
          </div>
          <div className="mt-2 text-xs text-orange-100">
            최고 기록: {streakAnalysis.longestStreak}일
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">월간 목표 달성률</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {goalTracking.achievementRate.monthly}%
              </p>
            </div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              goalTracking.achievementRate.monthly >= 90 
                ? 'bg-green-100 dark:bg-green-900/30' 
                : goalTracking.achievementRate.monthly >= 70
                ? 'bg-yellow-100 dark:bg-yellow-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            }`}>
              <TrophyIcon className={`w-5 h-5 ${
                goalTracking.achievementRate.monthly >= 90 
                  ? 'text-green-600 dark:text-green-400' 
                  : goalTracking.achievementRate.monthly >= 70
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-red-600 dark:text-red-400'
              }`} />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            {goalTracking.currentProgress.monthly}/{goalTracking.monthlyGoal} 완료
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">완벽한 날</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {motivationMetrics.perfectDays}
              </p>
            </div>
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <CheckCircleIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            100% 목표 달성
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">달성한 배지</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {unlockedBadges.length}
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
              <StarIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            총 {motivationMetrics.streakBadges.length}개 중
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 스트릭 히스토리 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            🔥 스트릭 변화 추이
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={streakAnalysis.streakHistory.slice(-30)}>
                <defs>
                  <linearGradient id="streakGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <Tooltip 
                  formatter={formatTooltip}
                  labelFormatter={(date) => `날짜: ${date}`}
                />
                <Area
                  type="monotone"
                  dataKey="streakLength"
                  stroke="#f97316"
                  fillOpacity={1}
                  fill="url(#streakGradient)"
                  name="스트릭 길이"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 목표 달성 트렌드 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            🎯 목표 달성률 추이
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={goalTracking.historicalPerformance.slice(-12)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="period" 
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  domain={[0, 120]}
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <Tooltip formatter={formatTooltip} />
                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ fill: '#3b82f6', r: 4 }}
                  name="달성률"
                />
                <Line
                  type="monotone"
                  dataKey="consistency"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="일관성"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 개인 기록 및 도전 과제 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 개인 최고 기록 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            🏆 개인 최고 기록
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                  <ClockIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">최장 학습 시간</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">연속 학습 세션</p>
                </div>
              </div>
              <span className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                {motivationMetrics.personalBests.longestStudySession}분
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <ChartBarIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">하루 최대 복습</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">단일 일자 기록</p>
                </div>
              </div>
              <span className="text-lg font-bold text-green-600 dark:text-green-400">
                {motivationMetrics.personalBests.mostReviewsInDay}회
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <BoltIcon className="w-4 h-4 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">최고 정답률</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">단일 세션 기록</p>
                </div>
              </div>
              <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {motivationMetrics.personalBests.highestSuccessRate}%
              </span>
            </div>
          </div>
        </div>

        {/* 진행 중인 도전 과제 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            🎯 진행 중인 도전 과제
          </h3>
          <div className="space-y-4">
            {motivationMetrics.challenges.slice(0, 3).map((challenge, index) => {
              const progress = (challenge.current / challenge.target) * 100;
              return (
                <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100">{challenge.name}</h4>
                    <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                      {challenge.current}/{challenge.target}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {challenge.description}
                  </p>
                  <div className="mb-2">
                    <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.min(100, sanitizeNumber(progress))}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500 dark:text-gray-400">
                      진행률: {sanitizeNumber(progress).toFixed(0)}%
                    </span>
                    <span className="text-green-600 dark:text-green-400 font-medium">
                      🎁 {challenge.reward}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 스트릭 중단 원인 분석 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          ⚠️ 스트릭 중단 원인 분석
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={streakAnalysis.streakBreakReasons}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="frequency"
                >
                  {streakAnalysis.streakBreakReasons.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={ACHIEVEMENT_COLORS[index % ACHIEVEMENT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => [value, '횟수']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-3">
            {streakAnalysis.streakBreakReasons.map((reason, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: ACHIEVEMENT_COLORS[index % ACHIEVEMENT_COLORS.length] }}
                  />
                  <span className="font-medium text-gray-900 dark:text-gray-100">{reason.reason}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {reason.frequency}회
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    평균 {reason.averageBreakLength}일 중단
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI 예측 및 권장사항 */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-indigo-200 dark:border-indigo-800">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center">
              <BoltIcon className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-medium text-indigo-900 dark:text-indigo-100 mb-4">
              🤖 AI 예측 및 최적화 제안
            </h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h5 className="font-medium text-indigo-800 dark:text-indigo-200 mb-3">스트릭 예측</h5>
                <div className="space-y-2 text-sm text-indigo-700 dark:text-indigo-300">
                  <div className="flex items-center justify-between">
                    <span>연장 가능성:</span>
                    <span className="font-medium">{predictions.streakPrediction.likelihoodToExtend}%</span>
                  </div>
                  {predictions.streakPrediction.riskFactors.length > 0 && (
                    <div>
                      <span className="font-medium">위험 요소:</span>
                      <ul className="list-disc list-inside mt-1 ml-2">
                        {predictions.streakPrediction.riskFactors.map((risk, idx) => (
                          <li key={idx}>{risk}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
              <div>
                <h5 className="font-medium text-indigo-800 dark:text-indigo-200 mb-3">목표 최적화</h5>
                <div className="space-y-2 text-sm text-indigo-700 dark:text-indigo-300">
                  <div className="flex items-center justify-between">
                    <span>월말 예상 달성률:</span>
                    <span className="font-medium">{predictions.goalAchievement.monthlyForecast}%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>권장 일일 목표:</span>
                    <span className="font-medium">{predictions.goalAchievement.recommendedDailyTarget}회</span>
                  </div>
                  {predictions.goalAchievement.adjustmentNeeded && (
                    <div className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400 p-2 rounded text-xs">
                      ⚡ 목표 조정이 권장됩니다
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GoalAchievementAnalysis;