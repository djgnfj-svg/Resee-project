import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import { sanitizeChartData, generateCategoryColors } from '../../../utils/chart-helpers';

interface CategoryData {
  name: string;
  value: number;
  color: string;
  masteryLevel: number;
}

interface CategoryPieChartProps {
  data: CategoryData[];
  height?: number;
}

const CategoryPieChart: React.FC<CategoryPieChartProps> = ({ 
  data, 
  height = 300 
}) => {
  const sanitizedData = sanitizeChartData(data);
  const colors = generateCategoryColors(sanitizedData.length);

  // 데이터가 있는지 확인
  const hasData = sanitizedData.length > 0 && sanitizedData.some(item => item.value > 0);

  if (!hasData) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          🎯 카테고리별 분포
        </h3>
        <div className="flex items-center justify-center h-64 text-gray-500 dark:text-gray-400">
          <div className="text-center">
            <div className="text-4xl mb-2">📊</div>
            <p>카테고리 데이터가 없습니다</p>
          </div>
        </div>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-gray-900 dark:bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-white dark:text-gray-100 font-medium">{data.name}</p>
          <p className="text-blue-300">복습 횟수: {data.value}</p>
          <p className="text-green-300">숙련도: {(data.masteryLevel * 100).toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        🎯 카테고리별 분포
      </h3>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={sanitizedData}
              cx="50%"
              cy="50%"
              outerRadius={100}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
            >
              {sanitizedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.color || colors[index]} 
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-2">
        {sanitizedData.map((entry, index) => (
          <div key={entry.name} className="flex items-center text-sm">
            <div 
              className="w-3 h-3 rounded-full mr-2" 
              style={{ backgroundColor: entry.color || colors[index] }}
            ></div>
            <span className="text-gray-600 dark:text-gray-400 truncate">
              {entry.name} ({entry.value})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CategoryPieChart;