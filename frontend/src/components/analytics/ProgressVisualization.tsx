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
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
  RadialBarChart,
  RadialBar
} from 'recharts';
import { 
  ArrowArrowTrendingUpIcon, 
  ArrowArrowTrendingDownIcon, 
  MinusIcon,
  FireIcon,
  AcademicCapIcon,
  ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface ProgressVisualizationProps {
  data: {
    weeklyProgress: Array<{
      date: string;
      reviews: number;
      successRate: number;
      newContent: number;
      masteredItems: number;
    }>;
    monthlyTrends: Array<{
      month: string;
      totalReviews: number;
      averageScore: number;
      contentAdded: number;
      timeSpent: number;
    }>;
    categoryDistribution: Array<{
      name: string;
      value: number;
      color: string;
      masteryLevel: number;
    }>;
    performanceMetrics: {
      currentStreak: number;
      longestStreak: number;
      totalReviews: number;
      averageRetention: number;
      studyEfficiency: number;
      weeklyGoal: number;
      weeklyProgress: number;
    };
  };
}

const COLORS = {
  primary: '#3b82f6',
  success: '#10b981', 
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  indigo: '#6366f1',
  pink: '#ec4899',
  teal: '#14b8a6'
};

const ProgressVisualization: React.FC<ProgressVisualizationProps> = ({ data }) => {
  const { weeklyProgress, monthlyTrends, categoryDistribution, performanceMetrics } = data;

  // 성과 지표 계산
  const performanceInsights = useMemo(() => {
    const recent = weeklyProgress.slice(-7);
    const previousWeek = weeklyProgress.slice(-14, -7);
    
    const recentAvgSuccess = recent.reduce((sum, day) => sum + day.successRate, 0) / recent.length;
    const prevAvgSuccess = previousWeek.length > 0 
      ? previousWeek.reduce((sum, day) => sum + day.successRate, 0) / previousWeek.length 
      : recentAvgSuccess;
    
    const trend = recentAvgSuccess - prevAvgSuccess;
    const trendPercent = ((recentAvgSuccess - prevAvgSuccess) / prevAvgSuccess * 100);

    return {
      trend: trend > 1 ? 'up' : trend < -1 ? 'down' : 'stable',
      trendPercent: Math.abs(trendPercent),
      recentSuccess: recentAvgSuccess,
      totalReviewsThisWeek: recent.reduce((sum, day) => sum + day.reviews, 0)
    };
  }, [weeklyProgress]);

  // 주간 목표 진행률
  const weeklyProgressPercent = Math.min((performanceMetrics.weeklyProgress / performanceMetrics.weeklyGoal) * 100, 100);

  const formatTooltipValue = (value: number, name: string) => {
    if (name.includes('Rate') || name.includes('율')) {
      return [`${value.toFixed(1)}%`, name];
    }
    if (name.includes('Time') || name.includes('시간')) {
      return [`${value}분`, name];
    }
    return [value, name];
  };

  return (
    <div className="space-y-6">
      {/* 핵심 성과 지표 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 현재 스트릭 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">연속 학습</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {performanceMetrics.currentStreak}일
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center">
              <FireIcon className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              최고 기록: {performanceMetrics.longestStreak}일
            </div>
          </div>
        </div>

        {/* 주간 진행률 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">주간 목표</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {weeklyProgressPercent.toFixed(0)}%
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <ChartBarIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="mt-4">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 rounded-full h-2 transition-all duration-300"
                style={{ width: `${weeklyProgressPercent}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {performanceMetrics.weeklyProgress}/{performanceMetrics.weeklyGoal} 복습 완료
            </div>
          </div>
        </div>

        {/* 성공률 트렌드 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">평균 정답률</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {performanceInsights.recentSuccess.toFixed(1)}%
              </p>
            </div>
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              performanceInsights.trend === 'up' 
                ? 'bg-green-100 dark:bg-green-900/30' 
                : performanceInsights.trend === 'down'
                ? 'bg-red-100 dark:bg-red-900/30'
                : 'bg-gray-100 dark:bg-gray-700'
            }`}>
              {performanceInsights.trend === 'up' ? (
                <ArrowTrendingUpIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
              ) : performanceInsights.trend === 'down' ? (
                <ArrowTrendingDownIcon className="w-6 h-6 text-red-600 dark:text-red-400" />
              ) : (
                <MinusIcon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              )}
            </div>
          </div>
          <div className="mt-4">
            <div className={`text-xs ${
              performanceInsights.trend === 'up' 
                ? 'text-green-600 dark:text-green-400' 
                : performanceInsights.trend === 'down'
                ? 'text-red-600 dark:text-red-400'
                : 'text-gray-500 dark:text-gray-400'
            }`}>
              {performanceInsights.trend !== 'stable' && (
                <>
                  {performanceInsights.trend === 'up' ? '↗' : '↘'} {performanceInsights.trendPercent.toFixed(1)}% 
                  {performanceInsights.trend === 'up' ? '향상' : '감소'}
                </>
              )}
              {performanceInsights.trend === 'stable' && '안정적 유지'}
            </div>
          </div>
        </div>

        {/* 총 복습 횟수 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 복습</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {performanceMetrics.totalReviews.toLocaleString()}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
              <AcademicCapIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              이번 주: {performanceInsights.totalReviewsThisWeek}회
            </div>
          </div>
        </div>
      </div>

      {/* 주간 학습 진도 차트 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          📈 주간 학습 진도
        </h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={weeklyProgress}>
              <defs>
                <linearGradient id="reviewsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="successGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.success} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={COLORS.success} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                stroke="#9ca3af"
              />
              <YAxis 
                yAxisId="left"
                tick={{ fontSize: 12 }}
                stroke="#9ca3af"
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                stroke="#9ca3af"
              />
              <Tooltip 
                formatter={formatTooltipValue}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px'
                }}
              />
              <Legend />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="reviews"
                stroke={COLORS.primary}
                fill="url(#reviewsGradient)"
                name="복습 횟수"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="successRate"
                stroke={COLORS.success}
                strokeWidth={3}
                dot={{ fill: COLORS.success }}
                name="정답률 (%)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 월간 학습 패턴 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            📊 월간 학습 패턴
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                />
                <Tooltip 
                  formatter={formatTooltipValue}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Bar 
                  dataKey="totalReviews" 
                  fill={COLORS.primary} 
                  name="월간 복습"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 카테고리별 분포 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            🎯 카테고리별 학습 분포
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {categoryDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => [value, '콘텐츠 수']}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Legend 
                  wrapperStyle={{ fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 학습 효율성 레이더 차트 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          ⚡ 학습 효율성 분석
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 원형 진행률 표시기들 */}
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <div className="w-24 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart data={[{ name: 'Retention', value: performanceMetrics.averageRetention, fill: COLORS.success }]}>
                    <RadialBar dataKey="value" cornerRadius={10} fill={COLORS.success} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {performanceMetrics.averageRetention}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">평균 기억 유지율</p>
          </div>

          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <div className="w-24 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart data={[{ name: 'Efficiency', value: performanceMetrics.studyEfficiency, fill: COLORS.purple }]}>
                    <RadialBar dataKey="value" cornerRadius={10} fill={COLORS.purple} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {performanceMetrics.studyEfficiency}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">학습 효율성</p>
          </div>

          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <div className="w-24 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart data={[{ name: 'Goal', value: weeklyProgressPercent, fill: COLORS.indigo }]}>
                    <RadialBar dataKey="value" cornerRadius={10} fill={COLORS.indigo} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {weeklyProgressPercent.toFixed(0)}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">목표 달성률</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressVisualization;