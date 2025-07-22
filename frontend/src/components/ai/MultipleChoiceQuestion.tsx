/**
 * Multiple Choice Question Component
 * Displays AI-generated multiple choice questions in read-only format
 */
import React, { useState } from 'react';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { AIQuestion } from '../../types/ai-review';

interface MultipleChoiceQuestionProps {
  question: AIQuestion;
  showAnswer?: boolean;
  readOnly?: boolean;
}

export const MultipleChoiceQuestion: React.FC<MultipleChoiceQuestionProps> = ({
  question,
  showAnswer = false,
  readOnly = false
}) => {
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(showAnswer);

  const handleOptionSelect = (option: string) => {
    if (readOnly) return;
    setSelectedOption(option);
  };

  const handleShowAnswer = () => {
    setShowExplanation(true);
  };

  const getOptionStyle = (option: string) => {
    const baseStyle = "flex items-center p-3 border rounded-lg transition-all text-left w-full";
    
    if (showExplanation) {
      // Show correct answer when explanation is visible
      const isCorrect = option === question.correct_answer;
      if (isCorrect) {
        return `${baseStyle} border-green-500 bg-green-50 text-green-800`;
      }
      return `${baseStyle} border-gray-300 bg-gray-50 text-gray-600`;
    }

    // Normal state
    if (selectedOption === option && !readOnly) {
      return `${baseStyle} border-blue-500 bg-blue-50 cursor-pointer`;
    }
    
    return `${baseStyle} border-gray-300 ${readOnly ? 'cursor-default' : 'cursor-pointer hover:border-gray-400 hover:bg-gray-50'}`;
  };

  const getOptionIcon = (option: string) => {
    if (showExplanation) {
      const isCorrect = option === question.correct_answer;
      return isCorrect ? '✓' : '○';
    }
    
    if (!readOnly && selectedOption === option) {
      return '●';
    }
    
    return '○';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Question Header */}
      <div className="flex items-center gap-2 mb-4">
        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">
          객관식
        </span>
        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
          {aiReviewAPI.getDifficultyLabel(question.difficulty)}
        </span>
      </div>

      {/* Question Text */}
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        {question.question_text}
      </h3>

      {/* Options */}
      <div className="space-y-3 mb-4">
        {question.options?.map((option, index) => (
          <button
            key={index}
            onClick={() => handleOptionSelect(option)}
            disabled={readOnly}
            className={getOptionStyle(option)}
          >
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center mr-3">
              {getOptionIcon(option)}
            </span>
            <span className="flex-1">{option}</span>
          </button>
        ))}
      </div>

      {/* Show Answer Button */}
      {!showExplanation && !readOnly && (
        <button
          onClick={handleShowAnswer}
          className="w-full py-2 px-4 rounded-md font-medium transition-all bg-green-600 text-white hover:bg-green-700"
        >
          정답 및 해설 보기
        </button>
      )}

      {/* Correct Answer Display */}
      {showExplanation && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-green-900">✅ 정답</span>
          </div>
          
          <p className="text-green-800 text-sm font-medium">
            {question.correct_answer}
          </p>
        </div>
      )}

      {/* Explanation */}
      {showExplanation && question.explanation && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">📝 해설</h4>
          <p className="text-blue-800 text-sm">{question.explanation}</p>
        </div>
      )}

      {/* Keywords */}
      {question.keywords && question.keywords.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium text-gray-900 mb-2 text-sm">🏷️ 키워드</h4>
          <div className="flex flex-wrap gap-1">
            {question.keywords.map((keyword, index) => (
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