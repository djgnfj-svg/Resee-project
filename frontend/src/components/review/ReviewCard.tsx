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
        <div className="absolute inset-0 w-full bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-2xl shadow-xl dark:shadow-gray-900/40 backface-hidden border-2 border-indigo-200 dark:border-indigo-700" style={{ minHeight: '600px' }}>
          <div className="p-8 h-full flex flex-col justify-center items-center text-center gap-6">
            <div className="mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                {review.content.title}
              </h2>
              <div className="flex items-center justify-center flex-wrap gap-2">
                {review.content.category && (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300">
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                    </svg>
                    {review.content.category.name}
                  </span>
                )}
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {review.initial_review_completed ?
                    `${review.interval_index + 1}번째 복습` :
                    '첫 번째 복습'}
                </span>
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                  {isSubjective ? (
                    <>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                      주관식 평가
                    </>
                  ) : (
                    <>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      기억 확인
                    </>
                  )}
                </span>
              </div>
            </div>

            {isSubjective ? (
              // 주관식: 답변 먼저 작성
              <div className="w-full max-w-2xl flex flex-col">
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-3">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>학습한 내용을 먼저 작성해주세요 (AI가 자동으로 평가합니다)</span>
                </div>
                <textarea
                  value={descriptiveAnswer}
                  onChange={(e) => onDescriptiveAnswerChange(e.target.value)}
                  placeholder="이 내용을 자신의 말로 설명해보세요. 제출하면 정답과 AI 평가를 확인할 수 있습니다."
                  className="w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 resize-none mb-2"
                  rows={6}
                  maxLength={2000}
                  disabled={isSubmitting}
                />
                <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
                  <span>{descriptiveAnswer.length}/2000자</span>
                  <span className={descriptiveAnswer.length >= 10 ? 'text-green-600 dark:text-green-400 font-medium' : ''}>
                    {descriptiveAnswer.length >= 10 ? '✓ 제출 가능' : '(최소 10자)'}
                  </span>
                </div>
                <button
                  onClick={onSubmitSubjective}
                  disabled={descriptiveAnswer.length < 10 || isSubmitting}
                  className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-400 dark:to-purple-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-700 dark:hover:from-indigo-500 dark:hover:to-purple-600 transition-all duration-300 shadow-lg dark:shadow-gray-900/40 disabled:opacity-50 disabled:cursor-not-allowed"
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
                <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-8">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>이 내용을 얼마나 잘 기억하고 있나요?</span>
                </div>

                <button
                  onClick={onFlip}
                  className="bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-400 dark:to-purple-500 text-white px-8 py-4 rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-700 dark:hover:from-indigo-500 dark:hover:to-purple-600 transition-all duration-300 transform hover:scale-105 shadow-lg dark:shadow-gray-900/40"
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
              <div className="flex items-center gap-2 mb-3">
                <div className="p-1.5 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <svg className="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">정답</h4>
              </div>
              <div className="prose prose-base dark:prose-invert max-w-none">
                <ReactMarkdown>
                  {review.content.content}
                </ReactMarkdown>
              </div>
            </div>

            {/* 주관식 평가: AI 평가 결과 */}
            {isSubjective && aiEvaluation && (
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border-2 border-indigo-200 dark:border-indigo-700 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className="p-1.5 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
                    <svg className="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">AI 평가</h4>
                </div>
                <div className="flex items-center space-x-3 mb-3">
                  <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                    {Math.round(aiEvaluation.score)}점
                  </div>
                  <div className="flex-1">
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-400 dark:to-purple-500 transition-all duration-500"
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
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg">
                    <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">내가 작성한 답변</h4>
                </div>
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