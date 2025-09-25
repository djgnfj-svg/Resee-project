import React from 'react';
import ReactMarkdown from 'react-markdown';
import { ReviewSchedule } from '../../types';

interface ReviewCardProps {
  review: ReviewSchedule;
  isFlipped: boolean;
  showContent: boolean;
  onFlip: () => void;
  onBack: () => void;
}

const ReviewCard: React.FC<ReviewCardProps> = ({
  review,
  isFlipped,
  showContent,
  onFlip,
  onBack,
}) => {
  return (
    <div className="relative h-96 mb-8">
      <div className={`absolute inset-0 w-full h-full transition-transform duration-700 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
        {/* Front of Card */}
        <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden border-2 border-blue-200 dark:border-blue-700">
          <div className="p-8 h-full flex flex-col justify-center items-center text-center">
            <div className="mb-6">
              <div className="text-4xl mb-4">🧠</div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                {review.content.title}
              </h2>
              <div className="flex items-center justify-center space-x-4 text-sm">
                {review.content.category && (
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                    {review.content.category.name}
                  </span>
                )}
                <span className="text-gray-500 dark:text-gray-400 text-xs">
                  {review.initial_review_completed ? 
                    `${review.interval_index + 1}번째 복습` : 
                    '첫 번째 복습'}
                </span>
              </div>
            </div>
            
            <div className="text-gray-600 dark:text-gray-400 mb-8">
              이 내용을 얼마나 잘 기억하고 있나요?
            </div>
            
            <button
              onClick={onFlip}
              className="bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 dark:hover:from-blue-500 dark:hover:to-purple-600 transition-all duration-300 transform hover:scale-105 shadow-lg dark:shadow-gray-900/40"
            >
              내용 확인하기 (Space)
            </button>
          </div>
        </div>
        
        {/* Back of Card */}
        <div className="absolute inset-0 w-full h-full bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden rotate-y-180 border-2 border-green-200 dark:border-green-700">
          <div className="p-8 h-full flex flex-col">
            <div className="flex-1 overflow-y-auto">
              <div className="prose prose-lg dark:prose-invert max-w-none">
                <ReactMarkdown>
                  {review.content.content}
                </ReactMarkdown>
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <button
                onClick={onBack}
                className="text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 text-sm mb-4 transition-colors"
              >
                ← 뒤로가기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewCard;