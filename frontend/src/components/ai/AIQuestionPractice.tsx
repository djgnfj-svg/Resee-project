/**
 * AI Question Practice Component
 * 생성된 AI 질문을 풀고 답변을 AI로 평가받는 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { 
  AIQuestion, 
  AIAnswerEvaluationResponse 
} from '../../types/ai-review';

interface AIQuestionPracticeProps {
  question: AIQuestion;
  onComplete?: (evaluation: AIAnswerEvaluationResponse) => void;
}

export const AIQuestionPractice: React.FC<AIQuestionPracticeProps> = ({
  question,
  onComplete
}) => {
  const [userAnswer, setUserAnswer] = useState<string>('');
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState<AIAnswerEvaluationResponse | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);

  // Reset state when question changes
  useEffect(() => {
    setUserAnswer('');
    setSelectedOption('');
    setEvaluation(null);
    setShowAnswer(false);
  }, [question.id]);

  const handleSubmitAnswer = async () => {
    const finalAnswer = question.question_type_display === 'Multiple Choice' 
      ? selectedOption 
      : userAnswer;

    if (!finalAnswer.trim()) {
      toast.error('답변을 입력해주세요.');
      return;
    }

    setIsEvaluating(true);

    try {
      const evaluationResult = await aiReviewAPI.evaluateAnswer({
        question_id: question.id,
        user_answer: finalAnswer
      });

      setEvaluation(evaluationResult);
      setShowAnswer(true);
      onComplete?.(evaluationResult);

      // Show feedback toast based on score
      const scoreLabel = aiReviewAPI.getScoreLabel(evaluationResult.score);
      toast.success(`평가 완료! 점수: ${Math.round(evaluationResult.score * 100)}점 (${scoreLabel})`, {
        duration: 4000
      });

    } catch (error: any) {
      console.error('Answer evaluation failed:', error);
      const errorMessage = error.response?.data?.error || 'AI 평가에 실패했습니다.';
      toast.error(errorMessage);
    } finally {
      setIsEvaluating(false);
    }
  };

  const renderQuestionInterface = () => {
    if (question.question_type_display === 'Multiple Choice' && question.options) {
      return (
        <div className="space-y-3">
          {question.options.map((option, index) => (
            <label
              key={index}
              className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                selectedOption === option
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="radio"
                name="option"
                value={option}
                checked={selectedOption === option}
                onChange={(e) => setSelectedOption(e.target.value)}
                className="sr-only"
              />
              <div className={`w-4 h-4 rounded-full border-2 mr-3 flex items-center justify-center ${
                selectedOption === option
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-400'
              }`}>
                {selectedOption === option && (
                  <div className="w-2 h-2 rounded-full bg-white"></div>
                )}
              </div>
              <span className="text-sm text-gray-900">{option}</span>
            </label>
          ))}
        </div>
      );
    } else {
      // Short answer or essay type questions
      return (
        <div>
          <textarea
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            placeholder="답변을 자유롭게 작성해주세요..."
            className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-vertical"
            disabled={isEvaluating || showAnswer}
          />
          <div className="mt-2 text-xs text-gray-500">
            💡 구체적이고 명확한 답변일수록 더 정확한 AI 평가를 받을 수 있습니다.
          </div>
        </div>
      );
    }
  };

  const getScoreDisplay = (score: number) => {
    const percentage = Math.round(score * 100);
    const label = aiReviewAPI.getScoreLabel(score);
    const color = aiReviewAPI.getScoreColor(score);
    
    const colorClasses = {
      green: 'text-green-700 bg-green-100',
      blue: 'text-blue-700 bg-blue-100',
      yellow: 'text-yellow-700 bg-yellow-100',
      orange: 'text-orange-700 bg-orange-100',
      red: 'text-red-700 bg-red-100'
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${colorClasses[color as keyof typeof colorClasses]}`}>
        {percentage}점 ({label})
      </span>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Question Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-purple-100 rounded-lg">
            🧠
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">AI 문제 풀이</h3>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                {aiReviewAPI.getQuestionTypeLabel(question.question_type_display.toLowerCase().replace(' ', '_'))}
              </span>
              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                {aiReviewAPI.getDifficultyLabel(question.difficulty)}
              </span>
            </div>
          </div>
        </div>

        {evaluation && (
          <div className="text-right">
            {getScoreDisplay(evaluation.score)}
          </div>
        )}
      </div>

      {/* Question Text */}
      <div className="mb-6">
        <div className="text-lg text-gray-900 mb-4 leading-relaxed">
          {question.question_text}
        </div>
        
        {question.keywords && question.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            <span className="text-xs text-gray-500 mr-2">키워드:</span>
            {question.keywords.map((keyword, index) => (
              <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                {keyword}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Answer Interface */}
      {!showAnswer && (
        <div className="mb-6">
          {renderQuestionInterface()}
        </div>
      )}

      {/* Submit Button */}
      {!showAnswer && (
        <button
          onClick={handleSubmitAnswer}
          disabled={isEvaluating || (!userAnswer.trim() && !selectedOption)}
          className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
            isEvaluating || (!userAnswer.trim() && !selectedOption)
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-purple-600 text-white hover:bg-purple-700'
          }`}
        >
          {isEvaluating ? (
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              AI가 답변을 평가하고 있습니다...
            </div>
          ) : (
            '🤖 AI 평가 받기'
          )}
        </button>
      )}

      {/* Evaluation Results */}
      {evaluation && showAnswer && (
        <div className="mt-6 space-y-4">
          {/* User's Answer */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">내 답변</h4>
            <p className="text-gray-700">{evaluation.user_answer}</p>
          </div>

          {/* Correct Answer */}
          <div className="p-4 bg-green-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">정답</h4>
            <p className="text-gray-700">{question.correct_answer}</p>
            {question.explanation && (
              <div className="mt-2 text-sm text-gray-600">
                <strong>설명:</strong> {question.explanation}
              </div>
            )}
          </div>

          {/* AI Feedback */}
          <div className="p-4 bg-blue-50 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">🤖 AI 피드백</h4>
            <p className="text-gray-700 mb-3">{evaluation.feedback}</p>
            
            {evaluation.evaluation_details && (
              <div className="space-y-2 text-sm">
                {evaluation.evaluation_details.strengths.length > 0 && (
                  <div>
                    <span className="font-medium text-green-700">✅ 잘한 점:</span>
                    <ul className="list-disc list-inside ml-4 text-gray-600">
                      {evaluation.evaluation_details.strengths.map((strength, index) => (
                        <li key={index}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {evaluation.evaluation_details.weaknesses.length > 0 && (
                  <div>
                    <span className="font-medium text-orange-700">⚠️ 부족한 점:</span>
                    <ul className="list-disc list-inside ml-4 text-gray-600">
                      {evaluation.evaluation_details.weaknesses.map((weakness, index) => (
                        <li key={index}>{weakness}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {evaluation.evaluation_details.suggestions.length > 0 && (
                  <div>
                    <span className="font-medium text-blue-700">💡 개선 제안:</span>
                    <ul className="list-disc list-inside ml-4 text-gray-600">
                      {evaluation.evaluation_details.suggestions.map((suggestion, index) => (
                        <li key={index}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {evaluation.similarity_score !== undefined && (
              <div className="mt-3 text-xs text-gray-500">
                의미적 유사도: {Math.round(evaluation.similarity_score * 100)}%
              </div>
            )}
          </div>

          {/* Processing Time */}
          {evaluation.processing_time_ms && (
            <div className="text-xs text-gray-400 text-center">
              AI 처리 시간: {evaluation.processing_time_ms}ms
            </div>
          )}
        </div>
      )}
    </div>
  );
};