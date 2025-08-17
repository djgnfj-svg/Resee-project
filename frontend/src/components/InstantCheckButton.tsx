import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  MagnifyingGlassIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiClient } from '../utils/api';
import LoadingSpinner from './LoadingSpinner';

interface InstantCheckResult {
  id: number;
  check_point: string;
  questions_count: number;
  correct_count: number;
  understanding_score: number;
  weak_points: string[];
  feedback: string;
  duration_seconds: number;
}

interface InstantCheckQuestion {
  question_text: string;
  correct_answer: string;
  options?: string[];
  explanation?: string;
}

interface InstantCheckButtonProps {
  contentId: number;
  checkPoint?: string;
  className?: string;
  children?: React.ReactNode;
}

const InstantCheckButton: React.FC<InstantCheckButtonProps> = ({ 
  contentId, 
  checkPoint = 'current',
  className = '',
  children
}) => {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [questions, setQuestions] = useState<InstantCheckQuestion[]>([]);
  const [userAnswers, setUserAnswers] = useState<string[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const [checkResult, setCheckResult] = useState<InstantCheckResult | null>(null);

  // 실시간 검토 시작
  const startCheckMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/ai-review/instant-check/', {
        content_id: contentId,
        check_point: checkPoint,
        question_count: 3
      });
      return response.data;
    },
    onSuccess: (data) => {
      setQuestions(data.questions);
      setUserAnswers(new Array(data.questions.length).fill(''));
      setCurrentQuestion(0);
      setShowModal(true);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '검토를 시작할 수 없습니다.';
      toast.error(message);
    }
  });

  // 답안 제출 및 결과 조회
  const submitAnswersMutation = useMutation({
    mutationFn: async (answers: string[]) => {
      const response = await apiClient.post('/api/ai-review/instant-check/submit/', {
        content_id: contentId,
        check_point: checkPoint,
        answers: answers
      });
      return response.data;
    },
    onSuccess: (data) => {
      setCheckResult(data);
      setShowResults(true);
      queryClient.invalidateQueries({ queryKey: ['content', contentId] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '답안 제출에 실패했습니다.';
      toast.error(message);
    }
  });

  const handleStartCheck = () => {
    startCheckMutation.mutate();
  };

  const handleAnswerChange = (answer: string) => {
    const newAnswers = [...userAnswers];
    newAnswers[currentQuestion] = answer;
    setUserAnswers(newAnswers);
  };

  const handleNextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // 마지막 문제면 제출
      submitAnswersMutation.mutate(userAnswers);
    }
  };

  const handlePrevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setShowResults(false);
    setQuestions([]);
    setUserAnswers([]);
    setCurrentQuestion(0);
    setCheckResult(null);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const currentQ = questions[currentQuestion];

  return (
    <>
      <button
        onClick={handleStartCheck}
        disabled={startCheckMutation.isPending}
        className={`inline-flex items-center px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 ${className}`}
      >
        {startCheckMutation.isPending ? (
          <LoadingSpinner className="w-4 h-4 mr-2" />
        ) : (
          <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
        )}
        {children || (startCheckMutation.isPending ? '검토 준비중...' : '실시간 검토')}
      </button>

      {/* 검토 모달 */}
      {showModal && !showResults && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* 모달 헤더 */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <MagnifyingGlassIcon className="w-6 h-6 text-blue-600 mr-2" />
                  <h3 className="text-xl font-semibold text-gray-900">
                    실시간 이해도 검토
                  </h3>
                </div>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* 진행률 */}
              <div className="mb-6">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>문제 {currentQuestion + 1} / {questions.length}</span>
                  <span>{Math.round(((currentQuestion + 1) / questions.length) * 100)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${((currentQuestion + 1) / questions.length) * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* 현재 문제 */}
              {currentQ && (
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-4">
                    {currentQ.question_text}
                  </h4>

                  {currentQ.options ? (
                    // 객관식
                    <div className="space-y-2">
                      {currentQ.options.map((option, index) => (
                        <label 
                          key={index}
                          className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="radio"
                            name="answer"
                            value={option}
                            checked={userAnswers[currentQuestion] === option}
                            onChange={(e) => handleAnswerChange(e.target.value)}
                            className="mr-3"
                          />
                          <span>{option}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    // 주관식
                    <textarea
                      value={userAnswers[currentQuestion] || ''}
                      onChange={(e) => handleAnswerChange(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
                      rows={4}
                      placeholder="답변을 입력하세요..."
                    />
                  )}
                </div>
              )}

              {/* 네비게이션 버튼 */}
              <div className="flex justify-between">
                <button
                  onClick={handlePrevQuestion}
                  disabled={currentQuestion === 0}
                  className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
                >
                  이전
                </button>
                <button
                  onClick={handleNextQuestion}
                  disabled={!userAnswers[currentQuestion] || submitAnswersMutation.isPending}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
                >
                  {submitAnswersMutation.isPending ? (
                    <LoadingSpinner className="w-4 h-4 mr-2" />
                  ) : null}
                  {currentQuestion === questions.length - 1 ? 
                    (submitAnswersMutation.isPending ? '제출 중...' : '제출') : 
                    '다음'
                  }
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 결과 모달 */}
      {showResults && checkResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* 모달 헤더 */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <CheckCircleIcon className="w-6 h-6 text-green-600 mr-2" />
                  <h3 className="text-xl font-semibold text-gray-900">
                    검토 결과
                  </h3>
                </div>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* 점수 카드 */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className={`text-2xl font-bold ${getScoreColor(checkResult.understanding_score)}`}>
                    {checkResult.understanding_score.toFixed(0)}점
                  </div>
                  <div className="text-sm text-gray-600">이해도</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {checkResult.correct_count}/{checkResult.questions_count}
                  </div>
                  <div className="text-sm text-gray-600">정답</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900 flex items-center justify-center">
                    <ClockIcon className="w-5 h-5 mr-1" />
                    {Math.round(checkResult.duration_seconds / 60)}분
                  </div>
                  <div className="text-sm text-gray-600">소요시간</div>
                </div>
              </div>

              {/* AI 피드백 */}
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 mb-3">AI 피드백</h4>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-gray-700">{checkResult.feedback}</p>
                </div>
              </div>

              {/* 취약점 */}
              {checkResult.weak_points.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 mb-3 flex items-center">
                    <ExclamationCircleIcon className="w-5 h-5 text-yellow-500 mr-2" />
                    보완이 필요한 부분
                  </h4>
                  <div className="space-y-2">
                    {checkResult.weak_points.map((point, index) => (
                      <div key={index} className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
                        <span className="text-yellow-800">{point}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 확인 버튼 */}
              <div className="text-right">
                <button
                  onClick={closeModal}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  확인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default InstantCheckButton;