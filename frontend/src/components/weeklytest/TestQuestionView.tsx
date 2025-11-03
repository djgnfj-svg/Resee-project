import React from 'react';
import { WeeklyTest } from '../../utils/api/weeklyTest';
import { renderTextWithCode } from '../../utils/textFormatters';

interface TestQuestionViewProps {
  test: WeeklyTest;
  currentQuestionIndex: number;
  answers: Record<number, string>;
  error: string;
  isLoading: boolean;
  onAnswerSelect: (questionId: number, answer: string) => void;
  onPrevious: () => void;
  onNext: () => void;
  onComplete: () => void;
}

const TestQuestionView: React.FC<TestQuestionViewProps> = ({
  test,
  currentQuestionIndex,
  answers,
  error,
  isLoading,
  onAnswerSelect,
  onPrevious,
  onNext,
  onComplete,
}) => {
  if (!test.questions || test.questions.length === 0) return null;

  const currentQuestion = test.questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === test.questions.length - 1;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {test.title}
              </h1>
              <div className="text-right">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {currentQuestionIndex + 1} / {test.questions.length}
                </div>
                <div className="text-xs mt-1">
                  <span className="text-indigo-600 dark:text-indigo-400 font-medium">
                    답변: {Object.keys(answers).length}/{test.questions.length}
                  </span>
                  {Object.keys(answers).length < test.questions.length && (
                    <span className="ml-2 text-red-500">
                      (미답변 {test.questions.length - Object.keys(answers).length}개)
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${((currentQuestionIndex + 1) / test.questions.length) * 100}%`
                }}
              />
            </div>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          <div className="mb-8">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                문제 {currentQuestionIndex + 1}
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {renderTextWithCode(currentQuestion.question_text)}
              </p>

              {currentQuestion.content && (
                <div className="mt-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                  <p className="text-sm font-medium text-indigo-800 dark:text-indigo-200">
                    관련 콘텐츠: {currentQuestion.content.title}
                  </p>
                </div>
              )}
            </div>

            <div className="space-y-4">
              {currentQuestion.question_type === 'true_false' ? (
                <div className="flex space-x-4">
                  {['O', 'X'].map((option) => (
                    <button
                      key={option}
                      onClick={() => onAnswerSelect(currentQuestion.id, option)}
                      className={`flex-1 py-3 px-6 rounded-lg border-2 transition-all ${
                        answers[currentQuestion.id] === option
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 border-indigo-600 text-white'
                          : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-indigo-500'
                      }`}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  {currentQuestion.choices?.map((choice, index) => (
                    <button
                      key={index}
                      onClick={() => onAnswerSelect(currentQuestion.id, choice)}
                      className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                        answers[currentQuestion.id] === choice
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 border-indigo-600 text-white'
                          : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-indigo-500'
                      }`}
                    >
                      {index + 1}. {choice}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-between">
            <button
              onClick={onPrevious}
              disabled={currentQuestionIndex === 0}
              className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              이전 문제
            </button>

            {isLastQuestion ? (
              <button
                onClick={onComplete}
                disabled={isLoading}
                className="px-6 py-3 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50 transition-colors"
              >
                {isLoading ? '완료 중...' : '시험 완료'}
              </button>
            ) : (
              <button
                onClick={onNext}
                className="px-6 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg transition-all duration-200 shadow-md"
              >
                다음 문제
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestQuestionView;
