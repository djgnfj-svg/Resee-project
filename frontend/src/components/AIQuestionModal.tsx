import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { XMarkIcon, SparklesIcon, AcademicCapIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiClient } from '../utils/api';
import LoadingSpinner from './LoadingSpinner';
import { Content } from '../types';
import { AIQuestion } from '../types/ai-review';

interface AIQuestionModalProps {
  content: Content;
  onClose: () => void;
}

const AIQuestionModal: React.FC<AIQuestionModalProps> = ({ content, onClose }) => {
  const [questions, setQuestions] = useState<AIQuestion[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);

  // AI 질문 생성 mutation
  const generateQuestionsMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/ai-review/generate-questions/', {
        content_id: content.id,
        question_types: ['multiple_choice'],
        difficulty: 3,
        count: 3
      });
      return response.data;
    },
    onSuccess: (data) => {
      setQuestions(data);
      toast.success('AI 질문이 생성되었습니다!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'AI 질문 생성에 실패했습니다.';
      toast.error(message);
    }
  });

  const handleAnswerSelect = (questionId: number, answer: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmit = () => {
    setShowResults(true);
  };

  const handleGenerateQuestions = () => {
    generateQuestionsMutation.mutate();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <SparklesIcon className="h-8 w-8 mr-3" />
              <div>
                <h2 className="text-2xl font-bold">AI 학습</h2>
                <p className="text-indigo-100 mt-1">{content.title}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {questions.length === 0 ? (
            <div className="text-center py-12">
              <AcademicCapIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                AI 질문을 생성해보세요
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                AI가 콘텐츠를 분석하여 학습에 도움이 되는 질문을 만들어드립니다.
              </p>
              <button
                onClick={handleGenerateQuestions}
                disabled={generateQuestionsMutation.isPending}
                className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center mx-auto"
              >
                {generateQuestionsMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" color="white" />
                    <span className="ml-2">AI 질문 생성 중...</span>
                  </>
                ) : (
                  <>
                    <SparklesIcon className="h-5 w-5 mr-2" />
                    AI 질문 생성하기
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-6">
              {questions.map((question, index) => (
                <div key={question.id} className="border dark:border-gray-700 rounded-lg p-6">
                  <div className="flex items-start mb-4">
                    <span className="flex-shrink-0 w-8 h-8 bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full flex items-center justify-center font-semibold text-sm">
                      {index + 1}
                    </span>
                    <p className="ml-3 text-gray-900 dark:text-white font-medium">
                      {question.question_text}
                    </p>
                  </div>

                  {question.options && (
                    <div className="space-y-2 ml-11">
                      {question.options.map((option, optionIndex) => (
                        <label
                          key={optionIndex}
                          className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                            selectedAnswers[question.id] === option
                              ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                              : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                          } ${showResults ? 'cursor-not-allowed' : ''}`}
                        >
                          <input
                            type="radio"
                            name={`question-${question.id}`}
                            value={option}
                            checked={selectedAnswers[question.id] === option}
                            onChange={() => handleAnswerSelect(question.id, option)}
                            disabled={showResults}
                            className="mr-3"
                          />
                          <span className={`${
                            showResults && option === question.correct_answer
                              ? 'text-green-600 dark:text-green-400 font-semibold'
                              : showResults && selectedAnswers[question.id] === option && option !== question.correct_answer
                              ? 'text-red-600 dark:text-red-400 line-through'
                              : ''
                          }`}>
                            {option}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}

                  {showResults && question.explanation && (
                    <div className="mt-4 ml-11 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        <strong>해설:</strong> {question.explanation}
                      </p>
                    </div>
                  )}
                </div>
              ))}

              {!showResults && (
                <div className="flex justify-end mt-6">
                  <button
                    onClick={handleSubmit}
                    disabled={Object.keys(selectedAnswers).length !== questions.length}
                    className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    답안 제출
                  </button>
                </div>
              )}

              {showResults && (
                <div className="mt-6 p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <h3 className="font-semibold text-lg mb-2">결과</h3>
                  <p className="text-gray-700 dark:text-gray-300">
                    총 {questions.length}문제 중{' '}
                    {questions.filter(q => selectedAnswers[q.id] === q.correct_answer).length}문제 정답
                  </p>
                  <button
                    onClick={handleGenerateQuestions}
                    className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    새로운 질문 생성
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIQuestionModal;