import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { PlayIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/api';

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

interface TestCreatorProps {
  showCreateModal: boolean;
  onClose: () => void;
}

const TestCreator: React.FC<TestCreatorProps> = ({ showCreateModal, onClose }) => {
  const queryClient = useQueryClient();
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

  // 주간 시험 생성
  const createTestMutation = useMutation({
    mutationFn: async (data: any) => {
      // AI 기능 준비중 메시지 표시
      toast('🚧 AI 기능은 현재 준비 중입니다');
      throw new Error('AI 기능 준비중');
    },
    onSuccess: () => {
      toast.success('주간 시험이 생성되었습니다!');
      onClose();
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

  const handleCreateTest = () => {
    createTestMutation.mutate(testConfig);
  };

  if (!showCreateModal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full max-h-screen overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              새 주간 시험 만들기
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Form */}
          <div className="space-y-4">
            {/* Category Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                카테고리 (선택사항)
              </label>
              <select
                value={testConfig.category_id || ''}
                onChange={(e) => setTestConfig({
                  ...testConfig,
                  category_id: e.target.value ? parseInt(e.target.value) : null
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">전체 카테고리</option>
                {categories?.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Time Limit */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                제한 시간 (분)
              </label>
              <select
                value={testConfig.time_limit_minutes}
                onChange={(e) => setTestConfig({
                  ...testConfig,
                  time_limit_minutes: parseInt(e.target.value)
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value={15}>15분</option>
                <option value={30}>30분</option>
                <option value={45}>45분</option>
                <option value={60}>60분</option>
              </select>
            </div>

            {/* Question Count */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                문제 수
              </label>
              <select
                value={testConfig.total_questions}
                onChange={(e) => setTestConfig({
                  ...testConfig,
                  total_questions: parseInt(e.target.value)
                })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value={5}>5문제</option>
                <option value={10}>10문제</option>
                <option value={15}>15문제</option>
                <option value={20}>20문제</option>
              </select>
            </div>

            {/* Adaptive Mode */}
            <div className="flex items-center">
              <input
                type="checkbox"
                id="adaptive_mode"
                checked={testConfig.adaptive_mode}
                onChange={(e) => setTestConfig({
                  ...testConfig,
                  adaptive_mode: e.target.checked
                })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="adaptive_mode" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                적응형 난이도 (답변에 따라 난이도 조절)
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex space-x-3 mt-6">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
            >
              취소
            </button>
            <button
              onClick={handleCreateTest}
              disabled={createTestMutation.isPending}
              className="flex-1 flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
            >
              {createTestMutation.isPending ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
              ) : (
                <PlayIcon className="w-4 h-4 mr-2" />
              )}
              시험 생성
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestCreator;