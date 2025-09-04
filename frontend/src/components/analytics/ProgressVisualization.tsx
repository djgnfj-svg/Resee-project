import React from 'react';
import WeeklyProgressChart from './charts/WeeklyProgressChart';
import MonthlyTrendsChart from './charts/MonthlyTrendsChart';
import CategoryPieChart from './charts/CategoryPieChart';
import PerformanceMetrics from './charts/PerformanceMetrics';

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
  onGoalUpdate?: (newGoal: number) => Promise<void>;
}

const ProgressVisualization: React.FC<ProgressVisualizationProps> = ({ 
  data, 
  onGoalUpdate 
}) => {
  if (!data || typeof data !== 'object') {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <div className="text-4xl mb-4">📊</div>
        <p>데이터를 로딩 중입니다...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 성능 지표 */}
      <PerformanceMetrics 
        data={data.performanceMetrics} 
        onGoalUpdate={onGoalUpdate}
      />

      {/* 차트 영역 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WeeklyProgressChart data={data.weeklyProgress} />
        <CategoryPieChart data={data.categoryDistribution} />
      </div>

      {/* 월간 동향 차트 */}
      <MonthlyTrendsChart data={data.monthlyTrends} />
    </div>
  );
};

export default ProgressVisualization;