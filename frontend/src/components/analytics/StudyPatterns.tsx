import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

interface StudyPatternsProps {
  patterns: {
    hourly_pattern: Array<{ hour: number; count: number }>;
    daily_pattern: Array<{ day: string; count: number }>;
    recommended_hour: number;
    recommended_day: string;
    total_study_sessions: number;
  };
}

const StudyPatterns: React.FC<StudyPatternsProps> = ({ patterns }) => {
  // 시간대별 라벨
  const getHourLabel = (hour: number) => {
    if (hour === 0) return '12AM';
    if (hour < 12) return `${hour}AM`;
    if (hour === 12) return '12PM';
    return `${hour - 12}PM`;
  };

  // 시간대별 데이터 정리
  const hourlyData = patterns.hourly_pattern.map(item => ({
    hour: getHourLabel(item.hour),
    fullHour: item.hour,
    count: item.count,
    percentage: patterns.total_study_sessions > 0 ? (item.count / patterns.total_study_sessions * 100) : 0,
  }));

  // 요일별 데이터 정리
  const dailyData = patterns.daily_pattern.map(item => ({
    day: item.day,
    count: item.count,
    percentage: patterns.total_study_sessions > 0 ? (item.count / patterns.total_study_sessions * 100) : 0,
  }));

  // 가장 활발한 시간대/요일
  const peakHour = patterns.hourly_pattern.reduce((max, item) => 
    item.count > max.count ? item : max, { hour: 0, count: 0 }
  );

  const peakDay = patterns.daily_pattern.reduce((max, item) => 
    item.count > max.count ? item : max, { day: '', count: 0 }
  );

  // 커스텀 툴팁
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-medium text-gray-900 dark:text-gray-100">{label}</p>
          <p className="text-sm text-blue-600 dark:text-blue-400">
            {data.count}회 ({data.percentage.toFixed(1)}%)
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
          학습 패턴 분석
        </h2>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          최근 30일 기준
        </div>
      </div>

      {patterns.total_study_sessions === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 dark:text-gray-400">
            아직 학습 패턴 데이터가 충분하지 않습니다.
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* 패턴 요약 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <div className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-1">
                최적 학습 시간
              </div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {getHourLabel(patterns.recommended_hour)}
              </div>
              <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                {peakHour.count}회 학습
              </div>
            </div>

            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
              <div className="text-sm font-medium text-green-900 dark:text-green-200 mb-1">
                최적 학습 요일
              </div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {patterns.recommended_day}
              </div>
              <div className="text-xs text-green-600 dark:text-green-400 mt-1">
                {peakDay.count}회 학습
              </div>
            </div>

            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
              <div className="text-sm font-medium text-purple-900 dark:text-purple-200 mb-1">
                총 학습 세션
              </div>
              <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                {patterns.total_study_sessions}
              </div>
              <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                일평균 {(patterns.total_study_sessions / 30).toFixed(1)}회
              </div>
            </div>
          </div>

          {/* 시간대별 학습 패턴 */}
          <div>
            <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-4">
              시간대별 학습 활동
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourlyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis 
                    dataKey="hour" 
                    className="text-xs text-gray-600 dark:text-gray-400"
                    interval={1}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis className="text-xs text-gray-600 dark:text-gray-400" />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar 
                    dataKey="count" 
                    fill="#3b82f6" 
                    radius={[4, 4, 0, 0]}
                    name="학습 횟수"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 요일별 학습 패턴 */}
          <div>
            <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-4">
              요일별 학습 활동
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={dailyData}>
                  <PolarGrid className="opacity-30" />
                  <PolarAngleAxis 
                    dataKey="day" 
                    className="text-sm text-gray-600 dark:text-gray-400"
                  />
                  <PolarRadiusAxis 
                    angle={90} 
                    domain={[0, Math.max(...dailyData.map(d => d.count || 0)) || 10]}
                    className="text-xs text-gray-600 dark:text-gray-400"
                  />
                  <Radar
                    name="학습 횟수"
                    dataKey="count"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Tooltip 
                    formatter={(value, name) => [`${value}회`, name]}
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '0.5rem',
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 학습 패턴 인사이트 */}
          <div className="p-4 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800">
            <h3 className="text-sm font-medium text-indigo-900 dark:text-indigo-200 mb-2">
              🧠 학습 패턴 인사이트
            </h3>
            <div className="text-sm text-indigo-700 dark:text-indigo-300 space-y-1">
              <div>
                • {patterns.recommended_hour < 12 ? '오전' : '오후'} {getHourLabel(patterns.recommended_hour)}에 가장 활발하게 학습하고 있어요
              </div>
              <div>
                • {patterns.recommended_day}요일이 주요 학습일이에요
              </div>
              <div>
                • {patterns.total_study_sessions > 50 ? '매우 규칙적인' : 
                  patterns.total_study_sessions > 30 ? '꾸준한' : 
                  patterns.total_study_sessions > 15 ? '적당한' : '시작 단계의'} 학습 패턴을 보이고 있어요
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StudyPatterns;