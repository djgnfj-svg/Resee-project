import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ProductionFeatures from '../components/ProductionFeatures';
import InteractiveForgettingCurve from '../components/InteractiveForgettingCurve';
import ReviewSimulation from '../components/ReviewSimulation';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [scrollY, setScrollY] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    
    // 진입 애니메이션
    setTimeout(() => setIsVisible(true), 100);
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="text-center">
      {/* Enhanced Hero Section with Parallax */}
      <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background with gradient animation */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900">
          <div className="absolute inset-0 bg-white/30 dark:bg-gray-900/50"></div>
        </div>
        
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
        <div className={`relative z-10 mx-auto max-w-4xl px-6 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <div className="text-center mb-12">
            <div className="mb-6">
              <span className="inline-flex items-center rounded-full bg-blue-50 dark:bg-blue-900/50 px-4 py-2 text-sm font-medium text-blue-700 dark:text-blue-300 ring-1 ring-inset ring-blue-700/10 dark:ring-blue-300/10">
                <svg className="mr-2 h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.236 4.53L7.53 10.53a.75.75 0 00-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
                </svg>
                과학적으로 검증된 학습법
              </span>
            </div>
            
            <h1 className="text-5xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-7xl">
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                기억력을 과학하다
              </span>
              <br />
              <span className="text-gray-900 dark:text-gray-100">
                Resee
              </span>
            </h1>
            
            <p className="mt-8 text-xl leading-8 text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
              에빙하우스 망각곡선을 기반으로 한 스마트 복습 시스템으로<br />
              <span className="font-semibold text-gray-800 dark:text-gray-200">학습 효율을 3배 향상</span>시키세요
            </p>
            
            <div className="mt-12 flex items-center justify-center gap-6 flex-wrap">
              {isAuthenticated ? (
                <Link
                  to="/dashboard"
                  className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white transition-all duration-300 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105"
                >
                  <span className="mr-2">📊</span>
                  대시보드로 이동
                  <svg className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                  </svg>
                </Link>
              ) : (
                <>
                  <Link
                    to="/register"
                    className="group relative inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-white transition-all duration-300 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-2xl shadow-xl hover:shadow-2xl transform hover:scale-105 button-press ripple animate-glow"
                  >
                    <span className="mr-2">🚀</span>
                    무료로 시작하기
                    <svg className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                    </svg>
                  </Link>
                  <Link
                    to="/login"
                    className="group inline-flex items-center justify-center px-8 py-4 text-lg font-semibold text-gray-900 dark:text-gray-100 transition-all duration-300 bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-2xl shadow-lg hover:shadow-xl border border-gray-200 dark:border-gray-700 hover:bg-white dark:hover:bg-gray-800 transform hover:scale-105 button-press glassmorphism"
                  >
                    로그인
                    <svg className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                    </svg>
                  </Link>
                </>
              )}
            </div>

            {/* Stats preview */}
            <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3 max-w-2xl mx-auto">
              {[
                { label: '기억률 향상', value: '300%', icon: '🧠' },
                { label: '학습 시간 절약', value: '65%', icon: '⏰' },
                { label: '사용자 만족도', value: '98%', icon: '❤️' }
              ].map((stat, index) => (
                <div 
                  key={index}
                  className={`text-center p-6 bg-white/60 dark:bg-gray-800/60 backdrop-blur-lg rounded-2xl border border-white/20 dark:border-gray-700/20 transition-all duration-500 hover:bg-white/80 dark:hover:bg-gray-800/80 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
                  style={{ transitionDelay: `${index * 100 + 500}ms` }}
                >
                  <div className="text-2xl mb-2">{stat.icon}</div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </div>

      {/* Interactive Forgetting Curve Section */}
      <div className="py-24 bg-white dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-6">
          <InteractiveForgettingCurve />
        </div>
      </div>

      {/* Bento Grid Features Section */}
      <div className="py-24 bg-gradient-to-br from-gray-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              혁신적인 학습 경험
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
              과학적 근거와 직관적인 인터페이스가 만나 완전히 새로운 학습 환경을 제공합니다
            </p>
          </div>

          {/* Bento Grid Layout */}
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 h-auto lg:h-[600px]">
            
            {/* Large Feature - Smart Scheduling */}
            <div className="md:col-span-2 lg:row-span-2 group relative overflow-hidden bg-gradient-to-br from-blue-500 to-purple-600 rounded-3xl p-8 text-white hover:scale-[1.02] transition-all duration-500 shadow-xl hover:shadow-2xl hover-shimmer animate-float">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div className="relative z-10">
                <div className="text-4xl mb-4">🧠</div>
                <h3 className="text-2xl font-bold mb-4">스마트 복습 스케줄링</h3>
                <p className="text-blue-100 mb-6 text-lg leading-relaxed">
                  에빙하우스 망각곡선을 기반으로 한 <br />
                  <span className="font-semibold">1일 → 3일 → 7일 → 14일 → 30일</span><br />
                  과학적 복습 일정을 자동으로 관리합니다
                </p>
                
                {/* Mini Schedule Demo */}
                <div className="bg-white/20 backdrop-blur-lg rounded-2xl p-4 mt-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-medium">다음 복습 일정</span>
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  </div>
                  <div className="space-y-2">
                    {[
                      { subject: 'React Hooks', days: '1일 후', status: 'due' },
                      { subject: 'TypeScript 기초', days: '3일 후', status: 'upcoming' },
                      { subject: 'Algorithm 개념', days: '7일 후', status: 'scheduled' }
                    ].map((item, index) => (
                      <div key={index} className="flex items-center justify-between text-sm">
                        <span className="text-white/90">{item.subject}</span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          item.status === 'due' ? 'bg-yellow-400/20 text-yellow-200' :
                          item.status === 'upcoming' ? 'bg-blue-400/20 text-blue-200' :
                          'bg-green-400/20 text-green-200'
                        }`}>
                          {item.days}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Markdown Editor Feature */}
            <div className="group bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:scale-[1.02] hover-tilt card-entrance">
              <div className="text-3xl mb-4">✍️</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                마크다운 에디터
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
                실시간 미리보기와 함께 마크다운으로 학습 내용을 체계적으로 정리
              </p>
              
              {/* Mini Editor Demo */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-xs font-mono">
                <div className="text-blue-600 dark:text-blue-400"># React 컴포넌트</div>
                <div className="text-gray-500 dark:text-gray-300">- **함수형 컴포넌트**</div>
                <div className="text-gray-500 dark:text-gray-300">- useState 훅 사용</div>
                <div className="w-full h-1 bg-blue-200 dark:bg-blue-800 rounded mt-2 animate-pulse"></div>
              </div>
            </div>

            {/* Analytics Feature */}
            <div className="group bg-gradient-to-br from-green-400 to-teal-500 rounded-3xl p-6 text-white hover:scale-[1.02] transition-all duration-300 shadow-xl hover:shadow-2xl hover-glow animate-pulse-slow card-entrance">
              <div className="text-3xl mb-4">📊</div>
              <h3 className="text-xl font-bold mb-3">학습 분석</h3>
              <p className="text-green-100 mb-4 text-sm">
                복습 성공률과 학습 패턴을 시각화
              </p>
              
              {/* Mini Chart */}
              <div className="bg-white/20 backdrop-blur-lg rounded-lg p-3">
                <div className="flex items-end space-x-1 h-8">
                  {[4, 7, 3, 8, 5, 6, 9].map((height, index) => (
                    <div 
                      key={index}
                      className="bg-white/60 rounded-sm flex-1 transition-all duration-300"
                      style={{ height: `${height * 4}px` }}
                    ></div>
                  ))}
                </div>
                <div className="text-xs text-center mt-2 text-green-100">주간 복습 성과</div>
              </div>
            </div>

            {/* Category Management */}
            <div className="group bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-600 hover:scale-[1.02] hover-lift card-entrance">
              <div className="text-3xl mb-4">🗂️</div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                카테고리 관리
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
                주제별로 체계적인 학습 자료 분류
              </p>
              
              {/* Category Tags */}
              <div className="flex flex-wrap gap-2">
                {['프로그래밍', '언어학습', '과학'].map((category, index) => (
                  <span 
                    key={index}
                    className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full text-xs font-medium"
                  >
                    {category}
                  </span>
                ))}
              </div>
            </div>

            {/* Progress Tracking */}
            <div className="group bg-gradient-to-br from-orange-400 to-pink-500 rounded-3xl p-6 text-white hover:scale-[1.02] transition-all duration-300 shadow-xl hover:shadow-2xl animate-heartbeat card-entrance">
              <div className="text-3xl mb-4">🎯</div>
              <h3 className="text-xl font-bold mb-3">진도 추적</h3>
              <p className="text-orange-100 mb-4 text-sm">
                학습 진도와 목표 달성률을 실시간 모니터링
              </p>
              
              {/* Progress Circles */}
              <div className="flex justify-around">
                <div className="text-center">
                  <div className="w-12 h-12 border-4 border-white/30 border-t-white rounded-full animate-spin mx-auto mb-1"></div>
                  <div className="text-xs">완료율</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">85%</div>
                  <div className="text-xs">목표 달성</div>
                </div>
              </div>
            </div>

            {/* Offline Support */}
            <div className="md:col-span-2 group bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl p-6 text-white hover:scale-[1.02] transition-all duration-300 shadow-xl hover:shadow-2xl glassmorphism-dark card-entrance">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl mb-2">📱</div>
                  <h3 className="text-xl font-bold mb-2">PWA & 오프라인 지원</h3>
                  <p className="text-indigo-100 text-sm">
                    인터넷 연결 없이도 학습을 계속할 수 있는 Progressive Web App
                  </p>
                </div>
                <div className="text-right">
                  <div className="w-16 h-16 bg-white/20 backdrop-blur-lg rounded-2xl flex items-center justify-center mb-2">
                    <svg className="w-8 h-8" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2L2 7v10c0 5.55 3.84 9.739 9 11 5.16-1.261 9-5.45 9-11V7l-10-5z"/>
                    </svg>
                  </div>
                  <div className="text-xs text-indigo-200">항상 접근 가능</div>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Review Simulation Section */}
      <div className="py-24 bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-800 dark:via-gray-900 dark:to-indigo-900">
        <div className="max-w-7xl mx-auto px-6">
          <ReviewSimulation />
        </div>
      </div>

      {/* Add production features section */}
      <ProductionFeatures />
    </div>
  );
};

export default HomePage;