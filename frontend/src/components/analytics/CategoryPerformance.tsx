import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface CategoryData {
  id: number;
  name: string;
  slug: string;
  content_count: number;
  total_reviews: number;
  success_rate: number;
  recent_success_rate: number;
  difficulty_level: number;
  mastery_level: string;
}

interface CategoryPerformanceProps {
  categories: CategoryData[];
}

const CategoryPerformance: React.FC<CategoryPerformanceProps> = ({ categories }) => {
  // 마스터리 레벨별 색상
  const masteryColors = {
    expert: '#10b981', // green-500
    advanced: '#3b82f6', // blue-500
    intermediate: '#f59e0b', // amber-500
    beginner: '#ef4444', // red-500
    novice: '#6b7280', // gray-500
  };

  // 마스터리 레벨별 라벨
  const masteryLabels = {
    expert: '전문가',
    advanced: '고급',
    intermediate: '중급',
    beginner: '초급',
    novice: '입문',
  };

  // 차트 데이터 준비
  const chartData = categories.map(cat => ({
    name: cat.name.length > 8 ? cat.name.substring(0, 8) + '...' : cat.name,
    fullName: cat.name,
    success_rate: cat.success_rate,
    recent_success_rate: cat.recent_success_rate,
    total_reviews: cat.total_reviews,
    mastery_level: cat.mastery_level,
  }));

  // 마스터리 레벨 분포 데이터
  const masteryDistribution = Object.entries(
    categories.reduce((acc, cat) => {
      acc[cat.mastery_level] = (acc[cat.mastery_level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([level, count]) => ({
    name: masteryLabels[level as keyof typeof masteryLabels],
    value: count,
    color: masteryColors[level as keyof typeof masteryColors],
  }));

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-medium text-gray-900 dark:text-gray-100">{data.fullName}</p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            전체 성공률: <span className="font-medium text-blue-600 dark:text-blue-400">{data.success_rate}%</span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            최근 성공률: <span className="font-medium text-green-600 dark:text-green-400">{data.recent_success_rate}%</span>
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            총 복습 횟수: <span className="font-medium">{data.total_reviews}회</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          카테고리별 성과
        </h2>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          성공률 비교
        </div>
      </div>

      {categories.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 dark:text-gray-400">
            아직 카테고리별 데이터가 없습니다.
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* 성공률 비교 차트 */}
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis 
                  dataKey="name" 
                  className="text-xs text-gray-600 dark:text-gray-400"
                />
                <YAxis 
                  className="text-xs text-gray-600 dark:text-gray-400"
                  domain={[0, 100]}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar 
                  dataKey="success_rate" 
                  fill="#3b82f6" 
                  name="전체 성공률"
                  radius={[4, 4, 0, 0]}
                />
                <Bar 
                  dataKey="recent_success_rate" 
                  fill="#10b981" 
                  name="최근 성공률"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 마스터리 레벨 분포 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-4">
                마스터리 레벨 분포
              </h3>
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={masteryDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {masteryDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value, name) => [`${value}개`, name]}
                      contentStyle={{
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        border: '1px solid #e5e7eb',
                        borderRadius: '0.5rem',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div>
              <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-4">
                상위 성과 카테고리
              </h3>
              <div className="space-y-3">
                {categories
                  .sort((a, b) => b.success_rate - a.success_rate)
                  .slice(0, 5)
                  .map((category, index) => (
                    <div key={category.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900 dark:text-gray-100">
                            {category.name}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">
                            {category.total_reviews}회 복습 · {masteryLabels[category.mastery_level as keyof typeof masteryLabels]}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                          {category.success_rate.toFixed(1)}%
                        </div>
                        <div className={`text-xs ${
                          category.recent_success_rate > category.success_rate 
                            ? 'text-green-600 dark:text-green-400' 
                            : category.recent_success_rate < category.success_rate
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          최근: {category.recent_success_rate.toFixed(1)}%
                          {category.recent_success_rate > category.success_rate ? ' ↗' :
                           category.recent_success_rate < category.success_rate ? ' ↘' : ' →'}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>

          {/* 개선 필요 카테고리 */}
          {categories.some(cat => cat.success_rate < 70) && (
            <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
              <h3 className="text-sm font-medium text-amber-900 dark:text-amber-200 mb-2">
                💡 집중 학습 추천
              </h3>
              <div className="text-sm text-amber-700 dark:text-amber-300">
                {categories
                  .filter(cat => cat.success_rate < 70)
                  .sort((a, b) => a.success_rate - b.success_rate)
                  .slice(0, 3)
                  .map(cat => cat.name)
                  .join(', ')} 카테고리의 복습을 늘려보세요.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CategoryPerformance;