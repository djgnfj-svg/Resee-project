import React from 'react';
import {
  TrophyIcon,
  FireIcon,
  StarIcon,
  ChartBarIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline';
import {
  TrophyIcon as TrophyIconSolid,
  FireIcon as FireIconSolid,
  StarIcon as StarIconSolid,
} from '@heroicons/react/24/solid';

interface AchievementStatsProps {
  achievements: {
    current_streak: number;
    max_streak: number;
    perfect_sessions: number;
    mastered_categories: number;
    monthly_progress: number;
    monthly_target: number;
    monthly_completed: number;
  };
}

const AchievementStats: React.FC<AchievementStatsProps> = ({ achievements }) => {
  // 배지 데이터
  const badges = [
    {
      id: 'streak_week',
      name: '7일 연속 학습',
      description: '일주일 연속으로 학습하기',
      icon: FireIcon,
      iconSolid: FireIconSolid,
      earned: achievements.current_streak >= 7,
      progress: Math.min(achievements.current_streak / 7 * 100, 100),
      color: 'orange',
      rarity: 'common',
    },
    {
      id: 'streak_month',
      name: '30일 연속 학습',
      description: '한 달 연속으로 학습하기',
      icon: FireIcon,
      iconSolid: FireIconSolid,
      earned: achievements.current_streak >= 30,
      progress: Math.min(achievements.current_streak / 30 * 100, 100),
      color: 'red',
      rarity: 'rare',
    },
    {
      id: 'perfect_10',
      name: '완벽한 10회',
      description: '10번의 완벽한 복습 세션',
      icon: StarIcon,
      iconSolid: StarIconSolid,
      earned: achievements.perfect_sessions >= 10,
      progress: Math.min(achievements.perfect_sessions / 10 * 100, 100),
      color: 'yellow',
      rarity: 'common',
    },
    {
      id: 'master_3',
      name: '마스터 3개',
      description: '3개 카테고리 마스터하기',
      icon: TrophyIcon,
      iconSolid: TrophyIconSolid,
      earned: achievements.mastered_categories >= 3,
      progress: Math.min(achievements.mastered_categories / 3 * 100, 100),
      color: 'blue',
      rarity: 'epic',
    },
    {
      id: 'monthly_goal',
      name: '월간 목표 달성',
      description: '월 100회 복습 목표 달성',
      icon: CalendarDaysIcon,
      iconSolid: CalendarDaysIcon,
      earned: achievements.monthly_progress >= 100,
      progress: achievements.monthly_progress,
      color: 'green',
      rarity: 'rare',
    },
    {
      id: 'streak_legend',
      name: '연속 학습 전설',
      description: '100일 연속 학습하기',
      icon: TrophyIcon,
      iconSolid: TrophyIconSolid,
      earned: achievements.current_streak >= 100,
      progress: Math.min(achievements.current_streak / 100 * 100, 100),
      color: 'purple',
      rarity: 'legendary',
    },
  ];

  // 색상 매핑
  const colorClasses = {
    orange: {
      bg: 'from-orange-400 to-red-500',
      text: 'text-orange-600 dark:text-orange-400',
      border: 'border-orange-200 dark:border-orange-800',
      bgLight: 'bg-orange-50 dark:bg-orange-900/20',
    },
    red: {
      bg: 'from-red-400 to-pink-500',
      text: 'text-red-600 dark:text-red-400',
      border: 'border-red-200 dark:border-red-800',
      bgLight: 'bg-red-50 dark:bg-red-900/20',
    },
    yellow: {
      bg: 'from-yellow-400 to-orange-500',
      text: 'text-yellow-600 dark:text-yellow-400',
      border: 'border-yellow-200 dark:border-yellow-800',
      bgLight: 'bg-yellow-50 dark:bg-yellow-900/20',
    },
    blue: {
      bg: 'from-blue-400 to-indigo-500',
      text: 'text-blue-600 dark:text-blue-400',
      border: 'border-blue-200 dark:border-blue-800',
      bgLight: 'bg-blue-50 dark:bg-blue-900/20',
    },
    green: {
      bg: 'from-green-400 to-emerald-500',
      text: 'text-green-600 dark:text-green-400',
      border: 'border-green-200 dark:border-green-800',
      bgLight: 'bg-green-50 dark:bg-green-900/20',
    },
    purple: {
      bg: 'from-purple-400 to-pink-500',
      text: 'text-purple-600 dark:text-purple-400',
      border: 'border-purple-200 dark:border-purple-800',
      bgLight: 'bg-purple-50 dark:bg-purple-900/20',
    },
  };

  // 희귀도 스타일
  const rarityStyles = {
    common: 'border-gray-300 dark:border-gray-600',
    rare: 'border-blue-400 dark:border-blue-500 shadow-blue-100 dark:shadow-blue-900/50',
    epic: 'border-purple-400 dark:border-purple-500 shadow-purple-100 dark:shadow-purple-900/50',
    legendary: 'border-yellow-400 dark:border-yellow-500 shadow-yellow-100 dark:shadow-yellow-900/50 shadow-lg',
  };

  // 획득한 배지 수
  const earnedBadgesCount = badges.filter(badge => badge.earned).length;

  return (
    <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-xl shadow-xl border border-gray-200/60 dark:border-gray-700/60 p-8 hover:shadow-2xl transition-all duration-300">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
          <span className="text-3xl mr-3">🏆</span>
          성취 시스템
        </h2>
        <div className="text-base text-gray-600 dark:text-gray-300 font-medium">
          {earnedBadgesCount}/{badges.length} 배지 획득
        </div>
      </div>

      <div className="space-y-6">
        {/* 성취 요약 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
            <div className="w-8 h-8 mx-auto mb-2 bg-gradient-to-br from-orange-400 to-red-500 rounded-full flex items-center justify-center">
              <FireIconSolid className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {achievements.current_streak}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              연속 학습일
            </div>
          </div>

          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="w-8 h-8 mx-auto mb-2 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center">
              <TrophyIconSolid className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {achievements.mastered_categories}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              마스터 카테고리
            </div>
          </div>

          <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <div className="w-8 h-8 mx-auto mb-2 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
              <StarIconSolid className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {achievements.perfect_sessions}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              완벽한 세션
            </div>
          </div>

          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
            <div className="w-8 h-8 mx-auto mb-2 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center">
              <ChartBarIcon className="w-5 h-5 text-white" />
            </div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {achievements.monthly_progress.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              월간 진행률
            </div>
          </div>
        </div>

        {/* 월간 목표 진행률 */}
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
              월간 복습 목표
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              {achievements.monthly_completed} / {achievements.monthly_target}회
            </div>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-green-400 to-emerald-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(achievements.monthly_progress, 100)}%` }}
            />
          </div>
          <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {achievements.monthly_target - achievements.monthly_completed > 0 ? 
              `목표까지 ${achievements.monthly_target - achievements.monthly_completed}회 남음` :
              '목표 달성 완료! 🎉'
            }
          </div>
        </div>

        {/* 배지 컬렉션 */}
        <div>
          <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-4">
            배지 컬렉션
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {badges.map((badge, index) => {
              const colors = colorClasses[badge.color as keyof typeof colorClasses];
              const IconComponent = badge.earned ? badge.iconSolid : badge.icon;
              
              return (
                <div
                  key={badge.id}
                  className={`
                    relative p-4 rounded-lg border-2 transition-all duration-300 hover:scale-105
                    ${badge.earned ? rarityStyles[badge.rarity as keyof typeof rarityStyles] : 'border-gray-200 dark:border-gray-700'}
                    ${badge.earned ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-700/50'}
                    ${badge.earned ? 'shadow-sm' : 'opacity-60'}
                    animate-slide-in
                  `}
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {/* 희귀도 표시 */}
                  {badge.earned && badge.rarity !== 'common' && (
                    <div className="absolute -top-2 -right-2">
                      <div className={`
                        w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white
                        ${badge.rarity === 'rare' ? 'bg-blue-500' :
                          badge.rarity === 'epic' ? 'bg-purple-500' : 'bg-yellow-500'}
                      `}>
                        {badge.rarity === 'rare' ? 'R' :
                         badge.rarity === 'epic' ? 'E' : 'L'}
                      </div>
                    </div>
                  )}

                  <div className="text-center">
                    <div className={`
                      w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center
                      ${badge.earned ? `bg-gradient-to-br ${colors.bg}` : 'bg-gray-200 dark:bg-gray-600'}
                    `}>
                      <IconComponent className={`
                        w-6 h-6 
                        ${badge.earned ? 'text-white' : 'text-gray-400 dark:text-gray-500'}
                      `} />
                    </div>
                    
                    <div className={`
                      text-sm font-medium mb-1
                      ${badge.earned ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'}
                    `}>
                      {badge.name}
                    </div>
                    
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                      {badge.description}
                    </div>

                    {/* 진행률 표시 */}
                    {!badge.earned && (
                      <div>
                        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-1.5 mb-1">
                          <div 
                            className={`bg-gradient-to-r ${colors.bg} h-1.5 rounded-full transition-all duration-500`}
                            style={{ width: `${badge.progress}%` }}
                          />
                        </div>
                        <div className="text-xs text-gray-400 dark:text-gray-500">
                          {badge.progress.toFixed(0)}%
                        </div>
                      </div>
                    )}

                    {badge.earned && (
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${colors.bgLight} ${colors.text}`}>
                        ✓ 획득완료
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 다음 목표 */}
        <div className="p-4 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800">
          <h3 className="text-sm font-medium text-indigo-900 dark:text-indigo-200 mb-2">
            🎯 다음 목표
          </h3>
          <div className="text-sm text-indigo-700 dark:text-indigo-300">
            {badges.find(badge => !badge.earned && badge.progress > 0) ? (
              <>
                <strong>{badges.find(badge => !badge.earned && badge.progress > 0)?.name}</strong> 배지까지 
                {(100 - (badges.find(badge => !badge.earned && badge.progress > 0)?.progress || 0)).toFixed(0)}% 남았어요!
              </>
            ) : earnedBadgesCount === badges.length ? (
              "🎉 모든 배지를 획득했습니다! 새로운 도전을 기다려주세요."
            ) : (
              "꾸준한 학습으로 첫 번째 배지를 획득해보세요!"
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AchievementStats;