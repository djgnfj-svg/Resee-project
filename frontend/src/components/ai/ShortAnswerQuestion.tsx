/**
 * Short Answer Question Component
 * Displays AI-generated short answer questions with semantic evaluation
 */
import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { AIQuestion, AnswerEvaluationResult } from '../../types/ai-review';

interface ShortAnswerQuestionProps {
  question: AIQuestion;
  onAnswerEvaluated?: (evaluation: AnswerEvaluationResult) => void;
  showAnswer?: boolean;
}

export const ShortAnswerQuestion: React.FC<ShortAnswerQuestionProps> = ({
  question,
  onAnswerEvaluated,
  showAnswer = false
}) => {
  const [userAnswer, setUserAnswer] = useState('');
  const [evaluation, setEvaluation] = useState<AnswerEvaluationResult | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [showExplanation, setShowExplanation] = useState(showAnswer);

  const handleSubmit = async () => {
    if (!userAnswer.trim()) {
      toast.error('답안을 입력해주세요');
      return;
    }

    setIsEvaluating(true);

    try {
      const result = await aiReviewAPI.evaluateAnswer({
        question_id: question.id,
        user_answer: userAnswer.trim()
      });

      setEvaluation(result);
      setShowExplanation(true);
      onAnswerEvaluated?.(result);

      // Show appropriate feedback
      if (result.score >= 0.9) {
        toast.success('훌륭한 답변입니다! 🌟');
      } else if (result.score >= 0.7) {
        toast.success('좋은 답변입니다! 👍');
      } else if (result.score >= 0.5) {
        toast.error('부분적으로 맞습니다. AI 피드백을 확인해보세요 📝');
      } else {
        toast.error('답변을 다시 검토해보세요. 자세한 피드백을 확인하세요 💡');
      }
    } catch (error: any) {
      console.error('Answer evaluation failed:', error);
      toast.error('답안 평가에 실패했습니다');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Question Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded font-medium">
          주관식
        </span>
        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
          {aiReviewAPI.getDifficultyLabel(question.difficulty)}
        </span>
        {evaluation && (
          <span className={`px-2 py-1 text-xs rounded font-medium ${aiReviewAPI.getScoreColor(evaluation.score)} bg-opacity-10`}>
            점수: {Math.round(evaluation.score * 100)}점
          </span>
        )}
      </div>

      {/* Question Text */}
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        {question.question_text}
      </h3>

      {/* Answer Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          답변을 입력하세요
        </label>
        <textarea
          value={userAnswer}
          onChange={(e) => setUserAnswer(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={evaluation !== null}
          placeholder="여기에 자유롭게 답변을 작성해주세요..."
          rows={4}
          className={`w-full p-3 border rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none ${
            evaluation ? 'bg-gray-50' : ''
          }`}
        />
        <p className="text-xs text-gray-500 mt-1">
          Ctrl + Enter로 제출할 수 있습니다
        </p>
      </div>

      {/* Submit Button */}
      {!evaluation && (
        <button
          onClick={handleSubmit}
          disabled={!userAnswer.trim() || isEvaluating}
          className={`w-full py-2 px-4 rounded-md font-medium transition-all ${
            !userAnswer.trim() || isEvaluating
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          {isEvaluating ? (
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              AI가 의미론적 분석 중입니다...
            </div>
          ) : (
            '답안 제출하기'
          )}
        </button>
      )}

      {/* User's Answer Display */}
      {evaluation && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">📝 제출한 답안</h4>
          <p className="text-gray-700 text-sm whitespace-pre-wrap">{userAnswer}</p>
        </div>
      )}

      {/* Evaluation Results */}
      {evaluation && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-blue-900">🤖 AI 의미론적 평가</span>
            <span className={`px-2 py-1 text-xs rounded font-medium ${aiReviewAPI.getScoreColor(evaluation.score)}`}>
              {aiReviewAPI.getScoreLabel(evaluation.score)}
            </span>
            {evaluation.similarity_score && (
              <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                유사도: {Math.round(evaluation.similarity_score * 100)}%
              </span>
            )}
          </div>
          
          <p className="text-blue-800 text-sm mb-3">
            {evaluation.feedback}
          </p>

          {evaluation.evaluation_details && (
            <div className="space-y-3">
              {evaluation.evaluation_details.strengths.length > 0 && (
                <div className="p-3 bg-green-50 rounded border-l-4 border-green-400">
                  <span className="text-green-700 font-medium text-sm flex items-center gap-1">
                    ✅ 잘한 점
                  </span>
                  <ul className="text-sm text-green-600 mt-1 ml-2">
                    {evaluation.evaluation_details.strengths.map((strength, idx) => (
                      <li key={idx}>• {strength}</li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.evaluation_details.weaknesses.length > 0 && (
                <div className="p-3 bg-orange-50 rounded border-l-4 border-orange-400">
                  <span className="text-orange-700 font-medium text-sm flex items-center gap-1">
                    ⚠️ 개선할 점
                  </span>
                  <ul className="text-sm text-orange-600 mt-1 ml-2">
                    {evaluation.evaluation_details.weaknesses.map((weakness, idx) => (
                      <li key={idx}>• {weakness}</li>
                    ))}
                  </ul>
                </div>
              )}

              {evaluation.evaluation_details.suggestions.length > 0 && (
                <div className="p-3 bg-purple-50 rounded border-l-4 border-purple-400">
                  <span className="text-purple-700 font-medium text-sm flex items-center gap-1">
                    💡 학습 제안
                  </span>
                  <ul className="text-sm text-purple-600 mt-1 ml-2">
                    {evaluation.evaluation_details.suggestions.map((suggestion, idx) => (
                      <li key={idx}>• {suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {evaluation.processing_time_ms && (
            <p className="text-xs text-blue-600 mt-2">
              AI 처리 시간: {evaluation.processing_time_ms}ms
            </p>
          )}
        </div>
      )}

      {/* Model Answer */}
      {showExplanation && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg">
          <h4 className="font-medium text-green-900 mb-2">📖 모범 답안</h4>
          <p className="text-green-800 text-sm whitespace-pre-wrap">{question.correct_answer}</p>
        </div>
      )}

      {/* Explanation */}
      {showExplanation && question.explanation && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
          <h4 className="font-medium text-yellow-900 mb-2">💭 해설</h4>
          <p className="text-yellow-800 text-sm">{question.explanation}</p>
        </div>
      )}

      {/* Keywords */}
      {question.keywords && question.keywords.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium text-gray-900 mb-2 text-sm">🏷️ 핵심 키워드</h4>
          <div className="flex flex-wrap gap-1">
            {question.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};