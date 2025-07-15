import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { analyticsAPI } from '../utils/api';
import { DashboardData } from '../types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar } from 'recharts';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: dashboardData, isLoading, error } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
    onError: (error: any) => {
      toast.error(error.userMessage || '대시보드 데이터를 불러오는데 실패했습니다.');
    },
  });

  const { data: reviewStats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['reviewStats'],
    queryFn: analyticsAPI.getReviewStats,
    onError: (error: any) => {
      toast.error(error.userMessage || '통계 데이터를 불러오는데 실패했습니다.');
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

  // Chart colors
  const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  // Process review stats for charts
  const processedDailyData = reviewStats?.daily_reviews?.map((item: any) => ({
    date: new Date(item.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    count: item.count
  })) || [];

  const processedResultData = reviewStats?.result_distribution?.map((item: any) => ({
    name: item.result === 'remembered' ? '기억함' : 
          item.result === 'partial' ? '애매함' : '모름',
    value: item.count
  })) || [];

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
        {stats.map((stat, index) => {
          const icons = ['🎯', '⏰', '📖', '🎉'];
          const gradients = [
            'from-blue-500 to-blue-600',
            'from-yellow-500 to-orange-500', 
            'from-green-500 to-green-600',
            'from-purple-500 to-purple-600'
          ];
          
          return (
            <div
              key={stat.name}
              className="relative overflow-hidden rounded-2xl bg-white p-6 shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
            >
              <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${gradients[index]} rounded-full opacity-10 transform translate-x-6 -translate-y-6`}></div>
              <div className="relative">
                <div className="flex items-center justify-between">
                  <div className="text-2xl mb-2">{icons[index]}</div>
                  <div className={`text-2xl font-bold bg-gradient-to-r ${gradients[index]} bg-clip-text text-transparent`}>
                    {stat.value}{stat.unit}
                  </div>
                </div>
                <h3 className="text-gray-700 font-semibold text-lg">{stat.name}</h3>
                <div className={`h-2 bg-gray-100 rounded-full mt-3 overflow-hidden`}>
                  <div 
                    className={`h-full bg-gradient-to-r ${gradients[index]} rounded-full transition-all duration-500`}
                    style={{width: `${Math.min(stat.value, 100)}%`}}
                  ></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions & Tips */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mb-8">
        <div className="bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center mb-4">
            <div className="text-2xl mr-3">⚡</div>
            <h3 className="text-xl font-bold text-gray-900">빠른 액션</h3>
          </div>
          <div className="space-y-3">
            <button 
              onClick={() => navigate('/content')}
              className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4 text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105"
            >
              <span className="relative z-10 flex items-center justify-center">
                <span className="mr-2">📝</span>
                새 콘텐츠 추가
              </span>
            </button>
            <button 
              onClick={() => navigate('/review')}
              className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-r from-green-500 to-teal-600 px-6 py-4 text-white font-semibold hover:from-green-600 hover:to-teal-700 transition-all duration-300 transform hover:scale-105"
            >
              <span className="relative z-10 flex items-center justify-center">
                <span className="mr-2">🎯</span>
                오늘의 복습 시작
              </span>
            </button>
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

      {/* Charts Section */}
      {!statsLoading && reviewStats && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Daily Reviews Chart */}
          <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <div className="flex items-center mb-6">
              <div className="text-2xl mr-3">📊</div>
              <h3 className="text-xl font-bold text-gray-900">일별 복습 현황</h3>
              <span className="ml-auto text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">최근 30일</span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={processedDailyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#666', fontSize: 12 }}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#666', fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="url(#colorGradient)" 
                  strokeWidth={3}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6, fill: '#3B82F6' }}
                />
                <defs>
                  <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#3B82F6" />
                    <stop offset="100%" stopColor="#8B5CF6" />
                  </linearGradient>
                </defs>
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Review Results Distribution */}
          <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <div className="flex items-center mb-6">
              <div className="text-2xl mr-3">🎯</div>
              <h3 className="text-xl font-bold text-gray-900">복습 결과 분포</h3>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={processedResultData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {processedResultData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Weekly Performance Chart */}
      {!statsLoading && reviewStats && (
        <div className="mt-8">
          <div className="bg-white rounded-2xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300">
            <div className="flex items-center mb-6">
              <div className="text-2xl mr-3">📈</div>
              <h3 className="text-xl font-bold text-gray-900">주간 복습 성과</h3>
              <span className="ml-auto text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">최근 7일</span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={processedDailyData.slice(-7)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="date" 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#666', fontSize: 12 }}
                />
                <YAxis 
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#666', fontSize: 12 }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: 'none',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0,0,0,0.1)'
                  }}
                />
                <Bar 
                  dataKey="count" 
                  fill="url(#barGradient)" 
                  radius={[4, 4, 0, 0]}
                />
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10B981" />
                    <stop offset="100%" stopColor="#059669" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;