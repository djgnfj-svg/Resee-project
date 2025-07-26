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
      
      // Enhanced similarity check with multiple strategies
      const isCorrect = checkAnswerSimilarity(correctAnswer, userAnswer);
      
      if (isCorrect) {
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
      toast.success(`좋습니다! ${correctCount}/${totalBlanks} 정답 📚`);
    } else if (score >= 0.4) {
      toast.error(`조금 더 노력해보세요! ${correctCount}/${totalBlanks} 정답 💪`);
    } else {
      toast.error(`다시 한번 시도해보세요! ${correctCount}/${totalBlanks} 정답 🤔`);
    }
  };

  const checkAnswerSimilarity = (correct: string, user: string): boolean => {
    // Exact match
    if (user === correct) return true;
    
    // Remove common particles/suffixes for Korean
    const cleanCorrect = removeKoreanParticles(correct);
    const cleanUser = removeKoreanParticles(user);
    
    if (cleanUser === cleanCorrect) return true;
    
    // Partial matching (both directions)
    if (correct.length >= 3 && user.length >= 2) {
      if (correct.includes(user) || user.includes(correct)) return true;
    }
    
    // Levenshtein distance for typos (allow 1-2 character differences)
    const distance = levenshteinDistance(correct, user);
    const maxAllowedDistance = Math.max(1, Math.floor(correct.length * 0.2));
    
    return distance <= maxAllowedDistance;
  };

  const removeKoreanParticles = (text: string): string => {
    // Remove common Korean particles and endings
    return text
      .replace(/[은는이가을를에서의도로만]+$/, '') // Remove particles at the end
      .replace(/[하다함기]$/, '') // Remove verb endings
      .replace(/[적인적으로들]$/, '') // Remove adjective endings
      .trim();
  };

  const levenshteinDistance = (a: string, b: string): number => {
    const matrix = Array(b.length + 1).fill(null).map(() => Array(a.length + 1).fill(null));
    
    for (let i = 0; i <= b.length; i++) matrix[i][0] = i;
    for (let j = 0; j <= a.length; j++) matrix[0][j] = j;
    
    for (let i = 1; i <= b.length; i++) {
      for (let j = 1; j <= a.length; j++) {
        if (b.charAt(i - 1) === a.charAt(j - 1)) {
          matrix[i][j] = matrix[i - 1][j - 1];
        } else {
          matrix[i][j] = Math.min(
            matrix[i - 1][j - 1] + 1, // substitution
            matrix[i][j - 1] + 1,     // insertion
            matrix[i - 1][j] + 1      // deletion
          );
        }
      }
    }
    
    return matrix[b.length][a.length];
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
    const isCorrect = checkAnswerSimilarity(correctAnswer, userAnswer);

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
      const inputElement = (
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
          <span className={`px-2 py-1 text-xs rounded font-medium ${
            state.score >= 0.8 ? 'bg-green-100 text-green-700' :
            state.score >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
            'bg-red-100 text-red-700'
          }`}>
            점수: {Math.round(state.score * 100)}점
          </span>
        )}
      </div>

      {/* Instructions */}
      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-blue-800 text-sm">
          🧩 <strong>빈칸 채우기:</strong> 아래 문장에서 빈칸에 들어갈 적절한 단어나 구문을 입력하세요.<br/>
          💡 <strong>채점 방식:</strong> 유사한 답안, 오타, 조사 차이도 정답으로 인정됩니다!
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
              const isCorrect = checkAnswerSimilarity(correctAnswer.toLowerCase().trim(), userAnswer.toLowerCase().trim());
              
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