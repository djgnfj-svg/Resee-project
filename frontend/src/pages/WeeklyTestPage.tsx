import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AcademicCapIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import TestCreator from '../components/weeklytest/TestCreator';
import TestStats from '../components/weeklytest/TestStats';
import TestHistory from '../components/weeklytest/TestHistory';

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


const WeeklyTestPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  // 주간 시험 목록 조회
  const { data: tests, isLoading, error } = useQuery({
    queryKey: ['weekly-tests'],
    queryFn: aiReviewAPI.getWeeklyTest
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


  const handleStartTest = (testId: number) => {
    startTestMutation.mutate(testId);
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
          <TestStats
            currentTest={currentTest}
            onStartTest={handleStartTest}
            isStarting={startTestMutation.isPending}
          />
        )}

        {/* Completed Tests History */}
        <TestHistory completedTests={completedTests} />
      </div>

      {/* Create Test Modal */}
      <TestCreator
        showCreateModal={showCreateModal}
        onClose={() => setShowCreateModal(false)}
      />
    </div>
  );
};

export default WeeklyTestPage;