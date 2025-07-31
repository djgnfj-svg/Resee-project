import React, { useMemo } from 'react';
import {
  // LineChart,
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
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon, 
  MinusIcon,
  FireIcon,
  AcademicCapIcon,
  // ClockIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

// NaN 값을 안전하게 처리하는 헬퍼 함수 (강화된 버전)
const sanitizeNumber = (value: any, defaultValue: number = 0): number => {
  // null, undefined, empty string 처리
  if (value === null || value === undefined || value === '') {
    return defaultValue;
  }
  
  // 문자열을 숫자로 변환 시도
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  
  // NaN, Infinity, -Infinity 처리
  if (isNaN(num) || !isFinite(num)) {
    return defaultValue;
  }
  
  return num;
};

// 데이터 배열의 모든 수치 값을 안전하게 처리
const sanitizeChartData = <T extends Record<string, any>>(data: T[]): T[] => {
  if (!Array.isArray(data)) return [];
  
  return data.map(item => {
    if (!item || typeof item !== 'object') return {} as T;
    
    const sanitizedItem = { ...item } as T;
    Object.keys(sanitizedItem).forEach((key: keyof T) => {
      const value = sanitizedItem[key];
      if (typeof value === 'number' || value === null || value === undefined) {
        (sanitizedItem[key] as any) = sanitizeNumber(value, 0);
      }
    });
    return sanitizedItem;
  });
};

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
  primary: '#0ea5e9',
  success: '#22c55e', 
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  indigo: '#6366f1',
  pink: '#ec4899',
  teal: '#14b8a6'
};

const ProgressVisualization: React.FC<ProgressVisualizationProps> = ({ data }) => {
  // 모든 데이터를 안전하게 처리 (hooks는 항상 같은 순서로 호출되어야 함)
  const safeData = useMemo(() => {
    // 데이터 유효성 검증
    if (!data || !data.weeklyProgress || !data.monthlyTrends || !data.categoryDistribution || !data.performanceMetrics) {
      return {
        weeklyProgress: [],
        monthlyTrends: [],
        categoryDistribution: [],
        performanceMetrics: {
          currentStreak: 0,
          longestStreak: 0,
          totalReviews: 0,
          averageRetention: 0,
          studyEfficiency: 0,
          weeklyGoal: 50,
          weeklyProgress: 0
        }
      };
    }

    return {
      weeklyProgress: sanitizeChartData(data.weeklyProgress || []),
      monthlyTrends: sanitizeChartData(data.monthlyTrends || []),
      categoryDistribution: sanitizeChartData((data.categoryDistribution || []).map(item => ({
        ...item,
        value: sanitizeNumber(item.value, 0),
        masteryLevel: sanitizeNumber(item.masteryLevel, 0)
      }))),
      performanceMetrics: {
        currentStreak: sanitizeNumber(data.performanceMetrics?.currentStreak, 0),
        longestStreak: sanitizeNumber(data.performanceMetrics?.longestStreak, 0),
        totalReviews: sanitizeNumber(data.performanceMetrics?.totalReviews, 0),
        averageRetention: sanitizeNumber(data.performanceMetrics?.averageRetention, 0),
        studyEfficiency: sanitizeNumber(data.performanceMetrics?.studyEfficiency, 0),
        weeklyGoal: sanitizeNumber(data.performanceMetrics?.weeklyGoal, 50),
        weeklyProgress: sanitizeNumber(data.performanceMetrics?.weeklyProgress, 0)
      }
    };
  }, [data]);

  // 성과 지표 계산 (hooks는 항상 같은 순서로 호출되어야 함)
  const performanceInsights = useMemo(() => {
    const safeWeeklyProgress = Array.isArray(safeData.weeklyProgress) ? safeData.weeklyProgress : [];
    const recent = safeWeeklyProgress.slice(-7);
    const previousWeek = safeWeeklyProgress.slice(-14, -7);
    
    // 빈 배열 처리
    const recentAvgSuccess = recent.length > 0 
      ? sanitizeNumber(recent.reduce((sum, day) => sum + sanitizeNumber(day.successRate, 0), 0) / recent.length)
      : 0;
    
    const prevAvgSuccess = previousWeek.length > 0 
      ? sanitizeNumber(previousWeek.reduce((sum, day) => sum + sanitizeNumber(day.successRate, 0), 0) / previousWeek.length)
      : recentAvgSuccess;
    
    const trend = sanitizeNumber(recentAvgSuccess - prevAvgSuccess);
    // 안전한 백분율 계산 - 모든 경우에 대해 NaN 방지
    let trendPercent = 0;
    if (prevAvgSuccess !== 0 && !isNaN(prevAvgSuccess) && !isNaN(recentAvgSuccess)) {
      trendPercent = sanitizeNumber((recentAvgSuccess - prevAvgSuccess) / prevAvgSuccess * 100);
    }

    return {
      trend: trend > 1 ? 'up' : trend < -1 ? 'down' : 'stable',
      trendPercent: sanitizeNumber(Math.abs(trendPercent)),
      recentSuccess: sanitizeNumber(recentAvgSuccess),
      totalReviewsThisWeek: recent.reduce((sum, day) => sum + sanitizeNumber(day.reviews, 0), 0)
    };
  }, [safeData.weeklyProgress]);

  const { weeklyProgress, monthlyTrends, categoryDistribution, performanceMetrics } = safeData;

  // 주간 목표 진행률 (나누기 0 방지)
  const weeklyProgressPercent = sanitizeNumber(
    performanceMetrics.weeklyGoal > 0 
      ? Math.min((sanitizeNumber(performanceMetrics.weeklyProgress) / sanitizeNumber(performanceMetrics.weeklyGoal)) * 100, 100)
      : 0
  );

  // 실제 데이터가 있는지 확인 (빈 배열도 처리)
  const hasWeeklyData = safeData.weeklyProgress && safeData.weeklyProgress.length > 0;
  const hasMonthlyData = safeData.monthlyTrends && safeData.monthlyTrends.length > 0;
  const hasCategoryData = safeData.categoryDistribution && safeData.categoryDistribution.length > 0;
  
  // 데이터가 전혀 없는 경우 안내 메시지 표시
  if (!hasWeeklyData && !hasMonthlyData && !hasCategoryData) {
    return (
      <div className="text-center py-16 text-gray-500">
        <div className="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-6">
          <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          분석할 데이터가 부족합니다
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          콘텐츠를 추가하고 복습을 진행하면 상세한 학습 분석을 확인할 수 있습니다.
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
    );
  }

  // 배열 안전 체크
  const safeArray = (arr: any[], fallback: any[] = []): any[] => {
    return Array.isArray(arr) ? arr : fallback;
  };

  const formatTooltipValue = (value: number, name: string) => {
    const safeValue = sanitizeNumber(value);
    // 추가 NaN 체크
    if (isNaN(safeValue) || !isFinite(safeValue)) {
      return ['0', name];
    }
    if (name.includes('Rate') || name.includes('율')) {
      return [`${safeValue.toFixed(1)}%`, name];
    }
    if (name.includes('Time') || name.includes('시간')) {
      return [`${safeValue}분`, name];
    }
    return [Math.round(safeValue), name];
  };

  return (
    <div className="space-y-6">
      {/* 핵심 성과 지표 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 현재 스트릭 */}
        <div className="card card-raised card-body">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">연속 학습</p>
              <p className="heading-4">
                {sanitizeNumber(performanceMetrics.currentStreak)}일
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center">
              <FireIcon className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              최고 기록: {sanitizeNumber(performanceMetrics.longestStreak)}일
            </div>
          </div>
        </div>

        {/* 주간 진행률 */}
        <div className="card card-raised card-body">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">주간 목표</p>
              <p className="heading-4">
                {sanitizeNumber(weeklyProgressPercent).toFixed(0)}%
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
              {sanitizeNumber(performanceMetrics.weeklyProgress)}/{sanitizeNumber(performanceMetrics.weeklyGoal)} 복습 완료
            </div>
          </div>
        </div>

        {/* 성공률 트렌드 */}
        <div className="card card-raised card-body">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">평균 정답률</p>
              <p className="heading-4">
                {sanitizeNumber(performanceInsights.recentSuccess).toFixed(1)}%
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
                  {performanceInsights.trend === 'up' ? '↗' : '↘'} {sanitizeNumber(performanceInsights.trendPercent).toFixed(1)}% 
                  {performanceInsights.trend === 'up' ? '향상' : '감소'}
                </>
              )}
              {performanceInsights.trend === 'stable' && '안정적 유지'}
            </div>
          </div>
        </div>

        {/* 총 복습 횟수 */}
        <div className="card card-raised card-body">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 복습</p>
              <p className="heading-4">
                {sanitizeNumber(performanceMetrics.totalReviews).toLocaleString()}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
              <AcademicCapIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-xs text-gray-500 dark:text-gray-400">
              이번 주: {sanitizeNumber(performanceInsights.totalReviewsThisWeek)}회
            </div>
          </div>
        </div>
      </div>

      {/* 주간 학습 진도 차트 */}
      <div className="card card-raised card-body">
        <h3 className="heading-5">
          📈 주간 학습 진도
        </h3>
        <div className="h-80">
          {safeArray(weeklyProgress).length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={(() => {
                const rawData = safeArray(weeklyProgress);
                if (rawData.length === 0) {
                  return Array.from({length: 7}, (_, i) => ({
                    date: `Day ${i + 1}`, 
                    reviews: 0, 
                    successRate: 0, 
                    newContent: 0, 
                    masteredItems: 0
                  }));
                }
                return rawData.map((item, index) => ({
                  date: item?.date || `Day ${index + 1}`,
                  reviews: Math.max(0, sanitizeNumber(item?.reviews, 0)),
                  successRate: Math.max(0, Math.min(100, sanitizeNumber(item?.successRate, 0))),
                  newContent: Math.max(0, sanitizeNumber(item?.newContent, 0)),
                  masteredItems: Math.max(0, sanitizeNumber(item?.masteredItems, 0))
                }));
              })()}>
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
                domain={[0, (dataMax: number) => {
                  const safeMax = sanitizeNumber(dataMax, 10);
                  return Math.max(10, safeMax + 10);
                }]}
                allowDataOverflow={false}
                allowDecimals={false}
                type="number"
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                tick={{ fontSize: 12 }}
                stroke="#9ca3af"
                domain={[0, 100]}
                allowDataOverflow={false}
                allowDecimals={false}
                type="number"
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
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              데이터가 없습니다
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 월간 학습 패턴 */}
        <div className="card card-raised card-body">
          <h3 className="heading-5">
            📊 월간 학습 패턴
          </h3>
          <div className="h-64">
            {safeArray(monthlyTrends).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={(() => {
                const rawData = safeArray(monthlyTrends);
                if (rawData.length === 0) {
                  return Array.from({length: 4}, (_, i) => ({
                    month: `Month ${i + 1}`, 
                    totalReviews: Math.floor(Math.random() * 10), 
                    averageScore: Math.floor(Math.random() * 50) + 50, 
                    contentAdded: Math.floor(Math.random() * 5), 
                    timeSpent: Math.floor(Math.random() * 30) + 10
                  }));
                }
                return rawData.map((item, index) => ({
                  month: item?.month || `Month ${index + 1}`,
                  totalReviews: Math.max(0, sanitizeNumber(item?.totalReviews, 1)),
                  averageScore: Math.max(0, Math.min(100, sanitizeNumber(item?.averageScore, 50))),
                  contentAdded: Math.max(0, sanitizeNumber(item?.contentAdded, 1)),
                  timeSpent: Math.max(0, sanitizeNumber(item?.timeSpent, 10))
                }));
              })()}>              
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  domain={[0, (dataMax: number) => {
                    const safeMax = sanitizeNumber(dataMax, 5);
                    return Math.max(5, safeMax + 5);
                  }]}
                  allowDataOverflow={false}
                  allowDecimals={false}
                  type="number"
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
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                데이터가 없습니다
              </div>
            )}
          </div>
        </div>

        {/* 카테고리별 분포 */}
        <div className="card card-raised card-body">
          <h3 className="heading-5">
            🎯 카테고리별 학습 분포
          </h3>
          <div className="h-64">
            {safeArray(categoryDistribution).filter(item => (item.value || 0) > 0).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={(() => {
                      const rawData = safeArray(categoryDistribution);
                      return rawData
                        .map(item => ({
                          name: item?.name || 'Unknown',
                          value: Math.max(1, sanitizeNumber(item?.value, 1)), // 최소값 1로 설정
                          color: item?.color || '#3b82f6',
                          masteryLevel: Math.max(0, Math.min(100, sanitizeNumber(item?.masteryLevel, 0)))
                        }))
                        .filter(item => item.value > 0 && item.name !== 'Unknown');
                    })()}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {safeArray(categoryDistribution).filter(item => (item.value || 0) > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color || '#3b82f6'} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => [sanitizeNumber(value), '콘텐츠 수']}
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
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <p className="text-sm">아직 학습 데이터가 없습니다</p>
                  <p className="text-xs mt-1">콘텐츠를 추가하고 복습을 시작해보세요</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 학습 효율성 레이더 차트 */}
      <div className="card card-raised card-body">
        <h3 className="heading-5">
          ⚡ 학습 효율성 분석
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* 원형 진행률 표시기들 */}
          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <div className="w-24 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart data={[{ 
                    name: 'Retention', 
                    value: Math.max(0, Math.min(100, sanitizeNumber(performanceMetrics.averageRetention, 0))), 
                    fill: COLORS.success 
                  }]}>
                    <RadialBar dataKey="value" cornerRadius={10} fill={COLORS.success} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {sanitizeNumber(performanceMetrics.averageRetention)}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">평균 기억 유지율</p>
          </div>

          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <div className="w-24 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart data={[{ 
                    name: 'Efficiency', 
                    value: Math.max(0, Math.min(100, sanitizeNumber(performanceMetrics.studyEfficiency, 0))), 
                    fill: COLORS.purple 
                  }]}>
                    <RadialBar dataKey="value" cornerRadius={10} fill={COLORS.purple} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {sanitizeNumber(performanceMetrics.studyEfficiency)}%
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">학습 효율성</p>
          </div>

          <div className="text-center">
            <div className="relative w-24 h-24 mx-auto mb-3">
              <div className="w-24 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart data={[{ 
                    name: 'Goal', 
                    value: Math.max(0, Math.min(100, sanitizeNumber(weeklyProgressPercent, 0))), 
                    fill: COLORS.indigo 
                  }]}>
                    <RadialBar dataKey="value" cornerRadius={10} fill={COLORS.indigo} />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  {sanitizeNumber(weeklyProgressPercent).toFixed(0)}%
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