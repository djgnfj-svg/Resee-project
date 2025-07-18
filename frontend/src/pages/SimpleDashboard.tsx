import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../utils/api';
import { DashboardData } from '../types';
import LoadingSpinner from '../components/LoadingSpinner';

const SimpleDashboard: React.FC = () => {
  const { data: dashboardData, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
    onError: (error: any) => {
      alert('Error: ' + (error.userMessage || '대시보드 데이터를 불러오는데 실패했습니다.'));
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" text="대시보드 데이터를 불러오는 중..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto mt-8 bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-4xl mb-4">😞</div>
        <h3 className="text-lg font-semibold text-red-800 mb-2">데이터를 불러올 수 없습니다</h3>
        <p className="text-sm text-red-600 mb-4">
          대시보드 데이터를 불러오는데 문제가 발생했습니다.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    );
  }

  const stats = [
    {
      name: '오늘의 복습',
      value: dashboardData?.today_reviews || 0,
      unit: '개',
      icon: '🎯',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: '복습 연속일',
      value: dashboardData?.streak_days || 0,
      unit: '일',
      icon: '🔥',
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    },
    {
      name: '전체 콘텐츠',
      value: dashboardData?.total_content || 0,
      unit: '개',
      icon: '📖',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      name: '복습 성공률',
      value: dashboardData?.success_rate || 0,
      unit: '%',
      icon: '🎉',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div>
      {/* Hero Section */}
      <div className="mb-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">안녕하세요! 📚</h1>
            <p className="text-blue-100 text-lg">
              오늘도 성실하게 학습하는 당신을 응원합니다.
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">
              {new Date().toLocaleDateString('ko-KR', { 
                month: 'long', 
                day: 'numeric', 
                weekday: 'short' 
              })}
            </div>
            <div className="text-blue-100 mt-1">
              {new Date().toLocaleTimeString('ko-KR', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        {stats.map((stat, index) => (
          <div
            key={`dashboard-stat-${index}`}
            className="relative overflow-hidden rounded-2xl bg-white p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div className="text-2xl mb-2">{stat.icon}</div>
              <div className="text-right">
                <div className={`text-2xl font-bold ${stat.color}`}>
                  {stat.value}{stat.unit}
                </div>
              </div>
            </div>
            <h3 className="text-gray-700 font-semibold text-lg">{stat.name}</h3>
            <div className="h-2 bg-gray-100 rounded-full mt-3 overflow-hidden">
              <div 
                className={`h-full ${stat.bgColor} rounded-full transition-all duration-500`}
                style={{width: `${Math.min(stat.value, 100)}%`}}
              ></div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions & Tips */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center mb-4">
            <div className="text-2xl mr-3">⚡</div>
            <h3 className="text-xl font-bold text-gray-900">빠른 액션</h3>
          </div>
          <div className="space-y-3">
            <a 
              href="/content"
              className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4 text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 block text-center"
            >
              <span className="mr-2">📝</span>
              새 콘텐츠 추가
            </a>
            <a 
              href="/review"
              className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-green-500 to-teal-600 px-6 py-4 text-white font-semibold hover:from-green-600 hover:to-teal-700 transition-all duration-300 transform hover:scale-105 block text-center"
            >
              <span className="mr-2">🎯</span>
              오늘의 복습 시작
            </a>
          </div>
        </div>

        <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center mb-4">
            <div className="text-2xl mr-3">💡</div>
            <h3 className="text-xl font-bold text-gray-900">학습 팁</h3>
          </div>
          <div className="space-y-3">
            <div className="flex items-start">
              <div className="text-green-500 mr-3 mt-1">•</div>
              <p className="text-gray-700">복습은 하루에 조금씩이라도 꾸준히 하는 것이 중요합니다.</p>
            </div>
            <div className="flex items-start">
              <div className="text-yellow-500 mr-3 mt-1">•</div>
              <p className="text-gray-700">기억이 애매하다면 '애매함'으로 표시하여 더 자주 복습하세요.</p>
            </div>
            <div className="flex items-start">
              <div className="text-purple-500 mr-3 mt-1">•</div>
              <p className="text-gray-700">카테고리와 태그를 활용하여 체계적으로 정리하세요.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Analytics Notice */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-200">
        <div className="flex items-center mb-4">
          <div className="text-2xl mr-3">📈</div>
          <h3 className="text-xl font-bold text-gray-900">향상된 분석 기능</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-2">🎯 주간 복습 성과</h4>
            <p className="text-sm text-gray-600">최근 4주간의 복습 성과와 성공률을 한 눈에 확인할 수 있습니다.</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-2">📊 일별 복습 현황</h4>
            <p className="text-sm text-gray-600">일별 복습 횟수와 성공률 추이를 시각적으로 분석합니다.</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-2">🎭 복습 결과 분포</h4>
            <p className="text-sm text-gray-600">기억함/애매함/모름의 분포를 30일/전체 기간별로 확인합니다.</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-2">🔥 연속 학습 추적</h4>
            <p className="text-sm text-gray-600">연속 복습일 수와 학습 지속성을 트래킹합니다.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleDashboard;