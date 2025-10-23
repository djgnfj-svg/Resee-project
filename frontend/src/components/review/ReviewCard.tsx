import React from 'react';
import ReactMarkdown from 'react-markdown';
import { ReviewSchedule } from '../../types';

interface ReviewCardProps {
  review: ReviewSchedule;
  isFlipped: boolean;
  showContent: boolean;
  onFlip: () => void;
  descriptiveAnswer: string;
  onDescriptiveAnswerChange: (value: string) => void;
  onSubmitSubjective?: () => void;
  isSubmitting?: boolean;
  submittedAnswer?: string;
  aiEvaluation?: {
    score: number;
    feedback: string;
    auto_result?: string;
  } | null;
}

const ReviewCard: React.FC<ReviewCardProps> = ({
  review,
  isFlipped,
  showContent,
  onFlip,
  descriptiveAnswer,
  onDescriptiveAnswerChange,
  onSubmitSubjective,
  isSubmitting = false,
  submittedAnswer,
  aiEvaluation,
}) => {
  const isSubjective = review.content.review_mode === 'subjective';

  return (
    <div className="relative mb-8" style={{ minHeight: '600px' }}>
      <div className={`w-full transition-transform duration-700 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`} style={{ minHeight: '600px' }}>
        {/* Front of Card */}
        <div className="absolute inset-0 w-full bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden border-2 border-blue-200 dark:border-blue-700" style={{ minHeight: '600px' }}>
          <div className="p-8 h-full flex flex-col justify-center items-center text-center gap-6">
            <div className="mb-6">
              <div className="text-4xl mb-4"></div>
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
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                  {isSubjective ? '주관식 평가' : '기억 확인'}
                </span>
              </div>
            </div>

            {isSubjective ? (
              // 주관식: 답변 먼저 작성
              <div className="w-full max-w-2xl flex flex-col">
                <div className="text-gray-600 dark:text-gray-400 mb-3">
                  학습한 내용을 먼저 작성해주세요 (AI가 자동으로 평가합니다)
                </div>
                <textarea
                  value={descriptiveAnswer}
                  onChange={(e) => onDescriptiveAnswerChange(e.target.value)}
                  placeholder="이 내용을 자신의 말로 설명해보세요. 제출하면 정답과 AI 평가를 확인할 수 있습니다."
                  className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 resize-none mb-2"
                  rows={6}
                  maxLength={2000}
                  disabled={isSubmitting}
                />
                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
                  <span>{descriptiveAnswer.length}/2000자</span>
                  <span>{descriptiveAnswer.length >= 10 ? '✓ 제출 가능' : '(최소 10자)'}</span>
                </div>
                <button
                  onClick={onSubmitSubjective}
                  disabled={descriptiveAnswer.length < 10 || isSubmitting}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 dark:hover:from-blue-500 dark:hover:to-purple-600 transition-all duration-300 shadow-lg dark:shadow-gray-900/40 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      AI 평가 중...
                    </div>
                  ) : (
                    '제출하고 AI 평가 받기'
                  )}
                </button>
              </div>
            ) : (
              // 객관식: 기존 방식
              <>
                <div className="text-gray-600 dark:text-gray-400 mb-8">
                  이 내용을 얼마나 잘 기억하고 있나요?
                </div>

                <button
                  onClick={onFlip}
                  className="bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-700 dark:hover:from-blue-500 dark:hover:to-purple-600 transition-all duration-300 transform hover:scale-105 shadow-lg dark:shadow-gray-900/40"
                >
                  내용 확인하기
                </button>
              </>
            )}
          </div>
        </div>

        {/* Back of Card */}
        <div className="absolute inset-0 w-full bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden rotate-y-180 border-2 border-green-200 dark:border-green-700" style={{ minHeight: '600px' }}>
          <div className="p-8 h-full flex flex-col space-y-4 overflow-y-auto">
            {/* 정답 내용 - 최우선 배치 */}
            <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">정답</h4>
              <div className="prose prose-base dark:prose-invert max-w-none">
                <ReactMarkdown>
                  {review.content.content}
                </ReactMarkdown>
              </div>
            </div>

            {/* 주관식 평가: AI 평가 결과 */}
            {isSubjective && aiEvaluation && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-blue-200 dark:border-blue-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">AI 평가</h4>
                <div className="flex items-center space-x-3 mb-3">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {Math.round(aiEvaluation.score)}점
                  </div>
                  <div className="flex-1">
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 transition-all duration-500"
                        style={{ width: `${aiEvaluation.score}%` }}
                      />
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {aiEvaluation.feedback}
                </p>
              </div>
            )}

            {/* 주관식 평가: 제출한 답변 표시 */}
            {isSubjective && submittedAnswer && (
              <div className="bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">내가 작성한 답변</h4>
                <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{submittedAnswer}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReviewCard;