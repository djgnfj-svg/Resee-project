import React from 'react';

interface StatData {
  name: string;
  value: number;
  unit: string;
  icon: string;
  color: string;
  bgColor: string;
}

interface StatsCardProps {
  stat: StatData;
  index: number;
}

const StatsCard: React.FC<StatsCardProps> = ({ stat, index }) => {
  return (
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
  );
};

export default StatsCard;