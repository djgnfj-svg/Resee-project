import React, { useState, useEffect } from 'react';

interface ReviewSimulationProps {
  className?: string;
}

const ReviewSimulation: React.FC<ReviewSimulationProps> = ({ className = '' }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [userResponse, setUserResponse] = useState<'remembered' | 'partial' | 'forgot' | null>(null);

  // 시뮬레이션 데이터
  const reviewSteps = [
    {
      id: 1,
      question: "React에서 컴포넌트의 상태를 관리하는 Hook은?",
      answer: "useState Hook을 사용하여 함수형 컴포넌트에서 상태를 관리할 수 있습니다.",
      category: "프로그래밍",
      difficulty: "기본",
      interval: "1일차 복습"
    },
    {
      id: 2,
      question: "에빙하우스 망각곡선의 핵심 원리는?",
      answer: "시간이 지날수록 기억이 감소하며, 복습을 통해 기억을 강화할 수 있다는 원리입니다.",
      category: "심리학",
      difficulty: "중급",
      interval: "3일차 복습"
    },
    {
      id: 3,
      question: "TypeScript의 주요 장점은?",
      answer: "정적 타입 검사를 통해 컴파일 시점에 오류를 발견하고 코드의 안정성을 향상시킵니다.",
      category: "프로그래밍",
      difficulty: "중급",
      interval: "7일차 복습"
    }
  ];

  const currentReview = reviewSteps[currentStep];

  useEffect(() => {
    if (!isAutoPlaying) return;

    const timer = setTimeout(() => {
      if (!showAnswer) {
        setShowAnswer(true);
      } else {
        // 자동으로 다음 단계로 이동
        if (currentStep < reviewSteps.length - 1) {
          setCurrentStep(prev => prev + 1);
          setShowAnswer(false);
          setUserResponse(null);
        } else {
          setCurrentStep(0);
          setShowAnswer(false);
          setUserResponse(null);
        }
      }
    }, showAnswer ? 3000 : 2500);

    return () => clearTimeout(timer);
  }, [currentStep, showAnswer, isAutoPlaying, reviewSteps.length]);

  const handleResponse = (response: 'remembered' | 'partial' | 'forgot') => {
    setUserResponse(response);
    setIsAutoPlaying(false);
  };

  const handleNext = () => {
    if (currentStep < reviewSteps.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      setCurrentStep(0);
    }
    setShowAnswer(false);
    setUserResponse(null);
    setIsAutoPlaying(true);
  };

  const handleShowAnswer = () => {
    setShowAnswer(true);
    setIsAutoPlaying(false);
  };

  const getResponseColor = (response: string) => {
    switch (response) {
      case 'remembered': return 'bg-green-500';
      case 'partial': return 'bg-yellow-500';
      case 'forgot': return 'bg-red-500';
      default: return 'bg-gray-300';
    }
  };

  const getNextInterval = (response: 'remembered' | 'partial' | 'forgot') => {
    switch (response) {
      case 'remembered': return '다음 복습: 7일 후';
      case 'partial': return '다음 복습: 3일 후';
      case 'forgot': return '다음 복습: 1일 후';
    }
  };

  return (
    <div className={`${className}`}>
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          복습 과정 체험하기
        </h3>
        <p className="text-gray-600 dark:text-gray-400 text-lg">
          실제 Resee에서 복습하는 과정을 미리 경험해보세요
        </p>
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              진행률
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {currentStep + 1} / {reviewSteps.length}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${((currentStep + 1) / reviewSteps.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Review Card */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {currentReview.category}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-purple-400 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {currentReview.difficulty}
                  </span>
                </div>
              </div>
              <span className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full text-xs font-medium">
                {currentReview.interval}
              </span>
            </div>
          </div>

          {/* Content */}
          <div className="p-8">
            <div className="mb-8">
              <h4 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                📝 문제
              </h4>
              <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                {currentReview.question}
              </p>
            </div>

            {showAnswer && (
              <div className="mb-8 p-6 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-2xl border border-green-200 dark:border-green-800">
                <h4 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                  <span className="mr-2">💡</span>
                  정답
                </h4>
                <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
                  {currentReview.answer}
                </p>
              </div>
            )}

            {/* Control Buttons */}
            <div className="flex flex-col space-y-4">
              {!showAnswer ? (
                <div className="text-center">
                  <button
                    onClick={handleShowAnswer}
                    className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                  >
                    <span className="mr-2">👀</span>
                    정답 보기
                  </button>
                </div>
              ) : (
                <>
                  <div className="text-center mb-4">
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      이 문제를 얼마나 잘 기억하고 있나요?
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        { key: 'forgot', label: '기억 안남', emoji: '😵', color: 'from-red-400 to-red-600' },
                        { key: 'partial', label: '애매함', emoji: '😐', color: 'from-yellow-400 to-yellow-600' },
                        { key: 'remembered', label: '완벽 기억', emoji: '😊', color: 'from-green-400 to-green-600' }
                      ].map((option) => (
                        <button
                          key={option.key}
                          onClick={() => handleResponse(option.key as any)}
                          className={`flex flex-col items-center p-6 rounded-2xl shadow-lg transition-all duration-300 transform hover:scale-105 ${
                            userResponse === option.key 
                              ? `bg-gradient-to-br ${option.color} text-white shadow-xl` 
                              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:shadow-xl border border-gray-200 dark:border-gray-600'
                          }`}
                        >
                          <span className="text-3xl mb-2">{option.emoji}</span>
                          <span className="font-semibold text-lg">{option.label}</span>
                          {userResponse === option.key && (
                            <span className="text-sm mt-2 opacity-90">
                              {getNextInterval(option.key as any)}
                            </span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="text-center">
                    <button
                      onClick={handleNext}
                      className="inline-flex items-center px-8 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                    >
                      다음 문제
                      <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Auto-play controls */}
        <div className="mt-6 text-center">
          <button
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
              isAutoPlaying 
                ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            {isAutoPlaying ? (
              <>
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                자동 재생 중
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
                수동 모드
              </>
            )}
          </button>
        </div>

        {/* Benefits Summary */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              icon: '🧠',
              title: '과학적 간격',
              description: '기억 정도에 따라 다음 복습 간격을 자동 조절'
            },
            {
              icon: '📊',
              title: '학습 추적',
              description: '복습 성과를 실시간으로 기록하고 분석'
            },
            {
              icon: '🎯',
              title: '효율적 학습',
              description: '가장 잊을 가능성이 높은 시점에 복습 알림'
            }
          ].map((benefit, index) => (
            <div key={index} className="text-center p-6 bg-gradient-to-br from-gray-50 to-white dark:from-gray-800 dark:to-gray-700 rounded-2xl border border-gray-200 dark:border-gray-600">
              <div className="text-3xl mb-3">{benefit.icon}</div>
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">{benefit.title}</h4>
              <p className="text-sm text-gray-600 dark:text-gray-400">{benefit.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ReviewSimulation;