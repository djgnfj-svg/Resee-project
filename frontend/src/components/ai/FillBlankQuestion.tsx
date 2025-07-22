/**
 * Fill-in-the-Blank Question Component
 * Interactive fill-in-the-blank exercises with AI-generated blanks
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { FillBlankResponse, FillBlankState } from '../../types/ai-review';
import { Content } from '../../types';

interface FillBlankQuestionProps {
  content: Content;
  numBlanks?: number;
  onCompleted?: (score: number) => void;
}

export const FillBlankQuestion: React.FC<FillBlankQuestionProps> = ({
  content,
  numBlanks = 3,
  onCompleted
}) => {
  const [state, setState] = useState<FillBlankState>({
    blankedText: '',
    answers: {},
    userAnswers: {},
    keywords: [],
    isChecking: false
  });
  const [isLoading, setIsLoading] = useState(true);
  const [showAnswers, setShowAnswers] = useState(false);

  // Generate fill-in-blank exercise
  useEffect(() => {
    const generateFillBlanks = async () => {
      try {
        const response: FillBlankResponse = await aiReviewAPI.generateFillBlanks({
          content_id: content.id,
          num_blanks: numBlanks
        });

        setState({
          blankedText: response.blanked_text,
          answers: response.answers,
          userAnswers: Object.keys(response.answers).reduce((acc, key) => {
            acc[key] = '';
            return acc;
          }, {} as Record<string, string>),
          keywords: response.keywords,
          isChecking: false
        });

        toast.success(`${numBlanks}개의 빈칸이 생성되었습니다! 🧩`);
      } catch (error: any) {
        console.error('Fill-blank generation failed:', error);
        toast.error('빈칸 채우기 생성에 실패했습니다');
      } finally {
        setIsLoading(false);
      }
    };

    generateFillBlanks();
  }, [content.id, numBlanks]);

  const handleInputChange = (blankKey: string, value: string) => {
    setState(prev => ({
      ...prev,
      userAnswers: {
        ...prev.userAnswers,
        [blankKey]: value
      }
    }));
  };

  const checkAnswers = () => {
    const totalBlanks = Object.keys(state.answers).length;
    let correctCount = 0;

    Object.keys(state.answers).forEach(blankKey => {
      const correctAnswer = state.answers[blankKey].toLowerCase().trim();
      const userAnswer = state.userAnswers[blankKey].toLowerCase().trim();
      
      // Simple similarity check - could be enhanced with fuzzy matching
      if (userAnswer === correctAnswer || 
          correctAnswer.includes(userAnswer) ||
          userAnswer.includes(correctAnswer)) {
        correctCount++;
      }
    });

    const score = correctCount / totalBlanks;
    setState(prev => ({ ...prev, score }));
    setShowAnswers(true);
    onCompleted?.(score);

    // Show appropriate feedback
    if (score === 1) {
      toast.success('완벽합니다! 모든 빈칸을 정확히 맞히셨네요! 🎉');
    } else if (score >= 0.8) {
      toast.success(`우수합니다! ${correctCount}/${totalBlanks} 정답 👏`);
    } else if (score >= 0.6) {
      toast.error(`좋습니다! ${correctCount}/${totalBlanks} 정답 📚`);
    } else if (score >= 0.4) {
      toast.error(`조금 더 노력해보세요! ${correctCount}/${totalBlanks} 정답 💪`);
    } else {
      toast.error(`다시 한번 시도해보세요! ${correctCount}/${totalBlanks} 정답 🤔`);
    }
  };

  const handleSubmit = () => {
    // Check if all blanks are filled
    const allFilled = Object.values(state.userAnswers).every(answer => answer.trim() !== '');
    
    if (!allFilled) {
      toast.error('모든 빈칸을 채워주세요');
      return;
    }

    setState(prev => ({ ...prev, isChecking: true }));
    
    // Simulate checking time
    setTimeout(() => {
      checkAnswers();
      setState(prev => ({ ...prev, isChecking: false }));
    }, 1000);
  };

  const resetExercise = () => {
    setState(prev => ({
      ...prev,
      userAnswers: Object.keys(prev.answers).reduce((acc, key) => {
        acc[key] = '';
        return acc;
      }, {} as Record<string, string>),
      score: undefined
    }));
    setShowAnswers(false);
  };

  const getBlankStyle = (blankKey: string) => {
    if (!showAnswers) {
      return "inline-block min-w-24 px-2 py-1 border-b-2 border-blue-500 bg-blue-50 focus:outline-none focus:bg-blue-100 text-center";
    }

    const correctAnswer = state.answers[blankKey].toLowerCase().trim();
    const userAnswer = state.userAnswers[blankKey].toLowerCase().trim();
    const isCorrect = userAnswer === correctAnswer || 
                     correctAnswer.includes(userAnswer) ||
                     userAnswer.includes(correctAnswer);

    return `inline-block min-w-24 px-2 py-1 border-b-2 text-center ${
      isCorrect 
        ? 'border-green-500 bg-green-50 text-green-800'
        : 'border-red-500 bg-red-50 text-red-800'
    }`;
  };

  const renderTextWithBlanks = () => {
    let text = state.blankedText;
    const blankKeys = Object.keys(state.answers).sort();

    blankKeys.forEach(blankKey => {
      const blankPattern = `[${blankKey}]`;
      const input = (
        <input
          key={blankKey}
          type="text"
          value={state.userAnswers[blankKey] || ''}
          onChange={(e) => handleInputChange(blankKey, e.target.value)}
          disabled={showAnswers}
          className={getBlankStyle(blankKey)}
          placeholder="답입력"
        />
      );
      
      // Replace the blank with input field
      const inputHtml = `<span data-blank="${blankKey}"></span>`;
      text = text.replace(blankPattern, inputHtml);
    });

    // Split by blank markers and insert inputs
    const parts = text.split(/(<span data-blank="[^"]+"><\/span>)/);
    
    return parts.map((part, index) => {
      const blankMatch = part.match(/data-blank="([^"]+)"/);
      if (blankMatch) {
        const blankKey = blankMatch[1];
        return (
          <input
            key={blankKey}
            type="text"
            value={state.userAnswers[blankKey] || ''}
            onChange={(e) => handleInputChange(blankKey, e.target.value)}
            disabled={showAnswers}
            className={getBlankStyle(blankKey)}
            placeholder="?"
          />
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mr-3"></div>
          <span className="text-gray-600">AI가 빈칸 채우기 문제를 생성하고 있습니다...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded font-medium">
          빈칸 채우기
        </span>
        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
          {Object.keys(state.answers).length}개 빈칸
        </span>
        {state.score !== undefined && (
          <span className={`px-2 py-1 text-xs rounded font-medium ${aiReviewAPI.getScoreColor(state.score)}`}>
            점수: {Math.round(state.score * 100)}점
          </span>
        )}
      </div>

      {/* Instructions */}
      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-blue-800 text-sm">
          🧩 <strong>빈칸 채우기:</strong> 아래 문장에서 빈칸에 들어갈 적절한 단어나 구문을 입력하세요.
        </p>
      </div>

      {/* Content with Blanks */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="text-gray-900 leading-relaxed">
          {renderTextWithBlanks()}
        </div>
      </div>

      {/* Action Buttons */}
      {!showAnswers ? (
        <button
          onClick={handleSubmit}
          disabled={state.isChecking || Object.values(state.userAnswers).some(answer => !answer.trim())}
          className={`w-full py-2 px-4 rounded-md font-medium transition-all ${
            state.isChecking || Object.values(state.userAnswers).some(answer => !answer.trim())
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-orange-600 text-white hover:bg-orange-700'
          }`}
        >
          {state.isChecking ? (
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              답안 확인 중...
            </div>
          ) : (
            '답안 확인하기'
          )}
        </button>
      ) : (
        <div className="flex gap-2">
          <button
            onClick={resetExercise}
            className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          >
            다시 시도하기
          </button>
          <button
            onClick={() => window.location.reload()}
            className="flex-1 py-2 px-4 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
          >
            새 문제 생성
          </button>
        </div>
      )}

      {/* Answer Key */}
      {showAnswers && (
        <div className="mt-6 p-4 bg-green-50 rounded-lg">
          <h4 className="font-medium text-green-900 mb-3">📖 정답 확인</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {Object.entries(state.answers).map(([blankKey, correctAnswer]) => {
              const userAnswer = state.userAnswers[blankKey];
              const isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim() ||
                               correctAnswer.toLowerCase().includes(userAnswer.toLowerCase().trim()) ||
                               userAnswer.toLowerCase().includes(correctAnswer.toLowerCase().trim());
              
              return (
                <div key={blankKey} className="flex items-center gap-2">
                  <span className="text-sm text-green-700 font-medium">{blankKey}:</span>
                  <span className="text-sm text-green-800">{correctAnswer}</span>
                  {!isCorrect && (
                    <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
                      입력: "{userAnswer}"
                    </span>
                  )}
                  <span className={`text-xs ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                    {isCorrect ? '✓' : '✗'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Keywords */}
      {state.keywords.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium text-gray-900 mb-2 text-sm">🏷️ 관련 키워드</h4>
          <div className="flex flex-wrap gap-1">
            {state.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded"
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