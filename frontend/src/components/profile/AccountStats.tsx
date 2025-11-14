import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { reviewAPI } from '../../utils/api';

const AccountStats: React.FC = () => {
  // Fetch dashboard statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: reviewAPI.getDashboard,
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">계정 통계</h3>
      {statsLoading ? (
        <div className="flex items-center justify-center h-24">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">
              {stats?.total_content || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">총 콘텐츠</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {stats?.total_reviews_30_days || 0}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">총 복습 (30일)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {stats?.success_rate ? `${Math.round(stats.success_rate)}%` : '0%'}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">성공률</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountStats;