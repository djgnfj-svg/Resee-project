import React from 'react';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Link } from 'react-router-dom';
import {
  LightBulbIcon,
  ClockIcon,
  ChartBarIcon,
  FireIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

interface Recommendation {
  type: string;
  title: string;
  message: string;
  action: string;
  category_id?: number;
  hour?: number;
}

interface RecommendationsProps {
  recommendations: Recommendation[];
}

const Recommendations: React.FC<RecommendationsProps> = ({ recommendations }) => {
  // 추천 타입별 아이콘과 색상
  const getRecommendationStyle = (type: string) => {
    switch (type) {
      case 'weak_category':
        return {
          icon: ExclamationTriangleIcon,
          color: 'amber',
          bgColor: 'bg-amber-50 dark:bg-amber-900/20',
          borderColor: 'border-amber-200 dark:border-amber-800',
          textColor: 'text-amber-800 dark:text-amber-200',
          iconColor: 'text-amber-600 dark:text-amber-400',
        };
      case 'optimal_time':
        return {
          icon: ClockIcon,
          color: 'blue',
          bgColor: 'bg-blue-50 dark:bg-blue-900/20',
          borderColor: 'border-blue-200 dark:border-blue-800',
          textColor: 'text-blue-800 dark:text-blue-200',
          iconColor: 'text-blue-600 dark:text-blue-400',
        };
      case 'streak_celebration':
        return {
          icon: FireIcon,
          color: 'green',
          bgColor: 'bg-green-50 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          textColor: 'text-green-800 dark:text-green-200',
          iconColor: 'text-green-600 dark:text-green-400',
        };
      case 'review_suggestion':
        return {
          icon: ChartBarIcon,
          color: 'purple',
          bgColor: 'bg-purple-50 dark:bg-purple-900/20',
          borderColor: 'border-purple-200 dark:border-purple-800',
          textColor: 'text-purple-800 dark:text-purple-200',
          iconColor: 'text-purple-600 dark:text-purple-400',
        };
      default:
        return {
          icon: LightBulbIcon,
          color: 'gray',
          bgColor: 'bg-gray-50 dark:bg-gray-700/50',
          borderColor: 'border-gray-200 dark:border-gray-600',
          textColor: 'text-gray-800 dark:text-gray-200',
          iconColor: 'text-gray-600 dark:text-gray-400',
        };
    }
  };

  // 액션에 따른 버튼 텍스트
  const getActionText = (action: string) => {
    switch (action) {
      case 'review_category': return '카테고리 복습하기';
      case 'schedule_reminder': return '알림 설정하기';
      case 'continue_streak': return '계속 학습하기';
      case 'improve_weak_areas': return '약점 개선하기';
      default: return '확인하기';
    }
  };

  // 액션 처리
  const handleAction = (recommendation: Recommendation) => {
    switch (recommendation.action) {
      case 'review_category':
        if (recommendation.category_id) {
          // 카테고리별 복습 페이지로 이동
          window.location.href = `/review?category=${recommendation.category_id}`;
        }
        break;
      case 'schedule_reminder':
        // 설정 페이지로 이동
        window.location.href = '/settings';
        break;
      case 'continue_streak':
        // 복습 페이지로 이동
        window.location.href = '/review';
        break;
      default:
        // 기본적으로 대시보드 새로고침
        window.location.reload();
    }
  };

  if (recommendations.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2 mb-4">
        <LightBulbIcon className="w-5 h-5 text-yellow-500" />
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          AI 추천
        </h2>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-400">
          {recommendations.length}개
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.map((recommendation, index) => {
          const style = getRecommendationStyle(recommendation.type);
          const IconComponent = style.icon;

          return (
            <div
              key={index}
              className={`
                p-4 rounded-lg border transition-all duration-200 hover:shadow-md animate-slide-in
                ${style.bgColor} ${style.borderColor}
              `}
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <div className="flex items-start space-x-3">
                <div className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  ${style.color === 'amber' ? 'bg-amber-100 dark:bg-amber-900/30' :
                    style.color === 'blue' ? 'bg-blue-100 dark:bg-blue-900/30' :
                    style.color === 'green' ? 'bg-green-100 dark:bg-green-900/30' :
                    style.color === 'purple' ? 'bg-purple-100 dark:bg-purple-900/30' :
                    'bg-gray-100 dark:bg-gray-700'
                  }
                `}>
                  <IconComponent className={`w-4 h-4 ${style.iconColor}`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium ${style.textColor} mb-1`}>
                    {recommendation.title}
                  </div>
                  <div className={`text-sm ${style.textColor} opacity-90 mb-3`}>
                    {recommendation.message}
                  </div>
                  
                  <button
                    onClick={() => handleAction(recommendation)}
                    className={`
                      inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md
                      transition-colors duration-200 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2
                      ${style.color === 'amber' ? 
                        'text-amber-700 dark:text-amber-200 bg-amber-100 dark:bg-amber-900/30 hover:bg-amber-200 dark:hover:bg-amber-900/50 focus:ring-amber-500' :
                        style.color === 'blue' ? 
                        'text-blue-700 dark:text-blue-200 bg-blue-100 dark:bg-blue-900/30 hover:bg-blue-200 dark:hover:bg-blue-900/50 focus:ring-blue-500' :
                        style.color === 'green' ? 
                        'text-green-700 dark:text-green-200 bg-green-100 dark:bg-green-900/30 hover:bg-green-200 dark:hover:bg-green-900/50 focus:ring-green-500' :
                        style.color === 'purple' ? 
                        'text-purple-700 dark:text-purple-200 bg-purple-100 dark:bg-purple-900/30 hover:bg-purple-200 dark:hover:bg-purple-900/50 focus:ring-purple-500' :
                        'text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 focus:ring-gray-500'
                      }
                    `}
                  >
                    {getActionText(recommendation.action)}
                  </button>
                </div>
              </div>

              {/* 특별한 추천 타입에 대한 추가 정보 */}
              {recommendation.type === 'optimal_time' && recommendation.hour && (
                <div className="mt-3 pt-3 border-t border-blue-200 dark:border-blue-700">
                  <div className="text-xs text-blue-600 dark:text-blue-400">
                    💡 {recommendation.hour}시경에 알림을 설정해보세요
                  </div>
                </div>
              )}

              {recommendation.type === 'streak_celebration' && (
                <div className="mt-3 pt-3 border-t border-green-200 dark:border-green-700">
                  <div className="text-xs text-green-600 dark:text-green-400">
                    🎖️ 이 기세로 더 높은 기록에 도전해보세요!
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 추천 시스템 설명 */}
      <div className="mt-6 p-4 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800">
        <div className="flex items-start space-x-3">
          <CheckCircleIcon className="flex-shrink-0 w-5 h-5 text-indigo-600 dark:text-indigo-400 mt-0.5" />
          <div>
            <div className="text-sm font-medium text-indigo-900 dark:text-indigo-200 mb-1">
              지능형 개인화 추천
            </div>
            <div className="text-sm text-indigo-700 dark:text-indigo-300">
              학습 패턴과 성과를 분석하여 개인에게 최적화된 학습 방법을 추천합니다. 
              추천사항을 따라 학습하면 더 효과적인 결과를 얻을 수 있어요.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Recommendations;