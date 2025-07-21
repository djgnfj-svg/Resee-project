import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  TreeMap
} from 'recharts';
import { 
  BookOpenIcon,
  TrophyIcon,
  ClockIcon,
  FireIcon,
  ChartBarIcon,
  AcademicCapIcon,
  LightBulbIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

interface AdvancedCategoryAnalysisProps {
  data: {
    categories: Array<{
      id: number;
      name: string;
      totalContent: number;
      masteredContent: number;
      inProgressContent: number;
      averageSuccessRate: number;
      averageDifficulty: number;
      totalReviews: number;
      averageReviewTime: number; // 분 단위
      masteryProgress: number; // 0-100%
      retentionRate: number;
      lastActivity: string;
      learningVelocity: number; // 일주일당 숙달한 콘텐츠 수
      categoryRank: number; // 1-N 순위
    }>;
    performanceMatrix: Array<{
      category: string;
      difficulty: number; // 1-5
      performance: number; // 0-100%
      reviewFrequency: number; // 일주일당 복습 횟수
      timeInvestment: number; // 총 시간 (분)
      masteryLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    }>;
    improvementSuggestions: Array<{
      categoryId: number;
      categoryName: string;
      issue: string;
      suggestion: string;
      priority: 'high' | 'medium' | 'low';
      expectedImprovement: number; // 예상 성과 향상 %
    }>;
    competencyMap: Array<{
      skill: string;
      currentLevel: number; // 1-100
      targetLevel: number;
      categories: string[];
      progress: number; // 0-100%
    }>;
  };
}

const DIFFICULTY_COLORS = {
  1: '#10b981', // 쉬움
  2: '#84cc16', // 약간 쉬움
  3: '#f59e0b', // 보통
  4: '#f97316', // 어려움
  5: '#ef4444'  // 매우 어려움
};

const MASTERY_COLORS = {
  beginner: '#ef4444',
  intermediate: '#f59e0b',
  advanced: '#3b82f6',
  expert: '#10b981'
};

const PRIORITY_COLORS = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#10b981'
};

const AdvancedCategoryAnalysis: React.FC<AdvancedCategoryAnalysisProps> = ({ data }) => {
  const { categories, performanceMatrix, improvementSuggestions, competencyMap } = data;

  // 카테고리별 종합 점수 계산
  const categoryScores = useMemo(() => {
    return categories.map(category => {
      const efficiencyScore = (category.averageSuccessRate / 100) * 100;
      const progressScore = category.masteryProgress;
      const velocityScore = Math.min(100, category.learningVelocity * 10);
      const retentionScore = category.retentionRate;
      
      const overallScore = (efficiencyScore * 0.3 + progressScore * 0.3 + velocityScore * 0.2 + retentionScore * 0.2);
      
      return {
        ...category,
        overallScore: Math.round(overallScore),
        efficiencyScore: Math.round(efficiencyScore),
        progressScore: Math.round(progressScore),
        velocityScore: Math.round(velocityScore),
        retentionScore: Math.round(retentionScore)
      };
    });
  }, [categories]);

  // 최고/최저 성과 카테고리
  const topCategory = categoryScores.reduce((best, current) => 
    current.overallScore > best.overallScore ? current : best
  );
  const bottomCategory = categoryScores.reduce((worst, current) => 
    current.overallScore < worst.overallScore ? current : worst
  );

  // 학습 효율성 매트릭스 데이터 준비
  const efficiencyMatrix = performanceMatrix.map(item => ({
    ...item,
    efficiency: (item.performance / item.timeInvestment) * 100
  }));

  // 트리맵을 위한 데이터 변환
  const treemapData = categories.map(category => ({
    name: category.name,
    size: category.totalContent,
    value: category.masteryProgress,
    color: category.masteryProgress >= 80 ? '#10b981' : 
           category.masteryProgress >= 60 ? '#f59e0b' : '#ef4444'
  }));

  const formatTooltip = (value: number, name: string) => {
    if (name.includes('Rate') || name.includes('율') || name.includes('Score') || name.includes('점수')) {
      return [`${value}%`, name];
    }
    if (name.includes('Time') || name.includes('시간')) {
      return [`${value}분`, name];
    }
    return [value, name];
  };

  return (
    <div className="space-y-6">
      {/* 카테고리 성과 개요 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">최고 성과</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
                {topCategory.name}
              </p>
            </div>
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
              <TrophyIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-green-600 dark:text-green-400">
            종합 점수: {topCategory.overallScore}%
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">개선 필요</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
                {bottomCategory.name}
              </p>
            </div>
            <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
              <LightBulbIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-red-600 dark:text-red-400">
            종합 점수: {bottomCategory.overallScore}%
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 카테고리</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {categories.length}
              </p>
            </div>
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <BookOpenIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            활성 학습 영역
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">평균 숙달도</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {Math.round(categories.reduce((sum, cat) => sum + cat.masteryProgress, 0) / categories.length)}%
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
              <AcademicCapIcon className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            전체 진도율
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 카테고리별 종합 성과 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            📊 카테고리별 종합 성과
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryScores} layout="horizontal" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fontSize: 11 }}
                  width={80}
                />
                <Tooltip formatter={formatTooltip} />
                <Bar 
                  dataKey="overallScore" 
                  fill="#3b82f6"
                  name="종합 점수"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 학습 효율성 매트릭스 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            ⚡ 난이도 vs 성과 매트릭스
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={performanceMatrix}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  type="number" 
                  dataKey="difficulty" 
                  domain={[0, 6]}
                  tick={{ fontSize: 11 }}
                  name="난이도"
                  label={{ value: '난이도', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  type="number" 
                  dataKey="performance" 
                  domain={[0, 100]}
                  tick={{ fontSize: 11 }}
                  name="성과"
                  label={{ value: '성과 (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  formatter={(value, name) => [
                    name === 'performance' ? `${value}%` : value,
                    name === 'performance' ? '성과' : name === 'difficulty' ? '난이도' : name
                  ]}
                  labelFormatter={(label) => `카테고리: ${label}`}
                />
                <Scatter 
                  dataKey="performance" 
                  fill="#8884d8"
                  name="성과"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 카테고리 콘텐츠 분포 트리맵 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          🌳 카테고리별 콘텐츠 분포 & 숙달도
        </h3>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <TreeMap
              data={treemapData}
              dataKey="size"
              aspectRatio={4/3}
              stroke="#e5e7eb"
              fill="#8884d8"
            />
          </ResponsiveContainer>
        </div>
        <div className="flex items-center justify-between mt-4 text-xs text-gray-500 dark:text-gray-400">
          <span>크기: 콘텐츠 수 | 색상: 숙달도</span>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span>&lt; 60%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span>60-80%</span>
            </div>
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span>&gt; 80%</span>
            </div>
          </div>
        </div>
      </div>

      {/* 역량 발달 현황 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          🎯 핵심 역량 발달 현황
        </h3>
        <div className="space-y-4">
          {competencyMap.map((skill, index) => (
            <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900 dark:text-gray-100">{skill.skill}</h4>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {skill.progress}% 달성
                </span>
              </div>
              <div className="bg-gray-200 dark:bg-gray-600 rounded-full h-2 mb-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${skill.progress}%` }}
                />
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500 dark:text-gray-400">
                  현재: {skill.currentLevel} | 목표: {skill.targetLevel}
                </span>
                <span className="text-blue-600 dark:text-blue-400">
                  관련: {skill.categories.join(', ')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 개선 제안 */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl p-6 border border-amber-200 dark:border-amber-800">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-amber-600 rounded-full flex items-center justify-center">
              <SparklesIcon className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-medium text-amber-900 dark:text-amber-100 mb-4">
              🚀 스마트 개선 제안
            </h4>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {improvementSuggestions
                .sort((a, b) => {
                  const priorityOrder = { high: 3, medium: 2, low: 1 };
                  return priorityOrder[b.priority] - priorityOrder[a.priority];
                })
                .slice(0, 4)
                .map((suggestion, index) => (
                  <div key={index} className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
                    <div className="flex items-start justify-between mb-2">
                      <h5 className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                        {suggestion.categoryName}
                      </h5>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        suggestion.priority === 'high' 
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          : suggestion.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                          : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      }`}>
                        {suggestion.priority}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      <strong>문제:</strong> {suggestion.issue}
                    </p>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                      <strong>제안:</strong> {suggestion.suggestion}
                    </p>
                    <div className="text-xs text-blue-600 dark:text-blue-400">
                      예상 개선: +{suggestion.expectedImprovement}%
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedCategoryAnalysis;