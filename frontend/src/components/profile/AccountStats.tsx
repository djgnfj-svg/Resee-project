import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../../utils/api';

const AccountStats: React.FC = () => {
  // Fetch dashboard statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
  });

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">계정 통계</h3>
      {statsLoading ? (
        <div className="flex items-center justify-center h-24">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {stats?.total_content || 0}
            </div>
            <div className="text-sm text-gray-600">총 콘텐츠</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {stats?.total_reviews_30_days || 0}
            </div>
            <div className="text-sm text-gray-600">총 복습 (30일)</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {stats?.success_rate ? `${Math.round(stats.success_rate)}%` : '0%'}
            </div>
            <div className="text-sm text-gray-600">성공률</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {stats?.streak_days || 0}
            </div>
            <div className="text-sm text-gray-600">연속 일수</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountStats;