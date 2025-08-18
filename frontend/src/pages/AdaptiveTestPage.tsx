import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AdjustmentsHorizontalIcon,
  ClockIcon,
  TrophyIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { AdaptiveTest, AdaptiveTestQuestion, AIQuestion } from '../types/ai-review';

interface AdaptiveQuestion {
  question_text: string;
  question_type: string;
  options: string[];
  correct_answer: string;
  difficulty: string;
  explanation: string;
  estimated_time: string;
}

const AdaptiveTestPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [currentTest, setCurrentTest] = useState<AdaptiveTest | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<AdaptiveQuestion | null>(null);
  const [userAnswer, setUserAnswer] = useState('');
  const [questionNumber, setQuestionNumber] = useState(0);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [showSetup, setShowSetup] = useState(true);
  
  // 설정 상태
  const [contentArea, setContentArea] = useState('');
  const [targetQuestions, setTargetQuestions] = useState(10);

  // 시험 시작
  const startTestMutation = useMutation({
    mutationFn: async ({ content_area, target_questions }: { content_area: string; target_questions: number }) => {
      const response = await apiClient.post('/api/ai-review/adaptive-test/start/', {
        content_area,
        target_questions
      });
      return response.data;
    },
    onSuccess: (data) => {
      setCurrentTest(data.test);
      setCurrentQuestion(data.first_question);
      setQuestionNumber(1);
      setShowSetup(false);
      toast.success('적응형 시험이 시작되었습니다!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '시험 시작에 실패했습니다.';
      toast.error(message);
    }
  });

  // 답안 제출 및 다음 문제
  const submitAnswerMutation = useMutation({
    mutationFn: async ({ test_id, user_answer }: { test_id: number; user_answer: string }) => {
      const response = await apiClient.post(`/api/ai-review/adaptive-test/${test_id}/answer/`, {
        user_answer
      });
      return response.data;
    },
    onSuccess: (data) => {
      setCurrentTest(data.test);
      
      if (data.is_completed) {
        setShowResult(true);
        toast.success('시험이 완료되었습니다!');
      } else {
        setCurrentQuestion(data.next_question);
        setQuestionNumber(prev => prev + 1);
        setUserAnswer('');
        
        // 난이도 변경 알림
        if (data.difficulty_changed) {
          const difficultyLabels: Record<string, string> = { easy: '쉬움', medium: '보통', hard: '어려움' };
          toast.success(`난이도가 "${difficultyLabels[data.test.current_difficulty]}"으로 조절되었습니다.`);
        }
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '답안 제출에 실패했습니다.';
      toast.error(message);
    }
  });

  // 타이머 효과
  useEffect(() => {
    if (currentQuestion && !showResult) {
      const estimatedSeconds = parseInt(currentQuestion.estimated_time);
      setTimeLeft(estimatedSeconds);
      
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev === null || prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      return () => clearInterval(timer);
    }
  }, [currentQuestion, showResult]);

  const handleSubmitAnswer = () => {
    if (!currentTest || !userAnswer.trim()) return;
    submitAnswerMutation.mutate({
      test_id: currentTest.id,
      user_answer: userAnswer
    });
  };

  const handleStartNewTest = () => {
    setCurrentTest(null);
    setCurrentQuestion(null);
    setUserAnswer('');
    setQuestionNumber(0);
    setShowResult(false);
    setShowSetup(true);
    setContentArea('');
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDifficultyLabel = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '쉬움';
      case 'medium': return '보통';
      case 'hard': return '어려움';
      default: return difficulty;
    }
  };

  // 설정 화면
  if (showSetup) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center mb-8">
              <AdjustmentsHorizontalIcon className="mx-auto h-16 w-16 text-indigo-600 mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">AI 적응형 시험</h1>
              <p className="text-gray-600">
                당신의 실력에 맞춰 난이도가 자동으로 조절되는 똑똑한 시험
              </p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  시험 주제
                </label>
                <input
                  type="text"
                  value={contentArea}
                  onChange={(e) => setContentArea(e.target.value)}
                  placeholder="예: Python 기초, 수학 미적분, 영어 문법..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  문제 수
                </label>
                <select
                  value={targetQuestions}
                  onChange={(e) => setTargetQuestions(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value={5}>5문제 (빠른 테스트)</option>
                  <option value={10}>10문제 (표준)</option>
                  <option value={15}>15문제 (정밀 분석)</option>
                  <option value={20}>20문제 (종합 평가)</option>
                </select>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-800 mb-2">적응형 시험의 특징</h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• 연속 3문제 정답 → 난이도 상승</li>
                  <li>• 연속 2문제 오답 → 난이도 하락</li>
                  <li>• 실시간 실력 측정 및 레벨 판정</li>
                  <li>• 개인 맞춤형 문제 출제</li>
                </ul>
              </div>

              <button
                onClick={() => startTestMutation.mutate({ content_area: contentArea, target_questions: targetQuestions })}
                disabled={!contentArea.trim() || startTestMutation.isPending}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors font-medium flex items-center justify-center"
              >
                {startTestMutation.isPending ? (
                  <LoadingSpinner className="w-5 h-5 mr-2" />
                ) : (
                  <TrophyIcon className="w-5 h-5 mr-2" />
                )}
                {startTestMutation.isPending ? '시험 준비 중...' : '적응형 시험 시작'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 결과 화면
  if (showResult && currentTest) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center mb-8">
              <TrophyIcon className="mx-auto h-16 w-16 text-indigo-600 mb-4" />
              <h1 className="text-3xl font-bold text-gray-900 mb-2">시험 완료!</h1>
              <p className="text-gray-600">AI가 분석한 당신의 실력을 확인해보세요</p>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {currentTest.total_questions > 0 ? 
                    ((currentTest.correct_answers / currentTest.total_questions) * 100).toFixed(0) : 
                    '0'}%
                </div>
                <div className="text-sm text-gray-600">정답률</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className={`text-2xl font-bold px-3 py-1 rounded-full text-center ${getDifficultyColor(currentTest.current_difficulty)}`}>
                  {getDifficultyLabel(currentTest.current_difficulty)}
                </div>
                <div className="text-sm text-gray-600 mt-2">최종 레벨</div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg mb-6">
              <h3 className="font-medium text-gray-900 mb-3">상세 결과</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">총 문제:</span>
                  <span className="ml-2 font-medium">{currentTest.total_questions}개</span>
                </div>
                <div>
                  <span className="text-gray-600">정답:</span>
                  <span className="ml-2 font-medium text-green-600">{currentTest.correct_answers}개</span>
                </div>
                <div>
                  <span className="text-gray-600">연속 정답:</span>
                  <span className="ml-2 font-medium">{currentTest.consecutive_correct}개</span>
                </div>
                <div>
                  <span className="text-gray-600">연속 오답:</span>
                  <span className="ml-2 font-medium">{currentTest.consecutive_wrong}개</span>
                </div>
              </div>
            </div>

            {currentTest.estimated_proficiency && (
              <div className="bg-indigo-50 p-4 rounded-lg mb-6">
                <h3 className="font-medium text-indigo-800 mb-2">AI 실력 분석</h3>
                <div className="text-indigo-700">
                  <span className="text-2xl font-bold">{currentTest.estimated_proficiency.toFixed(0)}점</span>
                  <span className="text-sm ml-2">(100점 만점)</span>
                </div>
                <div className="text-sm text-indigo-600 mt-2">
                  {currentTest.estimated_proficiency >= 80 ? '고급 수준입니다!' :
                   currentTest.estimated_proficiency >= 60 ? '중급 수준입니다.' :
                   '초급 수준입니다. 더 학습해보세요!'}
                </div>
              </div>
            )}

            <div className="space-y-3">
              <button
                onClick={handleStartNewTest}
                className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
              >
                새로운 시험 시작
              </button>
              <button
                onClick={() => window.history.back()}
                className="w-full bg-gray-600 text-white py-3 rounded-lg hover:bg-gray-700 transition-colors font-medium"
              >
                돌아가기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 시험 진행 화면
  if (currentTest && currentQuestion) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 py-8">
          {/* 진행률 헤더 */}
          <div className="bg-white rounded-xl shadow-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <span className="text-sm text-gray-600">문제 {questionNumber} / {currentTest.target_questions}</span>
                <span className={`ml-4 px-3 py-1 rounded-full text-xs font-medium ${getDifficultyColor(currentTest.current_difficulty)}`}>
                  {getDifficultyLabel(currentTest.current_difficulty)}
                </span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <ClockIcon className="h-4 w-4 mr-1" />
                {timeLeft !== null && timeLeft > 0 ? `${timeLeft}초` : '시간 초과'}
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(questionNumber / currentTest.target_questions) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* 문제 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-medium text-gray-900 mb-6">
              {currentQuestion.question_text}
            </h2>

            <div className="space-y-3 mb-6">
              {currentQuestion.options.map((option, index) => (
                <label
                  key={index}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="answer"
                    value={option}
                    checked={userAnswer === option}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    className="mr-3"
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>

            <button
              onClick={handleSubmitAnswer}
              disabled={!userAnswer || submitAnswerMutation.isPending}
              className="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors font-medium flex items-center justify-center"
            >
              {submitAnswerMutation.isPending ? (
                <LoadingSpinner className="w-5 h-5 mr-2" />
              ) : (
                <ArrowRightIcon className="w-5 h-5 mr-2" />
              )}
              {submitAnswerMutation.isPending ? '제출 중...' : 
               questionNumber === currentTest.target_questions ? '시험 완료' : '다음 문제'}
            </button>
          </div>

          {/* 현재 성과 */}
          <div className="mt-6 bg-white rounded-xl shadow-lg p-4">
            <h3 className="font-medium text-gray-900 mb-3">현재 성과</h3>
            <div className="flex items-center justify-between text-sm">
              <span>정답률: {currentTest.total_questions > 0 ? 
                ((currentTest.correct_answers / currentTest.total_questions) * 100).toFixed(0) : 
                '0'}%</span>
              <span>연속 정답: {currentTest.consecutive_correct}개</span>
              <span>연속 오답: {currentTest.consecutive_wrong}개</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <LoadingSpinner />
    </div>
  );
};

export default AdaptiveTestPage;