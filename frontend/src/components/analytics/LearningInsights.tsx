import React from 'react';
import {
  AcademicCapIcon,
  ChartBarIcon,
  ClockIcon,
  FireIcon,
  TrophyIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';

interface LearningInsightsProps {
  insights: {
    total_content: number;
    total_reviews: number;
    recent_30d_reviews: number;
    recent_7d_reviews: number;
    recent_success_rate: number;
    week_success_rate: number;
    average_interval_days: number;
    streak_days: number;
  };
}

const LearningInsights: React.FC<LearningInsightsProps> = ({ insights }) => {
  const stats = [
    {
      name: '총 학습 콘텐츠',
      value: insights.total_content,
      icon: AcademicCapIcon,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      suffix: '개',
    },
    {
      name: '전체 복습 횟수',
      value: insights.total_reviews,
      icon: ChartBarIcon,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      suffix: '회',
    },
    {
      name: '최근 성공률',
      value: insights.recent_success_rate,
      icon: TrophyIcon,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
      suffix: '%',
    },
    {
      name: '연속 학습일',
      value: insights.streak_days,
      icon: FireIcon,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
      suffix: '일',
    },
    {
      name: '평균 복습 간격',
      value: insights.average_interval_days,
      icon: ClockIcon,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-100 dark:bg-purple-900/30',
      suffix: '일',
    },
    {
      name: '최근 7일 복습',
      value: insights.recent_7d_reviews,
      icon: CalendarDaysIcon,
      color: 'text-indigo-600 dark:text-indigo-400',
      bgColor: 'bg-indigo-100 dark:bg-indigo-900/30',
      suffix: '회',
    },
  ];

  return (
    <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl shadow-xl border border-gray-200/60 dark:border-gray-700/60 p-8 hover:shadow-2xl transition-all duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          <span className="text-3xl mr-3">💡</span>
          학습 인사이트
        </h2>
        <div className="text-base text-gray-600 dark:text-gray-300 font-medium">
          최근 30일 기준
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat, index) => (
          <div
            key={stat.name}
            className="relative overflow-hidden rounded-lg bg-gray-50 dark:bg-gray-700/50 p-4 hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 animate-slide-in"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center">
              <div className={`rounded-md p-3 ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.name}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {typeof stat.value === 'number' && stat.value % 1 !== 0 
                    ? stat.value.toFixed(1) 
                    : stat.value.toLocaleString()
                  }
                  <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-1">
                    {stat.suffix}
                  </span>
                </p>
              </div>
            </div>

            {/* 개선 지표 표시 */}
            {stat.name === '최근 성공률' && (
              <div className="mt-2 flex items-center">
                <div className={`flex items-center text-sm ${
                  insights.week_success_rate > insights.recent_success_rate 
                    ? 'text-green-600 dark:text-green-400' 
                    : insights.week_success_rate < insights.recent_success_rate
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {insights.week_success_rate > insights.recent_success_rate ? '↗' :
                   insights.week_success_rate < insights.recent_success_rate ? '↘' : '→'}
                  <span className="ml-1">
                    이번 주: {insights.week_success_rate.toFixed(1)}%
                  </span>
                </div>
              </div>
            )}

            {stat.name === '최근 7일 복습' && (
              <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                일일 평균: {(insights.recent_7d_reviews / 7).toFixed(1)}회
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 종합 평가 */}
      <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <TrophyIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200">
              학습 상태 종합 평가
            </h3>
            <div className="mt-1 text-sm text-blue-700 dark:text-blue-300">
              {insights.recent_success_rate >= 80 ? (
                "🎉 훌륭한 학습 성과를 보이고 있어요! 이 페이스를 유지하세요."
              ) : insights.recent_success_rate >= 60 ? (
                "👍 안정적인 학습을 하고 있어요. 조금 더 집중하면 더 좋은 결과를 얻을 수 있을 거예요."
              ) : insights.recent_success_rate >= 40 ? (
                "💪 학습 리듬을 찾아가고 있어요. 꾸준히 복습하면 성과가 개선될 거예요."
              ) : (
                "🔥 새로운 시작! 규칙적인 복습으로 학습 효과를 높여보세요."
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningInsights;