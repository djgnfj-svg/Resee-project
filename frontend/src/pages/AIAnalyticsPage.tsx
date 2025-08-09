import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  AcademicCapIcon,
  ClockIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  CalendarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon
} from '@heroicons/react/24/outline';
import apiClient from '../utils/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';

interface LearningAnalytics {
  id: number;
  period_type: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  period_start: string;
  period_end: string;
  total_study_minutes: number;
  average_daily_minutes: number;
  peak_study_hour: number;
  study_day_pattern: Record<string, number>;
  total_contents_studied: number;
  total_reviews_completed: number;
  average_accuracy: number;
  weak_categories: Array<{category: string, score: number}>;
  strong_categories: Array<{category: string, score: number}>;
  recommended_focus_areas: string[];
  personalized_tips: string[];
  predicted_improvement_areas: string[];
  efficiency_score: number;
  retention_rate: number;
  created_at: string;
}

const AIAnalyticsPage: React.FC = () => {
  const [selectedPeriod, setSelectedPeriod] = useState<'weekly' | 'monthly' | 'quarterly'>('monthly');

  // 학습 분석 데이터 조회
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['learning-analytics', selectedPeriod],
    queryFn: async (): Promise<LearningAnalytics | null> => {
      const response = await apiClient.post('/api/ai-review/analytics/', {
        period_type: selectedPeriod
      });
      return response.data;
    }
  });

  const formatHour = (hour: number) => {
    if (hour === 0) return '오전 12시';
    if (hour < 12) return `오전 ${hour}시`;
    if (hour === 12) return '오후 12시';
    return `오후 ${hour - 12}시`;
  };

  const getDayLabel = (day: string) => {
    const labels: Record<string, string> = {
      'mon': '월', 'tue': '화', 'wed': '수', 'thu': '목',
      'fri': '금', 'sat': '토', 'sun': '일'
    };
    return labels[day] || day;
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackgroundColor = (score: number) => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">분석 데이터 없음</h3>
          <p className="mt-1 text-sm text-gray-500">
            충분한 학습 데이터가 쌓이면 AI 분석을 제공합니다.
          </p>
        </div>
      </div>
    );
  }

  const maxDayMinutes = Math.max(...Object.values(analytics.study_day_pattern));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <ChartBarIcon className="h-8 w-8 text-indigo-600 mr-3" />
                AI 학습 분석
              </h1>
              <p className="mt-2 text-gray-600">
                AI가 분석한 당신의 학습 패턴과 개선 방안을 확인하세요
              </p>
            </div>
            <div className="flex space-x-2">
              {(['weekly', 'monthly', 'quarterly'] as const).map((period) => (
                <button
                  key={period}
                  onClick={() => setSelectedPeriod(period)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedPeriod === period
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                  }`}
                >
                  {period === 'weekly' ? '주간' : period === 'monthly' ? '월간' : '분기'}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 핵심 지표 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <ClockIcon className="h-6 w-6 text-indigo-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">총 학습시간</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Math.round(analytics.total_study_minutes / 60)}시간
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <AcademicCapIcon className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">평균 정답률</p>
                <p className={`text-2xl font-bold ${getScoreColor(analytics.average_accuracy)}`}>
                  {analytics.average_accuracy.toFixed(0)}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <TrophyIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">학습 효율성</p>
                <p className={`text-2xl font-bold ${getScoreColor(analytics.efficiency_score)}`}>
                  {analytics.efficiency_score.toFixed(0)}점
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <ArrowTrendingUpIcon className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">기억 유지율</p>
                <p className={`text-2xl font-bold ${getScoreColor(analytics.retention_rate)}`}>
                  {analytics.retention_rate.toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* 학습 패턴 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CalendarIcon className="h-5 w-5 text-gray-600 mr-2" />
              학습 패턴 분석
            </h3>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">요일별 학습시간</p>
              <div className="space-y-2">
                {Object.entries(analytics.study_day_pattern).map(([day, minutes]) => (
                  <div key={day} className="flex items-center">
                    <div className="w-8 text-sm text-gray-600">{getDayLabel(day)}</div>
                    <div className="flex-1 mx-3">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-indigo-600 h-2 rounded-full"
                          style={{ width: `${(minutes / maxDayMinutes) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                    <div className="w-12 text-sm text-gray-900 text-right">
                      {minutes}분
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">집중 시간대</span>
                <span className="font-medium text-gray-900">
                  {formatHour(analytics.peak_study_hour)}
                </span>
              </div>
              <div className="flex justify-between text-sm mt-2">
                <span className="text-gray-600">일 평균 학습</span>
                <span className="font-medium text-gray-900">
                  {analytics.average_daily_minutes}분
                </span>
              </div>
            </div>
          </div>

          {/* 강약점 분석 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">강약점 분석</h3>
            
            <div className="mb-6">
              <h4 className="text-sm font-medium text-green-700 mb-2 flex items-center">
                <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />
                잘하는 분야
              </h4>
              <div className="space-y-2">
                {analytics.strong_categories.slice(0, 3).map((category, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded">
                    <span className="text-sm text-green-800">{category.category}</span>
                    <span className="text-sm font-medium text-green-600">{category.score}%</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center">
                <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />
                보완이 필요한 분야
              </h4>
              <div className="space-y-2">
                {analytics.weak_categories.slice(0, 3).map((category, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-red-50 border border-red-200 rounded">
                    <span className="text-sm text-red-800">{category.category}</span>
                    <span className="text-sm font-medium text-red-600">{category.score}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* AI 추천 및 팁 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 추천 집중 분야 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2" />
              AI 추천 집중 분야
            </h3>
            <div className="space-y-3">
              {analytics.recommended_focus_areas.map((area, index) => (
                <div key={index} className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">{area}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 개인화된 학습 팁 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <LightBulbIcon className="h-5 w-5 text-indigo-500 mr-2" />
              개인화된 학습 팁
            </h3>
            <div className="space-y-3">
              {analytics.personalized_tips.map((tip, index) => (
                <div key={index} className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
                  <p className="text-sm text-indigo-800">{tip}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 예상 개선 분야 */}
        {analytics.predicted_improvement_areas.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <ChartBarIcon className="h-5 w-5 text-blue-500 mr-2" />
              예상 개선 가능 분야
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analytics.predicted_improvement_areas.map((area, index) => (
                <div key={index} className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">{area}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAnalyticsPage;