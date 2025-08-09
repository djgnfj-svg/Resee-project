import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  BookOpenIcon, 
  ClockIcon, 
  AcademicCapIcon,
  PlayIcon,
  ChartBarIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import apiClient from '../utils/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';

interface WeeklyTest {
  id: number;
  week_start_date: string;
  week_end_date: string;
  total_questions: number;
  completed_questions: number;
  correct_answers: number;
  score: number | null;
  time_limit_minutes: number;
  started_at: string | null;
  completed_at: string | null;
  difficulty_distribution: Record<string, number>;
  content_coverage: number[];
  weak_areas: string[];
  improvement_from_last_week: number | null;
  status: 'draft' | 'ready' | 'in_progress' | 'completed' | 'expired';
  accuracy_rate: number;
  completion_rate: number;
  time_spent_minutes: number;
  created_at: string;
}

interface CreateTestData {
  time_limit_minutes: number;
  difficulty_distribution?: Record<string, number>;
}

const WeeklyTestPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testConfig, setTestConfig] = useState<CreateTestData>({
    time_limit_minutes: 30
  });

  // 주간 시험 목록 조회
  const { data: tests, isLoading, error } = useQuery({
    queryKey: ['weekly-tests'],
    queryFn: async (): Promise<WeeklyTest[]> => {
      const response = await apiClient.get('/api/ai-review/weekly-test/');
      return response.data;
    }
  });

  // 주간 시험 생성
  const createTestMutation = useMutation({
    mutationFn: async (data: CreateTestData) => {
      const response = await apiClient.post('/api/ai-review/weekly-test/', data);
      return response.data;
    },
    onSuccess: () => {
      toast.success('주간 시험이 생성되었습니다!');
      setShowCreateModal(false);
      queryClient.invalidateQueries({ queryKey: ['weekly-tests'] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '시험 생성에 실패했습니다.';
      toast.error(message);
    }
  });

  // 주간 시험 시작
  const startTestMutation = useMutation({
    mutationFn: async (testId: number) => {
      const response = await apiClient.post('/api/ai-review/weekly-test/start/', {
        test_id: testId
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('주간 시험이 시작되었습니다!');
      navigate(`/weekly-test/${data.test.id}/take`);
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '시험 시작에 실패했습니다.';
      toast.error(message);
    }
  });

  const handleCreateTest = () => {
    createTestMutation.mutate(testConfig);
  };

  const handleStartTest = (testId: number) => {
    startTestMutation.mutate(testId);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: WeeklyTest['status']) => {
    const badges = {
      draft: 'bg-gray-100 text-gray-800',
      ready: 'bg-green-100 text-green-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-purple-100 text-purple-800',
      expired: 'bg-red-100 text-red-800'
    };

    const labels = {
      draft: '준비중',
      ready: '시작가능',
      in_progress: '진행중',
      completed: '완료',
      expired: '만료'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badges[status]}`}>
        {labels[status]}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">오류 발생</h3>
          <p className="mt-1 text-sm text-gray-500">시험 목록을 불러올 수 없습니다.</p>
        </div>
      </div>
    );
  }

  const currentTest = tests?.find(test => test.status === 'ready' || test.status === 'in_progress');
  const completedTests = tests?.filter(test => test.status === 'completed') || [];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <AcademicCapIcon className="h-8 w-8 text-indigo-600 mr-3" />
                주간 종합 시험
              </h1>
              <p className="mt-2 text-gray-600">
                한 주 동안 학습한 내용을 종합적으로 평가하고 취약점을 파악해보세요
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors font-medium"
            >
              새 시험 생성
            </button>
          </div>
        </div>

        {/* Current Test */}
        {currentTest && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border-l-4 border-indigo-500">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <BookOpenIcon className="h-6 w-6 text-indigo-600 mr-2" />
                <h2 className="text-xl font-semibold text-gray-900">
                  {formatDate(currentTest.week_start_date)} - {formatDate(currentTest.week_end_date)} 주간 시험
                </h2>
                {getStatusBadge(currentTest.status)}
              </div>
              {currentTest.status === 'ready' && (
                <button
                  onClick={() => handleStartTest(currentTest.id)}
                  disabled={startTestMutation.isPending}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center disabled:opacity-50"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  {startTestMutation.isPending ? '시작 중...' : '시험 시작'}
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{currentTest.total_questions}</div>
                <div className="text-sm text-gray-600">총 문제 수</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-900 flex items-center">
                  <ClockIcon className="h-5 w-5 mr-1" />
                  {currentTest.time_limit_minutes === 0 ? '무제한' : `${currentTest.time_limit_minutes}분`}
                </div>
                <div className="text-sm text-gray-600">제한 시간</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{currentTest.content_coverage.length}</div>
                <div className="text-sm text-gray-600">출제 콘텐츠</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-indigo-600">
                  {currentTest.completion_rate.toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600">진행률</div>
              </div>
            </div>

            {/* 난이도 분포 */}
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">난이도 분포</h3>
              <div className="flex space-x-4">
                {Object.entries(currentTest.difficulty_distribution).map(([level, count]) => (
                  <div key={level} className="flex items-center">
                    <div className={`w-3 h-3 rounded mr-2 ${
                      level === 'easy' ? 'bg-green-400' :
                      level === 'medium' ? 'bg-yellow-400' : 'bg-red-400'
                    }`}></div>
                    <span className="text-sm text-gray-600">
                      {level === 'easy' ? '쉬움' : level === 'medium' ? '보통' : '어려움'}: {count}문항
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Completed Tests History */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center mb-6">
            <ChartBarIcon className="h-6 w-6 text-gray-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">시험 기록</h2>
          </div>

          {completedTests.length === 0 ? (
            <div className="text-center py-12">
              <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">완료된 시험이 없습니다</h3>
              <p className="mt-1 text-sm text-gray-500">
                첫 번째 주간 시험을 만들어보세요!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {completedTests.map((test) => (
                <div key={test.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-gray-900">
                      {formatDate(test.week_start_date)} - {formatDate(test.week_end_date)}
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`text-lg font-bold ${
                        test.score && test.score >= 80 ? 'text-green-600' :
                        test.score && test.score >= 60 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {test.score?.toFixed(0)}점
                      </span>
                      {getStatusBadge(test.status)}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
                    <div>
                      정답률: <span className="font-medium">{test.accuracy_rate.toFixed(0)}%</span>
                    </div>
                    <div>
                      소요시간: <span className="font-medium">{test.time_spent_minutes}분</span>
                    </div>
                    <div>
                      문제수: <span className="font-medium">{test.completed_questions}/{test.total_questions}</span>
                    </div>
                  </div>

                  {test.improvement_from_last_week !== null && (
                    <div className="mt-2 text-sm">
                      <span className={`font-medium ${
                        test.improvement_from_last_week > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        지난 주 대비 {test.improvement_from_last_week > 0 ? '+' : ''}{test.improvement_from_last_week.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Test Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">새 주간 시험 생성</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  시험 시간
                </label>
                <select
                  value={testConfig.time_limit_minutes}
                  onChange={(e) => setTestConfig(prev => ({ ...prev, time_limit_minutes: Number(e.target.value) }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                >
                  <option value={30}>30분</option>
                  <option value={60}>60분</option>
                  <option value={0}>무제한</option>
                </select>
              </div>

              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="text-sm text-blue-800">
                  <strong>자동 설정:</strong>
                  <ul className="mt-1 space-y-1 text-xs">
                    <li>• 이번 주 학습한 콘텐츠에서 문제 출제</li>
                    <li>• 난이도: 쉬움 30%, 보통 50%, 어려움 20%</li>
                    <li>• 총 15문제 (AI가 자동 생성)</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleCreateTest}
                disabled={createTestMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {createTestMutation.isPending ? '생성 중...' : '시험 생성'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WeeklyTestPage;