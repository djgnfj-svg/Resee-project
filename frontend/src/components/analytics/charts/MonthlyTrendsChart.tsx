import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { sanitizeChartData, formatNumber } from '../../../utils/chart-helpers';

interface MonthlyTrendsData {
  month: string;
  totalReviews: number;
  averageScore: number;
  contentAdded: number;
  timeSpent: number;
}

interface MonthlyTrendsChartProps {
  data: MonthlyTrendsData[];
  height?: number;
}

const MonthlyTrendsChart: React.FC<MonthlyTrendsChartProps> = ({ 
  data, 
  height = 400 
}) => {
  const sanitizedData = sanitizeChartData(data);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        📊 월간 학습 동향
      </h3>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <BarChart data={sanitizedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
            <XAxis 
              dataKey="month" 
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
                const labels: Record<string, string> = {
                  totalReviews: '총 복습',
                  averageScore: '평균 점수',
                  contentAdded: '추가된 콘텐츠',
                  timeSpent: '학습 시간 (분)'
                };
                return [formatNumber(value), labels[name] || name];
              }}
              labelStyle={{ color: '#F9FAFB' }}
            />
            <Legend />
            <Bar 
              dataKey="totalReviews" 
              fill="#3B82F6" 
              name="총 복습"
              radius={[2, 2, 0, 0]}
            />
            <Bar 
              dataKey="contentAdded" 
              fill="#8B5CF6" 
              name="추가된 콘텐츠"
              radius={[2, 2, 0, 0]}
            />
            <Bar 
              dataKey="timeSpent" 
              fill="#10B981" 
              name="학습 시간"
              radius={[2, 2, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MonthlyTrendsChart;