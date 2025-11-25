import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ObjectiveReviewProps } from './types';

/**
 * Objective Review Mode: 기억 확인 (제목 → 내용 확인)
 * 사용자가 제목을 보고 내용을 기억하는지 확인하는 모드
 */
const ObjectiveReviewCard: React.FC<ObjectiveReviewProps> = ({
  review,
  showContent,
  onFlip,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 break-words flex-1 min-w-0">
          {review.content.title}
        </h2>
        <div className="flex items-center gap-2 flex-shrink-0">
          {review.content.category && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
              {review.content.category.name}
            </span>
          )}
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
            {review.initial_review_completed ? `${review.interval_index + 1}번째 복습` : '첫 복습'}
          </span>
        </div>
      </div>

      {/* Content Area */}
      {!showContent ? (
        /* Hidden State: 기억 확인 */
        <div className="flex flex-col items-center justify-center py-12">
          <p className="text-gray-600 dark:text-gray-400 mb-6 text-center">
            이 내용을 기억하시나요?
          </p>
          <button
            onClick={onFlip}
            className="px-8 py-3 bg-primary-600 dark:bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            aria-label="내용 확인하기"
          >
            내용 확인하기
          </button>
        </div>
      ) : (
        /* Revealed State: 내용 표시 */
        <div className="prose dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {review.content.content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
};

if (process.env.NODE_ENV === 'development') {
  (ObjectiveReviewCard as any).whyDidYouRender = true;
}

export default React.memo(ObjectiveReviewCard);
