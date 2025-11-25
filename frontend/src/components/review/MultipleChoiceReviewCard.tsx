import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { MultipleChoiceReviewProps } from './types';

/**
 * Multiple Choice Review Mode: 객관식 (내용 → 제목 선택)
 * 사용자가 내용을 보고 올바른 제목을 선택하는 모드
 */
const MultipleChoiceReviewCard: React.FC<MultipleChoiceReviewProps> = ({
  review,
  selectedChoice,
  onSelectChoice,
  onSubmitMultipleChoice,
  isSubmitting = false,
  aiEvaluation,
}) => {
  const hasEvaluation = !!aiEvaluation;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center flex-shrink-0" aria-hidden="true">
            <svg className="w-5 h-5 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            객관식
          </h3>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {review.content.category && (
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300">
              {review.content.category.name}
            </span>
          )}
        </div>
      </div>

      {!hasEvaluation ? (
        /* Question View */
        <div className="space-y-6">
          {/* Content Display */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {review.content.content}
              </ReactMarkdown>
            </div>
          </div>

          {/* Multiple Choice Options */}
          {review.content.mc_choices?.choices && (
            <div className="space-y-3" role="radiogroup" aria-label="객관식 선택지">
              {review.content.mc_choices.choices.map((choice, idx) => {
                const isSelected = selectedChoice === choice;
                return (
                  <button
                    key={idx}
                    onClick={() => onSelectChoice(choice)}
                    disabled={isSubmitting}
                    role="radio"
                    aria-checked={isSelected}
                    aria-label={`선택지 ${idx + 1}: ${choice}`}
                    className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all break-words ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-gray-900 dark:text-gray-100'
                        : 'border-gray-200 dark:border-gray-600 hover:border-primary-300 dark:hover:border-primary-600 text-gray-700 dark:text-gray-300'
                    } disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2`}
                  >
                    <span className="font-medium mr-2">{idx + 1}.</span>
                    {choice}
                  </button>
                );
              })}
            </div>
          )}

          {/* Submit Button */}
          <button
            onClick={onSubmitMultipleChoice}
            disabled={!selectedChoice || isSubmitting}
            className="w-full px-6 py-3 bg-primary-600 dark:bg-primary-500 text-white rounded-lg font-medium hover:bg-primary-700 dark:hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            aria-label={isSubmitting ? '제출 중' : '선택한 답 제출하기'}
          >
            {isSubmitting ? '제출 중...' : '제출하기'}
          </button>
        </div>
      ) : (
        /* Result View */
        <div className="space-y-4">
          {/* Content Display */}
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              내용
            </h4>
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {review.content.content}
              </ReactMarkdown>
            </div>
          </div>

          {/* User's Selected Answer */}
          <div
            className={`rounded-lg p-4 border-2 ${
              aiEvaluation.is_correct
                ? 'bg-success-50 dark:bg-success-900/20 border-success-300 dark:border-success-700'
                : 'bg-error-50 dark:bg-error-900/20 border-error-300 dark:border-error-700'
            }`}
            role="status"
            aria-live="polite"
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                내 선택
              </h4>
              <span
                className={`text-sm font-bold ${
                  aiEvaluation.is_correct
                    ? 'text-success-600 dark:text-success-400'
                    : 'text-error-600 dark:text-error-400'
                }`}
              >
                {aiEvaluation.is_correct ? '✓ 정답' : '✗ 오답'}
              </span>
            </div>
            <p className="text-gray-800 dark:text-gray-200 font-medium break-words">
              {selectedChoice}
            </p>
          </div>

          {/* Correct Answer (if wrong) */}
          {!aiEvaluation.is_correct && (
            <div className="bg-success-50 dark:bg-success-900/20 rounded-lg p-4 border border-success-200 dark:border-success-700">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                정답
              </h4>
              <p className="text-success-700 dark:text-success-300 font-medium break-words">
                {review.content.title}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MultipleChoiceReviewCard;
