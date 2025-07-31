import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import { 
  ClockIcon, 
  CalendarIcon,
  FireIcon,
  ChartBarIcon,
  StarIcon
} from '@heroicons/react/24/outline';
interface LearningPatternsProps {
  data: {
    hourlyPattern: Array<{
      hour: number;
      studySessions: number;
      averagePerformance: number;
      totalTimeSpent: number;
      efficiency: number;
    }>;
    weeklyPattern: Array<{
      day: string;
      dayOfWeek: number;
      studySessions: number;
      averagePerformance: number;
      totalReviews: number;
      timeSpent: number;
    }>;
    streakAnalysis: {
      currentStreak: number;
      longestStreak: number;
      streakHistory: Array<{
        date: string;
        streakLength: number;
        performance: number;
      }>;
    };
    difficultyProgression: Array<{
      week: string;
      easy: number;
      medium: number;
      hard: number;
      averageScore: number;
    }>;
    learningVelocity: Array<{
      category: string;
      masterySpeed: number; // 숙달까지 걸린 복습 횟수
      retentionRate: number;
      difficultyLevel: number;
      totalContent: number;
    }>;
  };
}

const WEEKDAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const DIFFICULTY_COLORS = {
  easy: '#10b981',
  medium: '#f59e0b', 
  hard: '#ef4444'
};

const LearningPatterns: React.FC<LearningPatternsProps> = ({ data }) => {
  const { hourlyPattern, weeklyPattern, streakAnalysis, difficultyProgression, learningVelocity } = data;

  // NaN 방지를 위한 숫자 정리 유틸리티 함수
  const sanitizeNumber = (value: any, fallback: number = 0): number => {
    if (value === null || value === undefined) return fallback;
    const num = Number(value);
    return isNaN(num) || !isFinite(num) ? fallback : num;
  };

  // 최적 학습 시간 계산
  const optimalStudyTime = useMemo(() => {
    if (!hourlyPattern || hourlyPattern.length === 0 || !weeklyPattern || weeklyPattern.length === 0) {
      return {
        hour: 0,
        hourEfficiency: 0,
        day: '월',
        dayPerformance: 0
      };
    }
    
    const bestHour = hourlyPattern.reduce((best, current) => 
      sanitizeNumber(current.efficiency) > sanitizeNumber(best.efficiency) ? current : best
    );
    const bestDay = weeklyPattern.reduce((best, current) => 
      sanitizeNumber(current.averagePerformance) > sanitizeNumber(best.averagePerformance) ? current : best
    );
    
    return {
      hour: sanitizeNumber(bestHour.hour),
      hourEfficiency: sanitizeNumber(bestHour.efficiency),
      day: bestDay.day || '월',
      dayPerformance: sanitizeNumber(bestDay.averagePerformance)
    };
  }, [hourlyPattern, weeklyPattern]);

  // 학습 일관성 점수 계산
  const consistencyScore = useMemo(() => {
    const weeklyVariance = weeklyPattern.reduce((acc, day) => {
      const avgSessions = weeklyPattern.reduce((sum, d) => sum + d.studySessions, 0) / 7;
      return acc + Math.pow(day.studySessions - avgSessions, 2);
    }, 0) / 7;
    
    const consistencyScore = Math.max(0, 100 - (Math.sqrt(weeklyVariance) * 10));
    return Math.round(consistencyScore);
  }, [weeklyPattern]);

  // 히트맵을 위한 데이터 변환
  const heatmapData = useMemo(() => {
    const matrix: number[][] = [];
    for (let day = 0; day < 7; day++) {
      matrix[day] = [];
      for (let hour = 0; hour < 24; hour++) {
        const dayData = weeklyPattern[day];
        const hourData = hourlyPattern[hour];
        // 요일과 시간대의 활동 강도를 조합
        const intensity = dayData && hourData ? 
          sanitizeNumber(((sanitizeNumber(dayData.studySessions) * sanitizeNumber(hourData.studySessions)) / 10)) : 0;
        matrix[day][hour] = Math.min(100, sanitizeNumber(intensity));
      }
    }
    return matrix;
  }, [weeklyPattern, hourlyPattern]);

  const formatHour = (hour: number) => {
    return hour === 0 ? '12AM' : hour < 12 ? `${hour}AM` : hour === 12 ? '12PM' : `${hour-12}PM`;
  };

  const getIntensityColor = (intensity: number) => {
    if (intensity === 0) return '#f3f4f6';
    if (intensity < 20) return '#dcfce7';
    if (intensity < 40) return '#bbf7d0';
    if (intensity < 60) return '#86efac';
    if (intensity < 80) return '#4ade80';
    return '#22c55e';
  };

  return (
    <div className="space-y-6">
      {/* 핵심 패턴 지표 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">최적 학습 시간</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {formatHour(optimalStudyTime.hour)}
              </p>
            </div>
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
              <ClockIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            효율성 {optimalStudyTime.hourEfficiency}%
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">최적 요일</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {optimalStudyTime.day}요일
              </p>
            </div>
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center">
              <CalendarIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            성과 {optimalStudyTime.dayPerformance.toFixed(1)}%
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">학습 일관성</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {consistencyScore}%
              </p>
            </div>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              consistencyScore >= 80 
                ? 'bg-green-100 dark:bg-green-900/30' 
                : consistencyScore >= 60
                ? 'bg-yellow-100 dark:bg-yellow-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            }`}>
              <ChartBarIcon className={`w-5 h-5 ${
                consistencyScore >= 80 
                  ? 'text-green-600 dark:text-green-400' 
                  : consistencyScore >= 60
                  ? 'text-yellow-600 dark:text-yellow-400'
                  : 'text-red-600 dark:text-red-400'
              }`} />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            주간 균일성
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">연속 학습</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {streakAnalysis.currentStreak}일
              </p>
            </div>
            <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center">
              <FireIcon className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            최고 {streakAnalysis.longestStreak}일
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* 시간대별 학습 패턴 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            ⏰ 시간대별 학습 효율성
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={hourlyPattern}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="hour" 
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                  tickFormatter={formatHour}
                />
                <YAxis 
                  yAxisId="left"
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <Tooltip 
                  labelFormatter={(hour) => `${formatHour(hour as number)}`}
                  formatter={(value, name) => [
                    name === 'efficiency' ? `${value}%` : value,
                    name === 'efficiency' ? '효율성' : '세션 수'
                  ]}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="efficiency"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: '#3b82f6', r: 2 }}
                  name="효율성"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 요일별 학습 패턴 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            📅 요일별 학습 패턴
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyPattern}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="day" 
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  yAxisId="left"
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <YAxis 
                  yAxisId="right"
                  orientation="right"
                  tick={{ fontSize: 11 }}
                  stroke="#9ca3af"
                />
                <Tooltip 
                  formatter={(value, name) => [
                    name === 'averagePerformance' ? `${value}%` : value,
                    name === 'averagePerformance' ? '평균 성과' : '총 복습'
                  ]}
                />
                <Bar
                  yAxisId="left"
                  dataKey="totalReviews"
                  fill="#10b981"
                  name="총 복습"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* 학습 활동 히트맵 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          🔥 학습 활동 히트맵
        </h3>
        <div className="overflow-x-auto">
          <div className="min-w-full">
            <div className="flex items-center mb-4">
              <span className="text-xs text-gray-500 dark:text-gray-400 mr-4">시간대</span>
              <div className="flex space-x-1">
                {Array.from({ length: 24 }, (_, i) => (
                  <div key={i} className="w-4 text-center">
                    <span className="text-xs text-gray-400">{i % 6 === 0 ? i : ''}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-1">
              {WEEKDAY_NAMES.map((dayName, dayIndex) => (
                <div key={dayName} className="flex items-center">
                  <span className="text-xs text-gray-600 dark:text-gray-400 w-8 text-right mr-2">
                    {dayName}
                  </span>
                  <div className="flex space-x-1">
                    {Array.from({ length: 24 }, (_, hourIndex) => {
                      const intensity = heatmapData[dayIndex]?.[hourIndex] || 0;
                      return (
                        <div
                          key={`${dayIndex}-${hourIndex}`}
                          className="w-4 h-4 rounded-sm border border-gray-200 dark:border-gray-600"
                          style={{ backgroundColor: getIntensityColor(intensity) }}
                          title={`${dayName}요일 ${hourIndex}시: ${intensity.toFixed(0)}% 활동량`}
                        />
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between mt-4 text-xs text-gray-500 dark:text-gray-400">
              <span>활동 강도</span>
              <div className="flex items-center space-x-2">
                <span>낮음</span>
                <div className="flex space-x-1">
                  {[0, 20, 40, 60, 80].map((intensity) => (
                    <div
                      key={intensity}
                      className="w-3 h-3 rounded-sm"
                      style={{ backgroundColor: getIntensityColor(intensity) }}
                    />
                  ))}
                </div>
                <span>높음</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 카테고리별 학습 속도 분석 */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          🎯 카테고리별 학습 속도 & 난이도
        </h3>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={learningVelocity}>
              <PolarGrid />
              <PolarAngleAxis dataKey="category" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis 
                angle={30} 
                domain={[0, 100]} 
                tick={{ fontSize: 10 }}
                tickCount={5}
              />
              <Radar
                name="숙달 속도"
                dataKey="masterySpeed"
                stroke="#8b5cf6"
                fill="#8b5cf6"
                fillOpacity={0.3}
                strokeWidth={2}
              />
              <Radar
                name="기억 유지율"
                dataKey="retentionRate"
                stroke="#10b981"
                fill="#10b981"
                fillOpacity={0.2}
                strokeWidth={2}
              />
              <Tooltip 
                formatter={(value, name) => [
                  `${value}${name === '숙달 속도' ? '회' : '%'}`,
                  name
                ]}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 패턴 인사이트 */}
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
              <StarIcon className="w-4 h-4 text-white" />
            </div>
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-medium text-purple-900 dark:text-purple-100 mb-3">
              🎯 학습 패턴 분석 결과
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h5 className="font-medium text-purple-800 dark:text-purple-200 mb-2">최적화 제안</h5>
                <ul className="text-sm text-purple-700 dark:text-purple-300 space-y-1">
                  <li>• {formatHour(optimalStudyTime.hour)} 시간대 집중 학습 권장</li>
                  <li>• {optimalStudyTime.day}요일 중요 콘텐츠 복습</li>
                  <li>• 일관성 개선을 위한 규칙적인 학습 스케줄</li>
                </ul>
              </div>
              <div>
                <h5 className="font-medium text-purple-800 dark:text-purple-200 mb-2">성취 현황</h5>
                <ul className="text-sm text-purple-700 dark:text-purple-300 space-y-1">
                  <li>• 현재 {streakAnalysis.currentStreak}일 연속 학습 중</li>
                  <li>• 학습 일관성 {consistencyScore}% 달성</li>
                  <li>• 개인 최적 시간대 {optimalStudyTime.hourEfficiency}% 효율성</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LearningPatterns;