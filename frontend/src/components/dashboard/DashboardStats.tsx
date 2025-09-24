import React from 'react';

interface Stat {
  name: string;
  value: number;
  unit: string;
  icon: string;
  color: string;
  bgColor: string;
}

interface DashboardStatsProps {
  todayReviews: number;
  totalContent: number;
  successRate: number;
}

const DashboardStats: React.FC<DashboardStatsProps> = ({
  todayReviews,
  totalContent,
  successRate
}) => {
  const stats: Stat[] = [
    {
      name: '오늘의 복습',
      value: todayReviews,
      unit: '개',
      icon: '🎯',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      name: '전체 콘텐츠',
      value: totalContent,
      unit: '개',
      icon: '📖',
      color: 'text-green-600',
      bgColor: 'bg-green-50 dark:bg-green-900/20',
    },
    {
      name: '복습 성공률',
      value: successRate,
      unit: '%',
      icon: '🎉',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50 dark:bg-purple-900/20',
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
      {stats.map((stat, index) => (
        <div
          key={`dashboard-stat-${index}`}
          className="relative overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 shadow-lg dark:shadow-gray-700/20 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
        >
          <div className="flex items-center justify-between">
            <div className="text-2xl mb-2">{stat.icon}</div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${stat.color}`}>
                {stat.value}{stat.unit}
              </div>
            </div>
          </div>
          <h3 className="text-gray-700 dark:text-gray-300 font-semibold text-lg">{stat.name}</h3>
          <div className="h-2 bg-gray-100 rounded-full mt-3 overflow-hidden">
            <div
              className={`h-full ${stat.bgColor} rounded-full transition-all duration-500`}
              style={{width: `${Math.min(stat.value, 100)}%`}}
            ></div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DashboardStats;