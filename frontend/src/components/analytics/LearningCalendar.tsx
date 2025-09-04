import React, { useState } from 'react';
import { format, startOfYear, endOfYear, eachDayOfInterval, getDay } from 'date-fns';
import { ko } from 'date-fns/locale';

interface CalendarData {
  calendar_data: Array<{
    date: string;
    count: number;
    success_rate: number;
    intensity: number;
    remembered: number;
    partial: number;
    forgot: number;
  }>;
  monthly_summary: Array<{
    month: string;
    total_reviews: number;
    active_days: number;
    success_rate: number;
  }>;
  total_active_days: number;
  best_day: {
    date: string;
    count: number;
    success_rate: number;
  } | null;
}

interface LearningCalendarProps {
  calendarData: CalendarData;
}

const LearningCalendar: React.FC<LearningCalendarProps> = ({ calendarData }) => {
  const [selectedDay, setSelectedDay] = useState<any>(null);
  const [hoveredDay, setHoveredDay] = useState<any>(null);

  // API 데이터의 실제 날짜 범위 사용 (365일)
  const apiDates = calendarData.calendar_data.map(item => new Date(item.date)).sort((a, b) => a.getTime() - b.getTime());
  const dateRangeStart = apiDates[0];
  const dateRangeEnd = apiDates[apiDates.length - 1];
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const allDays = eachDayOfInterval({ start: dateRangeStart, end: dateRangeEnd });

  // 날짜별 데이터 맵 생성
  const dataMap = new Map(
    calendarData.calendar_data.map(item => [item.date, item])
  );

  // 강도별 색상 클래스
  const getIntensityColor = (intensity: number) => {
    switch (intensity) {
      case 0: return 'bg-gray-100 dark:bg-gray-800';
      case 1: return 'bg-green-200 dark:bg-green-900/50';
      case 2: return 'bg-green-300 dark:bg-green-800/70';
      case 3: return 'bg-green-400 dark:bg-green-700';
      case 4: return 'bg-green-500 dark:bg-green-600';
      default: return 'bg-gray-100 dark:bg-gray-800';
    }
  };

  // API 데이터 범위에 맞는 월별 그리드 생성
  const generateCalendarGrid = () => {
    const months = [];
    const startYear = dateRangeStart.getFullYear();
    const endYear = dateRangeEnd.getFullYear();
    
    // 시작 년도부터 끝 년도까지의 모든 월 처리
    for (let year = startYear; year <= endYear; year++) {
      const startMonth = year === startYear ? dateRangeStart.getMonth() : 0;
      const endMonth = year === endYear ? dateRangeEnd.getMonth() : 11;
      
      for (let month = startMonth; month <= endMonth; month++) {
        const monthStart = new Date(year, month, 1);
        const monthEnd = new Date(year, month + 1, 0);
        
        // 실제 데이터 범위와 교집합 계산
        const actualStart = monthStart < dateRangeStart ? dateRangeStart : monthStart;
        const actualEnd = monthEnd > dateRangeEnd ? dateRangeEnd : monthEnd;
        
        if (actualStart <= actualEnd) {
          const monthDays = eachDayOfInterval({ start: actualStart, end: actualEnd });
          
          // 첫 주의 빈 칸 계산 (월의 첫날 기준)
          const firstDayOfWeek = getDay(monthStart);
          const emptyDays = actualStart.getDate() === 1 ? Array(firstDayOfWeek).fill(null) : [];
          
          months.push({
            name: format(monthStart, 'yyyy년 MMM', { locale: ko }),
            days: [...emptyDays, ...monthDays],
          });
        }
      }
    }
    
    return months;
  };

  const months = generateCalendarGrid();

  // 통계 계산 - 안전성 검사 추가
  const totalReviews = calendarData.calendar_data?.reduce((sum, day) => sum + (day.count || 0), 0) || 0;
  const averageDaily = totalReviews / 365;
  const bestMonth = calendarData.monthly_summary?.length > 0 
    ? calendarData.monthly_summary.reduce((best, month) => 
        (month.total_reviews || 0) > (best?.total_reviews || 0) ? month : best, 
        calendarData.monthly_summary[0]
      )
    : null;

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
            <span className="text-3xl mr-3">📅</span>
            학습 캘린더 히트맵
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mt-2 text-base">
            GitHub 스타일 히트맵으로 보는 학습 기록
          </p>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded-lg">
          {format(dateRangeStart, 'yyyy.MM.dd')} - {format(dateRangeEnd, 'yyyy.MM.dd')}
        </div>
      </div>

      {/* 통계 요약 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
            {calendarData.total_active_days}
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400">
            활동일
          </div>
        </div>

        <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <div className="text-lg font-bold text-green-600 dark:text-green-400">
            {totalReviews}
          </div>
          <div className="text-xs text-green-600 dark:text-green-400">
            총 복습
          </div>
        </div>

        <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
          <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
            {averageDaily.toFixed(1)}
          </div>
          <div className="text-xs text-purple-600 dark:text-purple-400">
            일평균
          </div>
        </div>

        <div className="text-center p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800">
          <div className="text-lg font-bold text-amber-600 dark:text-amber-400">
            {calendarData.best_day?.count || 0}
          </div>
          <div className="text-xs text-amber-600 dark:text-amber-400">
            최고 기록
          </div>
        </div>
      </div>

      {/* 강도 범례 */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          적음
        </div>
        <div className="flex items-center space-x-1">
          {[0, 1, 2, 3, 4].map(level => (
            <div
              key={level}
              className={`w-3 h-3 rounded-sm ${getIntensityColor(level)}`}
            />
          ))}
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          많음
        </div>
      </div>

      {/* 캘린더 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 mb-6">
        {months.map((month, monthIndex) => (
          <div key={monthIndex} className="space-y-1">
            <div className="text-xs font-medium text-gray-600 dark:text-gray-400 text-center mb-2">
              {month.name}
            </div>
            <div className="grid grid-cols-7 gap-1">
              {['일', '월', '화', '수', '목', '금', '토'].map(day => (
                <div key={day} className="text-xs text-gray-400 dark:text-gray-500 text-center">
                  {day}
                </div>
              ))}
              {month.days.map((day, dayIndex) => {
                if (!day) {
                  return <div key={`empty-${dayIndex}`} className="w-3 h-3" />;
                }
                
                const dateStr = format(day, 'yyyy-MM-dd');
                const dayData = dataMap.get(dateStr);
                const intensity = dayData?.intensity || 0;
                
                return (
                  <div
                    key={dateStr}
                    className={`
                      w-3 h-3 rounded-sm cursor-pointer transition-all duration-200 hover:scale-125 hover:shadow-sm
                      ${getIntensityColor(intensity)}
                      ${selectedDay?.date === dateStr ? 'ring-2 ring-blue-500 ring-offset-1' : ''}
                    `}
                    onMouseEnter={() => setHoveredDay(dayData)}
                    onMouseLeave={() => setHoveredDay(null)}
                    onClick={() => setSelectedDay(dayData)}
                    title={`${format(day, 'yyyy년 MM월 dd일')}: ${dayData?.count || 0}회 복습`}
                  />
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* 호버/선택된 날짜 정보 */}
      {(hoveredDay || selectedDay) && (
        <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
          <div className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            {format(new Date((hoveredDay || selectedDay).date), 'yyyy년 MM월 dd일 (eee)', { locale: ko })}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-600 dark:text-gray-400">총 복습</div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {(hoveredDay || selectedDay).count}회
              </div>
            </div>
            <div>
              <div className="text-gray-600 dark:text-gray-400">성공률</div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                {(hoveredDay || selectedDay).success_rate}%
              </div>
            </div>
            <div>
              <div className="text-gray-600 dark:text-gray-400">기억함</div>
              <div className="font-medium text-green-600 dark:text-green-400">
                {(hoveredDay || selectedDay).remembered}회
              </div>
            </div>
            <div>
              <div className="text-gray-600 dark:text-gray-400">실패</div>
              <div className="font-medium text-red-600 dark:text-red-400">
                {(hoveredDay || selectedDay).forgot}회
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 월별 통계 */}
      <div className="mt-6">
        <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-4">
          월별 학습 통계
        </h3>
        {(!calendarData.monthly_summary || calendarData.monthly_summary.length === 0) ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm">월별 데이터가 없습니다.</div>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {calendarData.monthly_summary.slice(-12).map((month, index) => (
            <div
              key={month.month}
              className={`
                p-3 rounded-lg border transition-all duration-200 hover:shadow-md
                ${bestMonth && month.month === bestMonth.month
                  ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700' 
                  : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600'
                }
              `}
            >
              <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                {format(new Date(month.month + '-01'), 'yyyy년 MM월', { locale: ko })}
              </div>
              <div className="text-sm font-bold text-gray-900 dark:text-gray-100">
                {month.total_reviews}회
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {month.active_days}일 활동
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                성공률 {month.success_rate}%
              </div>
              {bestMonth && month.month === bestMonth.month && (
                <div className="text-xs text-green-600 dark:text-green-400 font-medium mt-1">
                  🏆 최고
                </div>
              )}
            </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LearningCalendar;