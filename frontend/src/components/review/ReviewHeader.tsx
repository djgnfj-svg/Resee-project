import React from 'react';

interface ReviewHeaderProps {
  remainingReviews: number;
}

const ReviewHeader: React.FC<ReviewHeaderProps> = ({
  remainingReviews,
}) => {

  return (
    <div className="mb-8">
      {/* Gradient Banner Header */}
      <div className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 shadow-lg mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          {/* Title Section */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">복습 타임</h1>
                <p className="text-indigo-100 text-sm mt-1">
                  에빙하우스 망각곡선을 활용한 스마트 복습 시스템
                </p>
              </div>
            </div>
          </div>

          {/* Stats Section */}
          {remainingReviews > 0 && (
            <div className="bg-white/20 backdrop-blur-sm rounded-xl p-4 min-w-[140px] border border-white/30">
              <div className="flex items-center gap-2 mb-1">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-xs font-medium text-white/90">남은 복습</span>
              </div>
              <div className="text-3xl font-bold text-white">{remainingReviews}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReviewHeader;