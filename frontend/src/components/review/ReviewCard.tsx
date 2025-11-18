import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ReviewSchedule } from '../../types';

interface ReviewCardProps {
  review: ReviewSchedule;
  isFlipped: boolean;
  showContent: boolean;
  onFlip: () => void;
  // Descriptive mode (제목 → 내용 작성)
  descriptiveAnswer: string;
  onDescriptiveAnswerChange: (value: string) => void;
  onSubmitDescriptive?: () => void;
  // Multiple choice mode (내용 → 제목 선택)
  selectedChoice?: string;
  onSelectChoice?: (choice: string) => void;
  onSubmitMultipleChoice?: () => void;
  // Subjective mode (내용 → 제목 작성)
  userTitle?: string;
  onUserTitleChange?: (value: string) => void;
  onSubmitSubjective?: () => void;
  // Common
  isSubmitting?: boolean;
  submittedAnswer?: string;
  aiEvaluation?: {
    score: number;
    feedback: string;
    auto_result?: string;
    is_correct?: boolean;
  } | null;
}

const ReviewCard: React.FC<ReviewCardProps> = ({
  review,
  isFlipped,
  showContent,
  onFlip,
  descriptiveAnswer,
  onDescriptiveAnswerChange,
  onSubmitDescriptive,
  selectedChoice,
  onSelectChoice,
  onSubmitMultipleChoice,
  userTitle,
  onUserTitleChange,
  onSubmitSubjective,
  isSubmitting = false,
  submittedAnswer,
  aiEvaluation,
}) => {
  const reviewMode = review.content.review_mode;
  const isDescriptive = reviewMode === 'descriptive';
  const isMultipleChoice = reviewMode === 'multiple_choice';
  const isSubjective = reviewMode === 'subjective';
  const isObjective = reviewMode === 'objective';

  // Mode 1: Objective (기억 확인)
  if (isObjective) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 break-words">
            {review.content.title}
          </h2>
          <div className="flex items-center gap-2">
            {review.content.category && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                {review.content.category.name}
              </span>
            )}
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
              {review.initial_review_completed ? `${review.interval_index + 1}번째 복습` : '첫 복습'}
            </span>
          </div>
        </div>

        {!showContent ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-gray-600 dark:text-gray-400 mb-6">이 내용을 기억하시나요?</p>
            <button
              onClick={onFlip}
              className="px-8 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
            >
              내용 확인하기
            </button>
          </div>
        ) : (
          <div className="prose dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.content.content}</ReactMarkdown>
          </div>
        )}
      </div>
    );
  }

  // Mode 2: Descriptive (제목 → 내용 작성)
  if (isDescriptive) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 break-words">
            {review.content.title}
          </h2>
          <div className="flex items-center gap-2">
            {review.content.category && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                {review.content.category.name}
              </span>
            )}
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
              서술형
            </span>
          </div>
        </div>

        {!aiEvaluation ? (
          /* Answer Input */
          <div className="space-y-4">
            <textarea
              value={descriptiveAnswer}
              onChange={(e) => onDescriptiveAnswerChange(e.target.value)}
              placeholder="이 내용을 자신의 말로 설명해보세요..."
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 resize-none"
              rows={8}
              maxLength={2000}
              disabled={isSubmitting}
            />
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">{descriptiveAnswer.length}/2000자</span>
              <button
                onClick={onSubmitDescriptive}
                disabled={descriptiveAnswer.length < 10 || isSubmitting}
                className="px-6 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? '평가 중...' : '제출하기'}
              </button>
            </div>
          </div>
        ) : (
          /* Result View */
          <div className="space-y-4">
            {/* User Answer */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">내 답변</h4>
              <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words">{submittedAnswer}</p>
            </div>

            {/* AI Evaluation */}
            <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-700">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">AI 평가</h4>
                <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                  {Math.round(aiEvaluation.score)}점
                </div>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 break-words">{aiEvaluation.feedback}</p>
            </div>

            {/* Correct Answer */}
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-700">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">정답</h4>
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.content.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Mode 3: Multiple Choice (내용 → 제목 선택)
  if (isMultipleChoice) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">객관식</h3>
          </div>
          <div className="flex items-center gap-2">
            {review.content.category && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                {review.content.category.name}
              </span>
            )}
          </div>
        </div>

        {!aiEvaluation ? (
          <div className="space-y-6">
            {/* Content */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.content.content}</ReactMarkdown>
              </div>
            </div>

            {/* Choices */}
            {review.content.mc_choices?.choices && (
              <div className="space-y-3">
                {review.content.mc_choices.choices.map((choice, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSelectChoice?.(choice)}
                    disabled={isSubmitting}
                    className={`w-full text-left px-4 py-3 rounded-lg border-2 transition-all break-words ${
                      selectedChoice === choice
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 text-gray-900 dark:text-gray-100'
                        : 'border-gray-200 dark:border-gray-600 hover:border-indigo-300 dark:hover:border-indigo-600 text-gray-700 dark:text-gray-300'
                    } disabled:opacity-50`}
                  >
                    <span className="font-medium mr-2">{idx + 1}.</span>
                    {choice}
                  </button>
                ))}
              </div>
            )}

            <button
              onClick={onSubmitMultipleChoice}
              disabled={!selectedChoice || isSubmitting}
              className="w-full px-6 py-3 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? '제출 중...' : '제출하기'}
            </button>
          </div>
        ) : (
          /* Result View */
          <div className="space-y-4">
            {/* Content */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">내용</h4>
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.content.content}</ReactMarkdown>
              </div>
            </div>

            {/* User Answer */}
            <div className={`rounded-lg p-4 border-2 ${
              aiEvaluation.is_correct
                ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700'
                : 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-700'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">내 선택</h4>
                <span className={`text-sm font-bold ${
                  aiEvaluation.is_correct
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}>
                  {aiEvaluation.is_correct ? '✓ 정답' : '✗ 오답'}
                </span>
              </div>
              <p className="text-gray-800 dark:text-gray-200 font-medium break-words">{selectedChoice}</p>
            </div>

            {/* Correct Answer */}
            {!aiEvaluation.is_correct && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-700">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">정답</h4>
                <p className="text-green-700 dark:text-green-300 font-medium break-words">{review.content.title}</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Mode 4: Subjective (내용 → 제목 작성)
  if (isSubjective) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">주관식</h3>
          </div>
          <div className="flex items-center gap-2">
            {review.content.category && (
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                {review.content.category.name}
              </span>
            )}
          </div>
        </div>

        {!aiEvaluation ? (
          <div className="space-y-6">
            {/* Content */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.content.content}</ReactMarkdown>
              </div>
            </div>

            {/* Title Input */}
            <div className="space-y-2">
              <input
                type="text"
                value={userTitle || ''}
                onChange={(e) => onUserTitleChange?.(e.target.value)}
                placeholder="이 내용에 맞는 제목을 작성해주세요"
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                maxLength={100}
                disabled={isSubmitting}
              />
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">{(userTitle || '').length}/100자</span>
                <button
                  onClick={onSubmitSubjective}
                  disabled={(userTitle || '').length < 2 || isSubmitting}
                  className="px-6 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg font-medium hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? '평가 중...' : '제출하기'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Result View */
          <div className="space-y-4">
            {/* Content */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">내용</h4>
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{review.content.content}</ReactMarkdown>
              </div>
            </div>

            {/* User Answer */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">내가 작성한 제목</h4>
              <p className="text-gray-800 dark:text-gray-200 font-medium break-words">{userTitle}</p>
            </div>

            {/* AI Evaluation */}
            <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-700">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">AI 평가</h4>
                <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
                  {Math.round(aiEvaluation.score)}점
                </div>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 break-words">{aiEvaluation.feedback}</p>
            </div>

            {/* Correct Answer */}
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-700">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">정답</h4>
              <p className="text-green-700 dark:text-green-300 font-medium break-words">{review.content.title}</p>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
};

export default ReviewCard;
