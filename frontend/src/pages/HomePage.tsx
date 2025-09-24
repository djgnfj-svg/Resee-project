import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [scrollY, setScrollY] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Redirect authenticated users to dashboard
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
      return;
    }

    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);

    // 진입 애니메이션
    setTimeout(() => setIsVisible(true), 100);

    return () => window.removeEventListener('scroll', handleScroll);
  }, [isAuthenticated, navigate]);

  return (
    <div className="text-center">
      {/* Main Hero Section - Automation Focused */}
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background with gradient animation */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-indigo-100 to-purple-100 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900"></div>

        {/* Floating elements for visual interest */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div
            className="absolute top-1/4 left-1/4 w-72 h-72 bg-gradient-to-r from-blue-400/20 to-purple-400/20 rounded-full blur-3xl"
            style={{ transform: `translateY(${scrollY * 0.5}px)` }}
          ></div>
          <div
            className="absolute top-3/4 right-1/4 w-96 h-96 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-3xl"
            style={{ transform: `translateY(${scrollY * -0.3}px)` }}
          ></div>
        </div>

        {/* Main content */}
        <div className={`relative z-10 mx-auto max-w-5xl px-6 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold tracking-tight sm:text-7xl">
              <span className="bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
                복습을 자동화하다
              </span>
            </h1>

            <p className="mt-8 text-xl leading-8 text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
              <span className="font-semibold text-gray-800 dark:text-gray-200">더 이상 복습 일정을 고민하지 마세요</span><br />
              주기적 복습과 AI로 내용검증, 카테고리별 AI가 만든 시험으로 복습에 들어가는 시간을 단축하세요
            </p>

            <div className="mt-12 flex items-center justify-center">
              <Link
                to="/register"
                className="group relative inline-flex items-center justify-center px-10 py-5 text-xl font-bold text-white transition-all duration-300 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 button-press ripple animate-glow"
              >
                <span className="mr-3">🚀</span>
                무료로 시작하기
                <svg className="ml-3 h-6 w-6 transition-transform group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                </svg>
              </Link>
            </div>

            {/* 3 Main Automation Features */}
            <div className="mt-24 grid grid-cols-1 gap-8 md:grid-cols-3 max-w-5xl mx-auto">
              {[
                {
                  label: '자동 주기적 복습',
                  description: '에빙하우스 망각곡선 기반으로 최적의 복습 주기를 자동으로 설정하고 알려드립니다',
                  icon: '🔄',
                  color: 'from-blue-500 to-indigo-600'
                },
                {
                  label: '자동 AI 시험',
                  description: 'AI가 학습 내용을 분석하여 자동으로 시험 문제를 생성하고 평가합니다',
                  icon: '🤖',
                  color: 'from-green-500 to-teal-600'
                },
                {
                  label: '자동 AI 내용 검증',
                  description: 'AI가 학습 자료의 정확성을 검증하고 개선 사항을 자동으로 제안합니다',
                  icon: '✅',
                  color: 'from-purple-500 to-pink-600'
                }
              ].map((feature, index) => (
                <div
                  key={index}
                  className={`group relative overflow-hidden bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-xl hover:shadow-2xl transition-all duration-500 border border-gray-200 dark:border-gray-700 hover:scale-[1.02] ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
                  style={{ transitionDelay: `${index * 150 + 300}ms` }}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
                  <div className="relative z-10">
                    <div className={`inline-flex items-center justify-center w-16 h-16 mb-6 rounded-2xl bg-gradient-to-r ${feature.color} text-white text-3xl shadow-xl`}>
                      {feature.icon}
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">{feature.label}</h3>
                    <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>

          </div>
        </div>

      </div>



    </div>
  );
};

export default HomePage;