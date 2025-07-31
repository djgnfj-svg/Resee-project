import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  SparklesIcon,
  BookOpenIcon,
  ClockIcon,
  ChartBarIcon,
  ArrowRightIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

const OnboardingPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const steps = [
    {
      id: 0,
      title: `안녕하세요, ${user?.username || user?.email.split('@')[0]}님! 🎉`,
      subtitle: 'Resee에 오신 것을 환영합니다',
      description: '과학적인 간격 반복 학습으로 더 효과적으로 기억하세요.',
      icon: SparklesIcon,
      color: 'from-blue-500 to-purple-600',
    },
    {
      id: 1,
      title: '학습 콘텐츠 만들기',
      subtitle: '지식을 체계적으로 정리하세요',
      description: '배운 내용을 마크다운 형식으로 작성하고 카테고리별로 관리할 수 있습니다.',
      icon: BookOpenIcon,
      color: 'from-green-500 to-blue-500',
    },
    {
      id: 2,
      title: '스마트 복습 시스템',
      subtitle: '에빙하우스 망각 곡선 기반',
      description: '1일, 3일, 7일, 14일, 30일 간격으로 자동 복습 스케줄이 생성됩니다.',
      icon: ClockIcon,
      color: 'from-purple-500 to-pink-500',
    },
    {
      id: 3,
      title: '학습 분석 대시보드',
      subtitle: '성과를 한눈에 확인하세요',
      description: '학습 패턴, 성취도, 카테고리별 성과를 시각적으로 분석할 수 있습니다.',
      icon: ChartBarIcon,
      color: 'from-orange-500 to-red-500',
    },
  ];

  useEffect(() => {
    // 자동 진행 (각 단계별 3초)
    const timer = setTimeout(() => {
      if (currentStep < steps.length - 1) {
        setCompletedSteps(prev => [...prev, currentStep]);
        setCurrentStep(currentStep + 1);
      }
    }, 3000);

    return () => clearTimeout(timer);
  }, [currentStep, steps.length]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCompletedSteps(prev => [...prev, currentStep]);
      setCurrentStep(currentStep + 1);
    }
  };

  const handleSkip = () => {
    navigate('/dashboard');
  };

  const handleGetStarted = () => {
    navigate('/content');
  };

  const currentStepData = steps[currentStep];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center py-12 px-4">
      <div className="max-w-2xl w-full">
        {/* 헤더 */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <div className={`w-16 h-16 bg-gradient-to-r ${currentStepData.color} rounded-full flex items-center justify-center shadow-lg`}>
              <currentStepData.icon className="w-8 h-8 text-white" />
            </div>
          </div>
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            {currentStepData.title}
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-4">
            {currentStepData.subtitle}
          </p>
        </div>

        {/* 진행 표시기 */}
        <div className="flex justify-center mb-8">
          <div className="flex items-center space-x-4">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300 ${
                    completedSteps.includes(index)
                      ? 'bg-green-500 text-white shadow-lg'
                      : index === currentStep
                      ? 'bg-blue-500 text-white shadow-lg animate-pulse'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {completedSteps.includes(index) ? (
                    <CheckCircleIcon className="w-6 h-6" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`w-12 h-0.5 transition-all duration-300 ${
                      completedSteps.includes(index) ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-8 border border-gray-200 dark:border-gray-700 mb-8">
          <div className="text-center space-y-6">
            <div className={`w-24 h-24 bg-gradient-to-r ${currentStepData.color} rounded-2xl flex items-center justify-center mx-auto shadow-lg transform hover:scale-105 transition-transform duration-300`}>
              <currentStepData.icon className="w-12 h-12 text-white" />
            </div>
            
            <div className="space-y-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {currentStepData.title}
              </h2>
              
              <p className="text-lg text-gray-600 dark:text-gray-400 leading-relaxed max-w-lg mx-auto">
                {currentStepData.description}
              </p>
            </div>

            {/* 특별한 첫 번째 단계 콘텐츠 */}
            {currentStep === 0 && (
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-6 border border-blue-200 dark:border-blue-800">
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    지금 시작할 수 있는 것들:
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span className="text-gray-700 dark:text-gray-300">첫 번째 학습 내용 추가</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span className="text-gray-700 dark:text-gray-300">카테고리 생성</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500" />
                      <span className="text-gray-700 dark:text-gray-300">즉시 복습 시작</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 마지막 단계 특별 콘텐츠 */}
            {currentStep === steps.length - 1 && (
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-xl p-6 border border-green-200 dark:border-green-800">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                    🚀 모든 준비가 완료되었습니다!
                  </h3>
                  <p className="text-gray-700 dark:text-gray-300">
                    이제 첫 번째 학습 콘텐츠를 만들고 효과적인 복습 여정을 시작해보세요.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="flex justify-center space-x-4">
          <button
            onClick={handleSkip}
            className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            건너뛰기
          </button>
          
          {currentStep < steps.length - 1 ? (
            <button
              onClick={handleNext}
              className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all flex items-center space-x-2 shadow-lg"
            >
              <span>다음</span>
              <ArrowRightIcon className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleGetStarted}
              className="px-8 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-lg hover:from-green-600 hover:to-blue-600 transition-all flex items-center space-x-2 shadow-lg animate-pulse"
            >
              <span>🎯 시작하기</span>
              <ArrowRightIcon className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* 자동 진행 표시 */}
        <div className="text-center mt-6">
          <div className="inline-flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping"></div>
            <span>자동으로 다음 단계로 진행됩니다 (3초)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingPage;