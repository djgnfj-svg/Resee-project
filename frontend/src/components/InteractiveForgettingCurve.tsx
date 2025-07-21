import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceDot, Tooltip } from 'recharts';

interface ForgettingCurveProps {
  className?: string;
}

const InteractiveForgettingCurve: React.FC<ForgettingCurveProps> = ({ className = '' }) => {
  const [activePoint, setActivePoint] = useState(0);
  const [isAnimating, setIsAnimating] = useState(true);

  // 에빙하우스 망각곡선 데이터 (실제 연구 기반)
  const forgettingCurveData = [
    { day: 0, retention: 100, label: '학습 직후', description: '새로운 정보를 완전히 기억' },
    { day: 1, retention: 44, label: '1일 후', description: '56%의 정보를 망각' },
    { day: 3, retention: 35, label: '3일 후', description: '복습 없이는 65% 망각' },
    { day: 7, retention: 25, label: '1주 후', description: '75%의 정보 손실' },
    { day: 14, retention: 20, label: '2주 후', description: '80% 망각 상태' },
    { day: 30, retention: 15, label: '1개월 후', description: '장기 기억으로 이동한 15%만 유지' }
  ];

  // 복습을 통한 기억력 강화 데이터
  const reviewData = [
    { day: 0, retention: 100, label: '학습 직후' },
    { day: 1, retention: 85, label: '1일 복습' },
    { day: 3, retention: 80, label: '3일 복습' },
    { day: 7, retention: 75, label: '1주 복습' },
    { day: 14, retention: 70, label: '2주 복습' },
    { day: 30, retention: 65, label: '1개월 복습' }
  ];

  useEffect(() => {
    if (!isAnimating) return;
    
    const interval = setInterval(() => {
      setActivePoint((prev) => (prev + 1) % forgettingCurveData.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [isAnimating, forgettingCurveData.length]);

  const handleMouseEnter = (index: number) => {
    setIsAnimating(false);
    setActivePoint(index);
  };

  const handleMouseLeave = () => {
    setIsAnimating(true);
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
          <p className="font-semibold text-gray-900 dark:text-gray-100">
            {payload[0].payload.label}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            기억률: {payload[0].value}%
          </p>
          {payload[0].payload.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {payload[0].payload.description}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`relative ${className}`}>
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          에빙하우스 망각곡선
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          복습 없이는 하루 만에 56%를 망각합니다
        </p>
      </div>

      <div className="relative h-80 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={forgettingCurveData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <XAxis 
              dataKey="day" 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickFormatter={(value) => `${value}일`}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* 망각곡선 */}
            <Line
              type="monotone"
              dataKey="retention"
              stroke="#EF4444"
              strokeWidth={3}
              dot={false}
              name="망각곡선"
            />
            
            {/* 복습 효과 곡선 */}
            <Line
              type="monotone"
              data={reviewData}
              dataKey="retention"
              stroke="#10B981"
              strokeWidth={3}
              strokeDasharray="8 4"
              dot={false}
              name="복습 후"
            />
            
            {/* 활성 포인트 */}
            {forgettingCurveData.map((point, index) => (
              <ReferenceDot
                key={index}
                x={point.day}
                y={point.retention}
                r={index === activePoint ? 8 : 4}
                fill={index === activePoint ? "#EF4444" : "#FCA5A5"}
                stroke="#FFFFFF"
                strokeWidth={2}
                className="cursor-pointer transition-all duration-300"
                onMouseEnter={() => handleMouseEnter(index)}
                onMouseLeave={handleMouseLeave}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 범례 */}
      <div className="flex justify-center space-x-6 mb-4">
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-red-500 mr-2"></div>
          <span className="text-sm text-gray-600 dark:text-gray-400">복습 없음</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-0.5 bg-green-500 border-dashed mr-2" style={{ borderTop: '2px dashed' }}></div>
          <span className="text-sm text-gray-600 dark:text-gray-400">Resee 복습</span>
        </div>
      </div>

      {/* 활성 포인트 정보 */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 rounded-xl p-6 border border-red-200 dark:border-red-800">
        <div className="text-center">
          <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {forgettingCurveData[activePoint]?.label}
          </h4>
          <div className="text-3xl font-bold text-red-600 dark:text-red-400 mb-2">
            {forgettingCurveData[activePoint]?.retention}%
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {forgettingCurveData[activePoint]?.description}
          </p>
        </div>
      </div>

      {/* Resee 복습 효과 설명 */}
      <div className="mt-6 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 dark:bg-green-800 rounded-full mb-4">
            <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443a55.381 55.381 0 015.25 2.882V15" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Resee와 함께라면
          </h4>
          <p className="text-gray-600 dark:text-gray-400">
            과학적 복습 간격(1→3→7→14→30일)으로 <br/>
            <span className="font-semibold text-green-600 dark:text-green-400">65% 이상의 기억률 유지</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default InteractiveForgettingCurve;