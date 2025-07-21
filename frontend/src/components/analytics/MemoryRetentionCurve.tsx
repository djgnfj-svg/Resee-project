import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart
} from 'recharts';
import { 
  LightBulbIcon, 
  ClockIcon,
  ArrowTrendingUpIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface MemoryRetentionProps {
  data: {
    retentionCurve: Array<{
      interval: number; // 복습 간격 (일)
      retentionRate: number; // 기억 유지율 (%)
      reviewCount: number; // 해당 간격의 총 복습 횟수
      optimalRate: number; // 이론적 최적 유지율
    }>;
    forgettingCurve: Array<{
      timeElapsed: number; // 경과 시간 (시간)
      memoryStrength: number; // 기억 강도 (%)
      withoutReview: number; // 복습 없을 때 기억 강도
      withReview: number; // 복습 있을 때 기억 강도
    }>;
    insights: {
      averageRetention: number;
      optimalRetention: number;
      improvementPotential: number;
      strongestInterval: number;
      weakestInterval: number;
      nextOptimalReview: number; // 시간 단위
    };
  };
}

const MemoryRetentionCurve: React.FC<MemoryRetentionProps> = ({ data }) => {
  const { retentionCurve, forgettingCurve, insights } = data;

  // 성과 지표 계산
  const performanceIndicators = useMemo(() => {
    const totalReviews = retentionCurve.reduce((sum, item) => sum + item.reviewCount, 0);
    const weightedRetention = retentionCurve.reduce((sum, item) => 
      sum + (item.retentionRate * item.reviewCount), 0) / totalReviews;

    const efficiency = (weightedRetention / insights.optimalRetention) * 100;
    const consistencyScore = 100 - (Math.max(...retentionCurve.map(r => r.retentionRate)) - 
                                  Math.min(...retentionCurve.map(r => r.retentionRate)));

    return {
      efficiency: Math.round(efficiency),
      consistency: Math.round(consistencyScore),
      totalReviews,
      weightedRetention: Math.round(weightedRetention)
    };
  }, [retentionCurve, insights]);

  const formatTooltip = (value: number, name: string) => {
    if (name.includes('Rate') || name.includes('율') || name.includes('Strength') || name.includes('강도')) {
      return [`${value.toFixed(1)}%`, name];
    }
    if (name.includes('Time') || name.includes('시간')) {
      return [`${value}시간`, name];
    }
    if (name.includes('Interval') || name.includes('간격')) {
      return [`${value}일`, name];
    }
    return [value, name];
  };

  return (
    <div className="space-y-6">
      {/* 핵심 지표 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">평균 기억률</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {performanceIndicators.weightedRetention}%
              </p>
            </div>
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <LightBulbIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            목표: {insights.optimalRetention}%
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">학습 효율성</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {performanceIndicators.efficiency}%
              </p>
            </div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              performanceIndicators.efficiency >= 90 
                ? 'bg-green-100 dark:bg-green-900/30' 
                : performanceIndicators.efficiency >= 75
                ? 'bg-yellow-100 dark:bg-yellow-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            }`}>
              <ArrowTrendingUpIcon className={`w-5 h-5 ${
                performanceIndicators.efficiency >= 90 
                  ? 'text-green-600 dark:text-green-400' 
                  : performanceIndicators.efficiency >= 75
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-red-600 dark:text-red-400'
              }`} />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            이론 대비 효율성
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">일관성</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {performanceIndicators.consistency}%
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
              <ClockIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            복습 간격별 균일성
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">개선 가능성</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                +{insights.improvementPotential}%
              </p>
            </div>
            <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center">
              <InformationCircleIcon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            최적화 잠재력
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 복습 간격별 기억 유지율 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            🧠 복습 간격별 기억 유지율
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={retentionCurve}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="interval" 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  label={{ value: '복습 간격 (일)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  label={{ value: '기억 유지율 (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={formatTooltip}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="retentionRate"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  name="실제 유지율"
                />
                <Line
                  type="monotone"
                  dataKey="optimalRate"
                  stroke="#10b981"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="이론적 최적율"
                />
                <ReferenceLine 
                  y={80} 
                  stroke="#f59e0b" 
                  strokeDasharray="3 3"
                  label={{ value: "목표선 (80%)", position: "topLeft" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 에빙하우스 망각 곡선 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            ⏰ 에빙하우스 망각 곡선
          </h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forgettingCurve}>
                <defs>
                  <linearGradient id="withReview" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="withoutReview" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="timeElapsed" 
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  label={{ value: '경과 시간 (시간)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  stroke="#9ca3af"
                  label={{ value: '기억 강도 (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={formatTooltip}
                  contentStyle={{
                    backgroundColor: '#ffffff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="withoutReview"
                  stackId="1"
                  stroke="#ef4444"
                  fill="url(#withoutReview)"
                  name="복습 없음"
                />
                <Area
                  type="monotone"
                  dataKey="withReview"
                  stroke="#10b981"
                  strokeWidth={3}
                  fill="none"
                  name="복습 포함"
                />
                <ReferenceLine 
                  x={insights.nextOptimalReview} 
                  stroke="#8b5cf6" 
                  strokeDasharray="3 3"
                  label={{ value: "최적 복습 시점", position: "top" }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 인사이트 및 권장사항 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <LightBulbIcon className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-lg font-medium text-blue-900 dark:text-blue-100 mb-3">
              🎯 개인화된 학습 최적화 제안
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="font-medium text-blue-800 dark:text-blue-200 mb-2">강점</h5>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                  <li>• {insights.strongestInterval}일 간격에서 최고 성과 ({retentionCurve.find(r => r.interval === insights.strongestInterval)?.retentionRate.toFixed(1)}%)</li>
                  <li>• 평균 기억 유지율이 목표치 대비 양호</li>
                  <li>• 일관된 복습 패턴 유지</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-blue-800 dark:text-blue-200 mb-2">개선 영역</h5>
                <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                  <li>• {insights.weakestInterval}일 간격 복습 강화 필요</li>
                  <li>• 복습 타이밍을 {insights.nextOptimalReview}시간으로 최적화</li>
                  <li>• {insights.improvementPotential}% 추가 성과 향상 가능</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemoryRetentionCurve;