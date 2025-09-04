import React from 'react';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon, 
  MinusIcon,
  FireIcon,
  AcademicCapIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { sanitizeNumber, getTrendIcon, formatPercentage } from '../../../utils/chart-helpers';
import WeeklyGoalEditor from '../../WeeklyGoalEditor';

interface PerformanceMetricsData {
  currentStreak: number;
  longestStreak: number;
  totalReviews: number;
  averageRetention: number;
  studyEfficiency: number;
  weeklyGoal: number;
  weeklyProgress: number;
}

interface PerformanceMetricsProps {
  data: PerformanceMetricsData;
  onGoalUpdate?: (newGoal: number) => Promise<void>;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ 
  data, 
  onGoalUpdate 
}) => {
  const sanitizedData = {
    currentStreak: sanitizeNumber(data.currentStreak, 0),
    longestStreak: sanitizeNumber(data.longestStreak, 0),
    totalReviews: sanitizeNumber(data.totalReviews, 0),
    averageRetention: sanitizeNumber(data.averageRetention, 0),
    studyEfficiency: sanitizeNumber(data.studyEfficiency, 0),
    weeklyGoal: sanitizeNumber(data.weeklyGoal, 0),
    weeklyProgress: sanitizeNumber(data.weeklyProgress, 0),
  };

  const weeklyProgressPercent = sanitizedData.weeklyGoal > 0 
    ? Math.min((sanitizedData.weeklyProgress / sanitizedData.weeklyGoal) * 100, 100)
    : 0;

  const streakTrend = getTrendIcon(sanitizedData.currentStreak, sanitizedData.longestStreak);
  const retentionTrend = getTrendIcon(sanitizedData.averageRetention, 75); // 75% 기준
  const efficiencyTrend = getTrendIcon(sanitizedData.studyEfficiency, 80); // 80% 기준

  const TrendIcon = ({ trend }: { trend: string }) => {
    switch (trend) {
      case 'up':
        return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <MinusIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* 연속 학습 일수 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <FireIcon className="h-8 w-8 text-orange-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">연속 학습</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {sanitizedData.currentStreak}일
              </p>
            </div>
          </div>
          <TrendIcon trend={streakTrend} />
        </div>
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          최고 기록: {sanitizedData.longestStreak}일
        </div>
      </div>

      {/* 총 복습 횟수 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <AcademicCapIcon className="h-8 w-8 text-blue-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">총 복습</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {sanitizedData.totalReviews.toLocaleString()}회
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 평균 기억률 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">평균 기억률</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {formatPercentage(sanitizedData.averageRetention)}
              </p>
            </div>
          </div>
          <TrendIcon trend={retentionTrend} />
        </div>
      </div>

      {/* 학습 효율성 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="h-8 w-8 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mr-3">
              <span className="text-purple-600 dark:text-purple-400 font-bold text-sm">⚡</span>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">학습 효율성</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {formatPercentage(sanitizedData.studyEfficiency)}
              </p>
            </div>
          </div>
          <TrendIcon trend={efficiencyTrend} />
        </div>
      </div>

      {/* 주간 목표 진행도 */}
      <div className="md:col-span-2 bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">주간 목표 진행도</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {sanitizedData.weeklyProgress} / {sanitizedData.weeklyGoal} 복습 완료
            </p>
          </div>
          {onGoalUpdate && (
            <WeeklyGoalEditor 
              currentGoal={sanitizedData.weeklyGoal} 
              onSave={onGoalUpdate} 
            />
          )}
        </div>
        
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 mb-2">
          <div 
            className={`h-4 rounded-full transition-all duration-500 ${
              weeklyProgressPercent >= 100 
                ? 'bg-green-500' 
                : weeklyProgressPercent >= 75
                  ? 'bg-blue-500'
                  : weeklyProgressPercent >= 50
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(weeklyProgressPercent, 100)}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {formatPercentage(weeklyProgressPercent)} 달성
          </span>
          <span className="text-gray-600 dark:text-gray-400">
            {Math.max(0, sanitizedData.weeklyGoal - sanitizedData.weeklyProgress)} 남음
          </span>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMetrics;