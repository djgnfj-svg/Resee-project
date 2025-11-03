import React from 'react';

const DashboardHero: React.FC = () => {
  return (
    <div className="mb-8 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 text-white">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">안녕하세요! 📚</h1>
          <p className="text-indigo-100 text-lg">
            오늘도 성실하게 학습하는 당신을 응원합니다.
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">
            {new Date().toLocaleDateString('ko-KR', { 
              month: 'long', 
              day: 'numeric', 
              weekday: 'short' 
            })}
          </div>
          <div className="text-indigo-100 mt-1">
            {new Date().toLocaleTimeString('ko-KR', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardHero;