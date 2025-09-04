import React from 'react';
import ReactMarkdown from 'react-markdown';
import { ReviewSchedule } from '../../types';
import { ExplanationEvaluationResponse } from '../../types/ai-review';

interface ExplanationModeProps {
  review: ReviewSchedule;
  userExplanation: string;
  setUserExplanation: (value: string) => void;
  isEvaluating: boolean;
  showEvaluation: boolean;
  evaluationResult: ExplanationEvaluationResponse | null;
  onSubmitExplanation: () => void;
  onReviewComplete: (result: 'remembered' | 'partial' | 'forgot') => void;
  isPending: boolean;
}

const ExplanationMode: React.FC<ExplanationModeProps> = ({
  review,
  userExplanation,
  setUserExplanation,
  isEvaluating,
  showEvaluation,
  evaluationResult,
  onSubmitExplanation,
  onReviewComplete,
  isPending,
}) => {
  return (
    <div className="space-y-6">
      {/* Content Display */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6">
        <div className="text-center mb-6">
          <div className="text-4xl mb-4">📝</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            {review.content.title}
          </h2>
          <div className="flex items-center justify-center space-x-4 text-sm mb-4">
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
        
        <div className="text-center">
          <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
            📝 "{review.content.title}" 에 대해 설명해보세요
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            기억나는 내용을 자신의 말로 설명한 후, AI가 평가하고 원본 내용과 비교해드립니다
          </p>
        </div>
      </div>

      {/* Explanation Input */}
      {!showEvaluation && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6">
          <div className="space-y-4">
            <label htmlFor="explanation" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              여러분의 설명을 작성해주세요 (최소 10자)
            </label>
            <textarea
              id="explanation"
              rows={6}
              value={userExplanation}
              onChange={(e) => setUserExplanation(e.target.value)}
              placeholder="이 내용에 대해 자신의 말로 설명해보세요..."
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-400 dark:focus:ring-primary-400 placeholder-gray-400 dark:placeholder-gray-500"
              disabled={isEvaluating}
            />
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {userExplanation.length}/2000 글자
              </span>
              <button
                onClick={onSubmitExplanation}
                disabled={isEvaluating || userExplanation.trim().length < 10}
                className="bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 text-white px-6 py-2 rounded-lg font-semibold hover:from-blue-600 hover:to-purple-700 dark:hover:from-blue-500 dark:hover:to-purple-600 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isEvaluating ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>AI 평가 중...</span>
                  </div>
                ) : (
                  'AI 평가 받기'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evaluation Result */}
      {showEvaluation && evaluationResult && (
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700 p-6">
          <div className="text-center mb-6">
            <div className="text-4xl mb-2">
              {evaluationResult.score >= 80 ? '🎉' : evaluationResult.score >= 60 ? '👍' : '💪'}
            </div>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-2">
              {evaluationResult.score}점
            </div>
            <div className={`text-lg font-medium ${
              evaluationResult.score >= 80 ? 'text-green-600 dark:text-green-400' :
              evaluationResult.score >= 60 ? 'text-blue-600 dark:text-blue-400' :
              'text-orange-600 dark:text-orange-400'
            }`}>
              {evaluationResult.score >= 80 ? '우수' : evaluationResult.score >= 60 ? '양호' : '노력 필요'}
            </div>
          </div>

          <div className="space-y-4">
            {/* Content Quality Assessment */}
            {evaluationResult.content_quality_assessment && (
              <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                <h3 className="font-medium text-purple-900 dark:text-purple-300 mb-2">📊 원본 내용 분석</h3>
                <div className="text-sm text-purple-800 dark:text-purple-200">
                  <p className="mb-2">
                    <span className="font-medium">품질 수준:</span> {
                      evaluationResult.content_quality_assessment.quality_level === 'excellent' ? '우수' :
                      evaluationResult.content_quality_assessment.quality_level === 'good' ? '양호' :
                      evaluationResult.content_quality_assessment.quality_level === 'average' ? '보통' : '개선 필요'
                    }
                    <span className="ml-2 text-xs">
                      (평가 기준: {
                        evaluationResult.evaluation_approach === 'strict' ? '엄격' :
                        evaluationResult.evaluation_approach === 'standard' ? '표준' : '관대'
                      })
                    </span>
                  </p>
                  {evaluationResult.adaptation_note && (
                    <p className="text-xs text-purple-600 dark:text-purple-400 italic">
                      {evaluationResult.adaptation_note}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Feedback */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">💬 AI 피드백</h3>
              <p className="text-blue-800 dark:text-blue-200">{evaluationResult.feedback}</p>
            </div>

            {/* Bonus Points */}
            {evaluationResult.bonus_points && evaluationResult.bonus_points.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                <h3 className="font-medium text-yellow-900 dark:text-yellow-300 mb-2">⭐ 가산점 항목</h3>
                <ul className="list-disc list-inside text-yellow-800 dark:text-yellow-200 space-y-1">
                  {evaluationResult.bonus_points.map((bonus: string, index: number) => (
                    <li key={index}>{bonus}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Strengths */}
            {evaluationResult.strengths && evaluationResult.strengths.length > 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                <h3 className="font-medium text-green-900 dark:text-green-300 mb-2">✅ 잘한 점</h3>
                <ul className="list-disc list-inside text-green-800 dark:text-green-200 space-y-1">
                  {evaluationResult.strengths.map((strength: string, index: number) => (
                    <li key={index}>{strength}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Improvements */}
            {evaluationResult.improvements && evaluationResult.improvements.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
                <h3 className="font-medium text-yellow-900 dark:text-yellow-300 mb-2">🔧 개선 점</h3>
                <ul className="list-disc list-inside text-yellow-800 dark:text-yellow-200 space-y-1">
                  {evaluationResult.improvements.map((improvement: string, index: number) => (
                    <li key={index}>{improvement}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Key Concepts */}
            <div className="grid md:grid-cols-2 gap-4">
              {evaluationResult.key_concepts_covered && evaluationResult.key_concepts_covered.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 dark:text-gray-300 mb-2">📚 다룬 개념</h3>
                  <div className="flex flex-wrap gap-2">
                    {evaluationResult.key_concepts_covered.map((concept: string, index: number) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {evaluationResult.missing_concepts && evaluationResult.missing_concepts.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 dark:text-gray-300 mb-2">❓ 놓친 개념</h3>
                  <div className="flex flex-wrap gap-2">
                    {evaluationResult.missing_concepts.map((concept: string, index: number) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                        {concept}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Original Content Comparison */}
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600">
              <h3 className="font-medium text-gray-900 dark:text-gray-300 mb-4 text-center">
                📖 원본 내용과 비교해보세요
              </h3>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown>{review.content.content}</ReactMarkdown>
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
                💡 이제 원본 내용과 여러분이 작성한 설명을 비교해보세요
              </div>
            </div>
          </div>

          {/* Review Actions */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-600">
            <p className="text-center text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
              이 복습을 어떻게 평가하시겠어요?
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => onReviewComplete('forgot')}
                disabled={isPending}
                className="group p-4 border-2 border-red-200 dark:border-red-700 rounded-xl text-center hover:border-red-300 dark:hover:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50 transition-all duration-300 bg-white dark:bg-gray-800"
              >
                <div className="text-2xl mb-2">😔</div>
                <div className="text-red-600 dark:text-red-400 font-semibold">더 연습 필요</div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">다시 처음부터</div>
              </button>
              
              <button
                onClick={() => onReviewComplete('partial')}
                disabled={isPending}
                className="group p-4 border-2 border-yellow-200 dark:border-yellow-700 rounded-xl text-center hover:border-yellow-300 dark:hover:border-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20 disabled:opacity-50 transition-all duration-300 bg-white dark:bg-gray-800"
              >
                <div className="text-2xl mb-2">🤔</div>
                <div className="text-yellow-600 dark:text-yellow-400 font-semibold">부분적 이해</div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">같은 간격으로</div>
              </button>
              
              <button
                onClick={() => onReviewComplete('remembered')}
                disabled={isPending}
                className="group p-4 border-2 border-green-200 dark:border-green-700 rounded-xl text-center hover:border-green-300 dark:hover:border-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50 transition-all duration-300 bg-white dark:bg-gray-800"
              >
                <div className="text-2xl mb-2">😊</div>
                <div className="text-green-600 dark:text-green-400 font-semibold">잘 이해함</div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">다음 단계로</div>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplanationMode;