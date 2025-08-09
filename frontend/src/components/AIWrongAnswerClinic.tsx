import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ExclamationTriangleIcon,
  LightBulbIcon,
  AcademicCapIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import apiClient from '../utils/apiClient';
import LoadingSpinner from './LoadingSpinner';

interface WrongAnswerAnalysis {
  error_analysis: string;
  concept_explanation: string;
  additional_tips: string[];
  practice_question: {
    question_text: string;
    options: string[];
    correct_answer: string;
    explanation: string;
  };
}

interface AIWrongAnswerClinicProps {
  questionId: number;
  questionText: string;
  userAnswer: string;
  correctAnswer: string;
  onClose: () => void;
  className?: string;
}

const AIWrongAnswerClinic: React.FC<AIWrongAnswerClinicProps> = ({
  questionId,
  questionText,
  userAnswer,
  correctAnswer,
  onClose,
  className = ''
}) => {
  const queryClient = useQueryClient();
  const [analysis, setAnalysis] = useState<WrongAnswerAnalysis | null>(null);
  const [practiceAnswer, setPracticeAnswer] = useState('');
  const [showPractice, setShowPractice] = useState(false);
  const [practiceResult, setPracticeResult] = useState<'correct' | 'incorrect' | null>(null);

  // 오답 분석 요청
  const analyzeWrongAnswerMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/ai-review/wrong-answer-clinic/', {
        question_id: questionId,
        user_answer: userAnswer
      });
      return response.data;
    },
    onSuccess: (data) => {
      setAnalysis(data);
      toast.success('AI 오답 분석이 완료되었습니다!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '오답 분석에 실패했습니다.';
      toast.error(message);
    }
  });

  const handleStartAnalysis = () => {
    analyzeWrongAnswerMutation.mutate();
  };

  const handlePracticeSubmit = () => {
    if (!analysis?.practice_question) return;
    
    const isCorrect = practiceAnswer === analysis.practice_question.correct_answer;
    setPracticeResult(isCorrect ? 'correct' : 'incorrect');
    
    if (isCorrect) {
      toast.success('정답입니다! 개념을 잘 이해하셨네요.');
    } else {
      toast.error('아직 연습이 더 필요해요. 해설을 다시 읽어보세요.');
    }
  };

  const handleTryAgain = () => {
    setPracticeAnswer('');
    setPracticeResult(null);
  };

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 ${className}`}>
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-500 mr-2" />
              <h3 className="text-xl font-semibold text-gray-900">AI 오답 클리닉</h3>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* 문제 정보 */}
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <h4 className="font-medium text-gray-900 mb-2">틀린 문제</h4>
            <div className="text-gray-700 mb-3">{questionText}</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-red-600">내 답변:</span>
                <span className="ml-2 text-red-700">{userAnswer}</span>
              </div>
              <div>
                <span className="font-medium text-green-600">정답:</span>
                <span className="ml-2 text-green-700">{correctAnswer}</span>
              </div>
            </div>
          </div>

          {/* 분석 시작 버튼 */}
          {!analysis && (
            <div className="text-center py-8">
              <ExclamationTriangleIcon className="mx-auto h-16 w-16 text-gray-400 mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                왜 틀렸는지 궁금하신가요?
              </h4>
              <p className="text-gray-600 mb-6">
                AI가 오답 원인을 분석하고 맞춤형 학습 가이드를 제공해드립니다.
              </p>
              <button
                onClick={handleStartAnalysis}
                disabled={analyzeWrongAnswerMutation.isPending}
                className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors font-medium flex items-center mx-auto disabled:opacity-50"
              >
                {analyzeWrongAnswerMutation.isPending ? (
                  <LoadingSpinner className="w-5 h-5 mr-2" />
                ) : (
                  <LightBulbIcon className="w-5 h-5 mr-2" />
                )}
                {analyzeWrongAnswerMutation.isPending ? 'AI 분석 중...' : 'AI 오답 분석 시작'}
              </button>
            </div>
          )}

          {/* 분석 결과 */}
          {analysis && (
            <div className="space-y-6">
              {/* 오답 원인 분석 */}
              <div className="border border-red-200 rounded-lg p-4 bg-red-50">
                <h4 className="font-medium text-red-800 mb-3 flex items-center">
                  <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
                  왜 틀렸을까요?
                </h4>
                <p className="text-red-700">{analysis.error_analysis}</p>
              </div>

              {/* 개념 재설명 */}
              <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                <h4 className="font-medium text-blue-800 mb-3 flex items-center">
                  <AcademicCapIcon className="h-4 w-4 mr-2" />
                  핵심 개념 이해하기
                </h4>
                <p className="text-blue-700">{analysis.concept_explanation}</p>
              </div>

              {/* 학습 팁 */}
              <div className="border border-green-200 rounded-lg p-4 bg-green-50">
                <h4 className="font-medium text-green-800 mb-3 flex items-center">
                  <LightBulbIcon className="h-4 w-4 mr-2" />
                  실용적인 학습 팁
                </h4>
                <ul className="space-y-2 text-green-700">
                  {analysis.additional_tips.map((tip, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-green-600 mr-2">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* 연습 문제 */}
              {analysis.practice_question && (
                <div className="border border-indigo-200 rounded-lg p-4 bg-indigo-50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-indigo-800 flex items-center">
                      <CheckCircleIcon className="h-4 w-4 mr-2" />
                      비슷한 문제로 연습해보기
                    </h4>
                    {!showPractice && (
                      <button
                        onClick={() => setShowPractice(true)}
                        className="text-indigo-600 hover:text-indigo-800 flex items-center text-sm font-medium"
                      >
                        연습하기 <ArrowRightIcon className="h-3 w-3 ml-1" />
                      </button>
                    )}
                  </div>

                  {showPractice && (
                    <div>
                      <div className="text-indigo-800 mb-4">
                        {analysis.practice_question.question_text}
                      </div>

                      {practiceResult === null ? (
                        <div className="space-y-3">
                          {analysis.practice_question.options.map((option, index) => (
                            <label
                              key={index}
                              className="flex items-center p-2 border border-indigo-200 rounded cursor-pointer hover:bg-indigo-100"
                            >
                              <input
                                type="radio"
                                name="practice"
                                value={option}
                                checked={practiceAnswer === option}
                                onChange={(e) => setPracticeAnswer(e.target.value)}
                                className="mr-3"
                              />
                              <span className="text-indigo-700">{option}</span>
                            </label>
                          ))}
                          <button
                            onClick={handlePracticeSubmit}
                            disabled={!practiceAnswer}
                            className="w-full bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 mt-4"
                          >
                            답안 확인
                          </button>
                        </div>
                      ) : (
                        <div className={`p-4 rounded-lg ${
                          practiceResult === 'correct' 
                            ? 'bg-green-100 border border-green-200' 
                            : 'bg-red-100 border border-red-200'
                        }`}>
                          <div className={`font-medium mb-2 ${
                            practiceResult === 'correct' ? 'text-green-800' : 'text-red-800'
                          }`}>
                            {practiceResult === 'correct' ? '✅ 정답입니다!' : '❌ 틀렸습니다.'}
                          </div>
                          <div className={`text-sm ${
                            practiceResult === 'correct' ? 'text-green-700' : 'text-red-700'
                          }`}>
                            <strong>정답:</strong> {analysis.practice_question.correct_answer}
                          </div>
                          <div className={`text-sm mt-2 ${
                            practiceResult === 'correct' ? 'text-green-700' : 'text-red-700'
                          }`}>
                            <strong>해설:</strong> {analysis.practice_question.explanation}
                          </div>
                          <button
                            onClick={handleTryAgain}
                            className="mt-3 text-indigo-600 hover:text-indigo-800 text-sm font-medium"
                          >
                            다시 풀어보기
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* 완료 버튼 */}
              <div className="text-center pt-4">
                <button
                  onClick={onClose}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  이해했어요!
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIWrongAnswerClinic;