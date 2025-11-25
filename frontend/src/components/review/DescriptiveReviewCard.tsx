import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { DescriptiveReviewProps } from './types';

/**
 * Descriptive Review Mode: 서술형 (제목 → 내용 작성 + AI 평가)
 * 사용자가 제목을 보고 내용을 자신의 말로 작성하고 AI 평가를 받는 모드
 */
const DescriptiveReviewCard: React.FC<DescriptiveReviewProps> = ({
  review,
  descriptiveAnswer,
  onDescriptiveAnswerChange,
  onSubmitDescriptive,
  isSubmitting = false,
  submittedAnswer,
  aiEvaluation,
}) => {
  const hasEvaluation = !!aiEvaluation;

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
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
            서술형
          </span>
        </div>
      </div>

      {!hasEvaluation ? (
        /* Answer Input View */
        <div className="space-y-4">
          <textarea
            value={descriptiveAnswer}
            onChange={(e) => onDescriptiveAnswerChange(e.target.value)}
            placeholder="이 내용을 자신의 말로 설명해보세요..."
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 resize-none"
            rows={8}
            maxLength={2000}
            disabled={isSubmitting}
            aria-label="답변 입력"
          />
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {descriptiveAnswer.length}/2000자
            </span>
            <button
              onClick={onSubmitDescriptive}
              disabled={descriptiveAnswer.length < 10 || isSubmitting}
              className="px-6 py-2 bg-primary-600 dark:bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label={isSubmitting ? '평가 중' : '제출하기'}
            >
              {isSubmitting ? '평가 중...' : '제출하기'}
            </button>
          </div>
        </div>
      ) : (
        /* Result View: AI 평가 결과 */
        <div className="space-y-4">
          {/* User Answer */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              내 답변
            </h4>
            <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words">
              {submittedAnswer}
            </p>
          </div>

          {/* AI Evaluation */}
          <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4 border border-primary-200 dark:border-primary-700">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                AI 평가
              </h4>
              <div className="text-xl font-bold text-primary-600 dark:text-primary-400">
                {Math.round(aiEvaluation.score)}점
              </div>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 break-words">
              {aiEvaluation.feedback}
            </p>
          </div>

          {/* Correct Answer */}
          <div className="bg-success-50 dark:bg-success-900/20 rounded-lg p-4 border border-success-200 dark:border-success-700">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              정답
            </h4>
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {review.content.content}
              </ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DescriptiveReviewCard;
