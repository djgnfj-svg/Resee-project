import React from 'react';

interface ReviewHeaderProps {
  remainingReviews: number;
}

const ReviewHeader: React.FC<ReviewHeaderProps> = ({
  remainingReviews,
}) => {

  return (
    <div className="mb-8 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">💡 복습 정보</h1>
          <p className="text-indigo-100">
            오늘 예정된 복습을 완료하고 장기 기억을 강화하세요
          </p>
        </div>
        {remainingReviews > 0 && (
          <div className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/20 backdrop-blur-sm text-white px-6 py-3 text-sm font-semibold border border-white/30 w-full sm:w-auto">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>남은 복습: {remainingReviews}개</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewHeader;