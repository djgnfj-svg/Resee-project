import React, { useState } from 'react';
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
import { aiReviewAPI } from '../utils/api';
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
  category_id?: number | null;
  time_limit_minutes: number;
  adaptive_mode?: boolean;
  total_questions?: number;
}

interface Category {
  id: number;
  name: string;
  description?: string;
}

const WeeklyTestPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testConfig, setTestConfig] = useState<CreateTestData>({
    category_id: null,
    time_limit_minutes: 30,
    adaptive_mode: true,
    total_questions: 10
  });

  // 카테고리 목록 조회
  const { data: categories } = useQuery({
    queryKey: ['weekly-test-categories'],
    queryFn: async () => {
      const response = await fetch('/api/ai-review/weekly-test/categories/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (!response.ok) throw new Error('카테고리 조회 실패');
      const data = await response.json();
      return data.categories as Category[];
    }
  });

  // 주간 시험 목록 조회
  const { data: tests, isLoading, error } = useQuery({
    queryKey: ['weekly-tests'],
    queryFn: aiReviewAPI.getWeeklyTest
  });

  // 주간 시험 생성
  const createTestMutation = useMutation({
    mutationFn: async (data: any) => {
      // AI 기능 준비중 메시지 표시
      toast('🚧 AI 기능은 현재 준비 중입니다');
      throw new Error('AI 기능 준비중');
    },
    onSuccess: () => {
      toast.success('주간 시험이 생성되었습니다!');
      setShowCreateModal(false);
      queryClient.invalidateQueries({ queryKey: ['weekly-tests'] });
    },
    onError: (error: any) => {
      // 준비중 에러는 별도 메시지 표시 안함
      if (error.message !== 'AI 기능 준비중') {
        const message = error.response?.data?.detail || '시험 생성에 실패했습니다.';
        toast.error(message);
      }
    }
  });

  // 주간 시험 시작
  const startTestMutation = useMutation({
    mutationFn: async (testId: number) => {
      // AI 기능 준비중 메시지 표시
      toast('🚧 AI 기능은 현재 준비 중입니다');
      throw new Error('AI 기능 준비중');
    },
    onSuccess: (data: any) => {
      toast.success('주간 시험이 시작되었습니다!');
      navigate(`/weekly-test/${data.test.id}/take`);
    },
    onError: (error: any) => {
      // 준비중 에러는 별도 메시지 표시 안함
      if (error.message !== 'AI 기능 준비중') {
        const message = error.response?.data?.detail || '시험 시작에 실패했습니다.';
        toast.error(message);
      }
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
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
      ready: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200',
      completed: 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200',
      expired: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
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
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">오류 발생</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">시험 목록을 불러올 수 없습니다.</p>
        </div>
      </div>
    );
  }

  const testsArray = Array.isArray(tests) ? tests : [];
  const currentTest = testsArray.find((test: WeeklyTest) => test.status === 'ready' || test.status === 'in_progress');
  const completedTests = testsArray.filter((test: WeeklyTest) => test.status === 'completed');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <AcademicCapIcon className="h-8 w-8 text-indigo-600 dark:text-indigo-400 mr-3" />
                주간 종합 시험
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-300">
                한 주 동안 학습한 내용을 종합적으로 평가하고 취약점을 파악해보세요
              </p>
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-indigo-600 dark:bg-indigo-500 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors font-medium"
            >
              새 시험 생성
            </button>
          </div>
        </div>

        {/* Current Test */}
        {currentTest && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8 border-l-4 border-indigo-500 dark:border-indigo-400">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center">
                <BookOpenIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400 mr-2" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  {formatDate(currentTest.week_start_date)} - {formatDate(currentTest.week_end_date)} 주간 시험
                </h2>
                {getStatusBadge(currentTest.status)}
              </div>
              {currentTest.status === 'ready' && (
                <button
                  onClick={() => handleStartTest(currentTest.id)}
                  disabled={startTestMutation.isPending}
                  className="bg-green-600 dark:bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-colors font-medium flex items-center disabled:opacity-50"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  {startTestMutation.isPending ? '시작 중...' : '시험 시작'}
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{currentTest.total_questions}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">총 문제 수</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                  <ClockIcon className="h-5 w-5 mr-1" />
                  {currentTest.time_limit_minutes === 0 ? '무제한' : `${currentTest.time_limit_minutes}분`}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">제한 시간</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{currentTest.content_coverage.length}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">출제 콘텐츠</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
                  {currentTest.completion_rate.toFixed(0)}%
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">진행률</div>
              </div>
            </div>

            {/* 난이도 분포 */}
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">난이도 분포</h3>
              <div className="flex space-x-4">
                {Object.entries(currentTest.difficulty_distribution as Record<string, number>).map(([level, count]) => (
                  <div key={level} className="flex items-center">
                    <div className={`w-3 h-3 rounded mr-2 ${
                      level === 'easy' ? 'bg-green-400' :
                      level === 'medium' ? 'bg-yellow-400' : 'bg-red-400'
                    }`} />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {level === 'easy' ? '쉬움' : level === 'medium' ? '보통' : '어려움'}: {count}문항
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Completed Tests History */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center mb-6">
            <ChartBarIcon className="h-6 w-6 text-gray-600 dark:text-gray-400 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">시험 기록</h2>
          </div>

          {completedTests.length === 0 ? (
            <div className="text-center py-12">
              <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">완료된 시험이 없습니다</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                첫 번째 주간 시험을 만들어보세요!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {completedTests.map((test: WeeklyTest) => (
                <div key={test.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      {formatDate(test.week_start_date)} - {formatDate(test.week_end_date)}
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={`text-lg font-bold ${
                        test.score && test.score >= 80 ? 'text-green-600 dark:text-green-400' :
                        test.score && test.score >= 60 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {test.score?.toFixed(0)}점
                      </span>
                      {getStatusBadge(test.status)}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400">
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
                        test.improvement_from_last_week > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
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
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-md w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">새 주간 시험 생성</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  카테고리 선택
                </label>
                <select
                  value={testConfig.category_id || ''}
                  onChange={(e) => setTestConfig(prev => ({ 
                    ...prev, 
                    category_id: e.target.value ? Number(e.target.value) : null 
                  }))}
                  className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">전체 콘텐츠</option>
                  {categories?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    시험 시간
                  </label>
                  <select
                    value={testConfig.time_limit_minutes}
                    onChange={(e) => setTestConfig(prev => ({ ...prev, time_limit_minutes: Number(e.target.value) }))}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value={30}>30분</option>
                    <option value={60}>60분</option>
                    <option value={0}>무제한</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    총 문제 수
                  </label>
                  <select
                    value={testConfig.total_questions}
                    onChange={(e) => setTestConfig(prev => ({ ...prev, total_questions: Number(e.target.value) }))}
                    className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value={5}>5문제</option>
                    <option value={10}>10문제</option>
                    <option value={15}>15문제</option>
                    <option value={20}>20문제</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="adaptive_mode"
                  checked={testConfig.adaptive_mode}
                  onChange={(e) => setTestConfig(prev => ({ ...prev, adaptive_mode: e.target.checked }))}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                />
                <label htmlFor="adaptive_mode" className="ml-2 block text-sm text-gray-900 dark:text-gray-100">
                  적응형 난이도 조절 (답변 결과에 따라 난이도 자동 조절)
                </label>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900 p-3 rounded-lg">
                <div className="text-sm text-blue-800 dark:text-blue-200">
                  <strong>시험 구성:</strong>
                  <ul className="mt-1 space-y-1 text-xs">
                    <li>• 객관식 6문제 + 주관식 3문제 + 서술형 1문제</li>
                    <li>• {testConfig.category_id ? '선택한 카테고리' : '전체 콘텐츠'}에서 문제 출제</li>
                    <li>• {testConfig.adaptive_mode ? '적응형 난이도 조절' : '고정 난이도'} 적용</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                취소
              </button>
              <button
                onClick={handleCreateTest}
                disabled={createTestMutation.isPending}
                className="px-4 py-2 bg-indigo-600 dark:bg-indigo-500 text-white rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50"
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