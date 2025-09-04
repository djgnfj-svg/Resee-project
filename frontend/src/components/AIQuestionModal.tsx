import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { XMarkIcon, SparklesIcon, AcademicCapIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiClient } from '../utils/api';
import LoadingSpinner from './LoadingSpinner';
import { Content } from '../types';
import { 
  AIQuestion, 
  QUESTION_TYPES, 
  DIFFICULTY_LEVELS, 
  QuestionTypeName, 
  DifficultyLevel 
} from '../types/ai-review';

interface AIQuestionModalProps {
  content: Content;
  onClose: () => void;
}

const AIQuestionModal: React.FC<AIQuestionModalProps> = ({ content, onClose }) => {
  const [questions, setQuestions] = useState<AIQuestion[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [showResults, setShowResults] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedTypes, setSelectedTypes] = useState<QuestionTypeName[]>(['multiple_choice']);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>(DIFFICULTY_LEVELS.MEDIUM);
  const [count, setCount] = useState(3);

  // AI 질문 생성 mutation
  const generateQuestionsMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/ai-review/generate-questions/', {
        content_id: content.id,
        question_types: selectedTypes,
        difficulty: difficulty,
        count: count
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

  const handleTypeToggle = (type: QuestionTypeName) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const handleGenerateQuestions = () => {
    if (selectedTypes.length === 0) {
      toast.error('최소 하나의 질문 유형을 선택해주세요.');
      return;
    }
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
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                title="질문 설정"
              >
                <Cog6ToothIcon className="h-6 w-6" />
              </button>
              <button
                onClick={onClose}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* Settings Panel */}
          {showSettings && (
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">질문 설정</h3>
              
              {/* Question Types */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  질문 유형
                </label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(QUESTION_TYPES.MULTIPLE_CHOICE)}
                      onChange={() => handleTypeToggle(QUESTION_TYPES.MULTIPLE_CHOICE)}
                      className="rounded border-gray-300 text-indigo-600 mr-2"
                    />
                    <span className="text-sm">객관식</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(QUESTION_TYPES.FILL_BLANK)}
                      onChange={() => handleTypeToggle(QUESTION_TYPES.FILL_BLANK)}
                      className="rounded border-gray-300 text-indigo-600 mr-2"
                    />
                    <span className="text-sm">빈칸 채우기</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedTypes.includes(QUESTION_TYPES.BLUR_PROCESSING)}
                      onChange={() => handleTypeToggle(QUESTION_TYPES.BLUR_PROCESSING)}
                      className="rounded border-gray-300 text-indigo-600 mr-2"
                    />
                    <span className="text-sm">중요 구간 찾기</span>
                  </label>
                </div>
              </div>

              {/* Difficulty */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  난이도: {difficulty === 1 ? '매우 쉬움' : difficulty === 2 ? '쉬움' : difficulty === 3 ? '보통' : difficulty === 4 ? '어려움' : '매우 어려움'}
                </label>
                <input
                  type="range"
                  min={DIFFICULTY_LEVELS.VERY_EASY}
                  max={DIFFICULTY_LEVELS.VERY_HARD}
                  value={difficulty}
                  onChange={(e) => setDifficulty(Number(e.target.value) as DifficultyLevel)}
                  className="w-full"
                />
              </div>

              {/* Count */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  질문 개수: {count}개
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  className="w-full"
                />
              </div>
            </div>
          )}

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
                    <div className="ml-3 flex-1">
                      <p className="text-gray-900 dark:text-white font-medium">
                        {question.question_text}
                      </p>
                      <span className="inline-block mt-1 px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                        {question.question_type_display} • 난이도 {question.difficulty}
                      </span>
                    </div>
                  </div>

                  {/* Multiple Choice Questions */}
                  {question.options && question.question_type_display === '객관식' && (
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

                  {/* Fill in the Blank Questions */}
                  {question.question_type_display === '빈칸 채우기' && (
                    <div className="ml-11">
                      <textarea
                        placeholder="답을 입력하세요..."
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        rows={3}
                        value={selectedAnswers[question.id] || ''}
                        onChange={(e) => handleAnswerSelect(question.id, e.target.value)}
                        disabled={showResults}
                      />
                      {showResults && (
                        <div className="mt-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                          <p className="text-sm text-green-800 dark:text-green-300">
                            <strong>정답:</strong> {question.correct_answer}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Blur Processing Questions */}
                  {question.question_type_display === '중요 구간 찾기' && (
                    <div className="ml-11">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        중요한 구간이나 핵심 개념을 찾아 설명해주세요:
                      </p>
                      <textarea
                        placeholder="중요한 구간과 이유를 설명해주세요..."
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        rows={4}
                        value={selectedAnswers[question.id] || ''}
                        onChange={(e) => handleAnswerSelect(question.id, e.target.value)}
                        disabled={showResults}
                      />
                      {showResults && question.keywords && (
                        <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <p className="text-sm text-blue-800 dark:text-blue-300">
                            <strong>핵심 키워드:</strong> {question.keywords.join(', ')}
                          </p>
                        </div>
                      )}
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
                <div className="flex justify-between mt-6">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    답변 진행률: {Object.keys(selectedAnswers).length}/{questions.length}
                  </div>
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
                  <p className="text-gray-700 dark:text-gray-300 mb-4">
                    총 {questions.length}문제 중{' '}
                    {questions.filter(q => selectedAnswers[q.id] === q.correct_answer).length}문제 정답
                    <span className="ml-2 font-semibold">
                      ({Math.round((questions.filter(q => selectedAnswers[q.id] === q.correct_answer).length / questions.length) * 100)}%)
                    </span>
                  </p>
                  <div className="flex space-x-2">
                    <button
                      onClick={handleGenerateQuestions}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      새로운 질문 생성
                    </button>
                    <button
                      onClick={() => {
                        setQuestions([]);
                        setSelectedAnswers({});
                        setShowResults(false);
                      }}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      처음으로
                    </button>
                  </div>
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