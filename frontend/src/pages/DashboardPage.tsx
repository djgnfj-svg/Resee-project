import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { analyticsAPI } from '../utils/api';
import { DashboardData } from '../types';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: dashboardData, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4">
        <div className="text-sm text-red-700">
          대시보드 데이터를 불러오는데 실패했습니다.
        </div>
      </div>
    );
  }

  const stats = [
    {
      name: '오늘의 복습',
      value: dashboardData?.today_reviews || 0,
      unit: '개',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      name: '대기 중인 복습',
      value: dashboardData?.pending_reviews || 0,
      unit: '개',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    },
    {
      name: '전체 콘텐츠',
      value: dashboardData?.total_content || 0,
      unit: '개',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      name: '복습 성공률',
      value: dashboardData?.success_rate || 0,
      unit: '%',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">대시보드</h1>
        <p className="mt-2 text-gray-600">
          학습 진행 상황과 복습 일정을 한눈에 확인하세요.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="overflow-hidden rounded-lg bg-white px-4 py-5 shadow sm:p-6"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`h-8 w-8 rounded-md ${stat.bgColor} flex items-center justify-center`}>
                  <div className={`h-3 w-3 rounded-full ${stat.color.replace('text-', 'bg-')}`}></div>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className={`text-lg font-medium ${stat.color}`}>
                    {stat.value}{stat.unit}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900">빠른 액션</h3>
            <div className="mt-6 space-y-4">
              <button 
                onClick={() => navigate('/content')}
                className="w-full rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white hover:bg-primary-700"
              >
                새 콘텐츠 추가
              </button>
              <button 
                onClick={() => navigate('/review')}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-50"
              >
                오늘의 복습 시작
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg bg-white shadow">
          <div className="p-6">
            <h3 className="text-lg font-medium text-gray-900">학습 팁</h3>
            <div className="mt-4 text-sm text-gray-600">
              <p>
                • 복습은 하루에 조금씩이라도 꾸준히 하는 것이 중요합니다.
              </p>
              <p className="mt-2">
                • 기억이 애매하다면 '애매함'으로 표시하여 더 자주 복습하세요.
              </p>
              <p className="mt-2">
                • 카테고리와 태그를 활용하여 체계적으로 정리하세요.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;