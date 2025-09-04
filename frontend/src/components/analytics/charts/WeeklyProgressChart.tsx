import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { sanitizeChartData, formatPercentage } from '../../../utils/chart-helpers';

interface WeeklyProgressData {
  date: string;
  reviews: number;
  successRate: number;
  newContent: number;
  masteredItems: number;
}

interface WeeklyProgressChartProps {
  data: WeeklyProgressData[];
  height?: number;
}

const WeeklyProgressChart: React.FC<WeeklyProgressChartProps> = ({ 
  data, 
  height = 300 
}) => {
  const sanitizedData = sanitizeChartData(data);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        📈 주간 학습 진행도
      </h3>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <AreaChart data={sanitizedData}>
            <defs>
              <linearGradient id="reviewsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
              </linearGradient>
              <linearGradient id="successGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#10B981" stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis 
              dataKey="date" 
              stroke="#6B7280"
              tick={{ fill: '#6B7280', fontSize: 12 }}
            />
            <YAxis 
              stroke="#6B7280"
              tick={{ fill: '#6B7280', fontSize: 12 }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1F2937',
                border: '1px solid #374151',
                borderRadius: '8px',
                color: '#F9FAFB'
              }}
              formatter={(value: number, name: string) => {
                if (name === 'successRate') {
                  return [formatPercentage(value), '성공률'];
                }
                return [value, name === 'reviews' ? '복습 횟수' : '마스터한 항목'];
              }}
              labelStyle={{ color: '#F9FAFB' }}
            />
            <Area 
              type="monotone" 
              dataKey="reviews" 
              stroke="#3B82F6" 
              fillOpacity={1}
              fill="url(#reviewsGradient)" 
            />
            <Area 
              type="monotone" 
              dataKey="masteredItems" 
              stroke="#10B981" 
              fillOpacity={1}
              fill="url(#successGradient)" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center space-x-6 mt-4 text-sm">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
          <span className="text-gray-600 dark:text-gray-400">복습 횟수</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
          <span className="text-gray-600 dark:text-gray-400">마스터한 항목</span>
        </div>
      </div>
    </div>
  );
};

export default WeeklyProgressChart;