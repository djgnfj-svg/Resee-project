import React, { useState, useCallback, useEffect } from 'react';
import { UseFormRegister, UseFormSetValue } from 'react-hook-form';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { contentAPI } from '../../utils/api';
import { Category, CategoryUsage } from '../../types';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  priority: 'low' | 'medium' | 'high';
}

interface CategoryFieldProps {
  register: UseFormRegister<ContentFormData>;
  setValue: UseFormSetValue<ContentFormData>;
  categories: Category[];
}

const CategoryField: React.FC<CategoryFieldProps> = ({ register, setValue, categories }) => {
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [categoryUsage, setCategoryUsage] = useState<CategoryUsage | null>(null);

  const queryClient = useQueryClient();

  // Fetch category usage
  const { data: categoriesData } = useQuery({
    queryKey: ['categories-usage'],
    queryFn: async () => {
      const response = await contentAPI.getCategories();
      if (response.usage) {
        setCategoryUsage(response.usage);
      }
      return response;
    },
  });

  // Check if user can create categories
  const canCreateCategory = categoryUsage ? categoryUsage.can_create : true;
  const isAtLimit = categoryUsage ? categoryUsage.current >= categoryUsage.limit : false;

  // 카테고리 생성 mutation
  const createCategoryMutation = useMutation({
    mutationFn: contentAPI.createCategory,
    onSuccess: (newCategory) => {
      // 기존 카테고리 목록에 새 카테고리를 즉시 추가
      queryClient.setQueryData<Category[]>(['categories'], (oldCategories = []) => {
        const categoryExists = oldCategories.some(cat => cat.id === newCategory.id);
        return categoryExists ? oldCategories : [...oldCategories, newCategory];
      });

      // React가 새 카테고리로 리렌더링할 시간을 준 후 자동 선택
      setTimeout(() => {
        setValue('category', newCategory.id);
      }, 100);

      // UI 초기화
      setShowCreateCategory(false);
      setNewCategoryName('');
      setIsCreatingCategory(false);

      alert(`카테고리 "${newCategory.name}"가 생성되어 선택되었습니다! 🎉`);
    },
    onError: (error: any) => {
      setIsCreatingCategory(false);
      if (error.response?.status === 402) {
        const errorData = error.response.data;
        alert(`⚠️ ${errorData.error}\n\n${errorData.message}`);
      } else {
        const errorMessage = error.response?.data?.name?.[0] || '카테고리 생성에 실패했습니다.';
        alert(`오류: ${errorMessage}`);
      }
    }
  });

  const handleCreateCategory = useCallback(async () => {
    const categoryName = newCategoryName.trim();
    if (!categoryName) return;

    setIsCreatingCategory(true);
    createCategoryMutation.mutate({
      name: categoryName,
      description: `개인 커스텀 카테고리: ${categoryName}`
    });
  }, [newCategoryName, createCategoryMutation]);

  return (
    <div className="space-y-3">
      <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
        카테고리
      </label>

      <div className="flex gap-2">
        <select
          {...register('category')}
          className="flex-1 px-4 py-4 border-2 border-gray-200 dark:border-gray-600 rounded-xl focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-4 focus:ring-indigo-200 dark:focus:ring-indigo-800 focus:outline-none transition-all duration-200 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        >
          <option value="">카테고리를 선택하세요 (선택사항)</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => setShowCreateCategory(true)}
          disabled={!canCreateCategory}
          className={`px-4 py-4 rounded-xl font-medium transition-colors duration-200 whitespace-nowrap ${
            canCreateCategory
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          }`}
          title={!canCreateCategory ? '카테고리 생성 제한에 도달했습니다' : '새 카테고리 만들기'}
        >
          + 새 카테고리
        </button>
      </div>

      {/* Category Usage Info */}
      {categoryUsage && (
        <div className={`p-3 rounded-lg text-sm ${
          isAtLimit ? 'bg-red-50 dark:bg-red-900/20' : 'bg-blue-50 dark:bg-blue-900/20'
        }`}>
          <div className="flex items-center justify-between">
            <span className={`font-medium ${
              isAtLimit ? 'text-red-800 dark:text-red-200' : 'text-blue-800 dark:text-blue-200'
            }`}>
              카테고리 사용량: {categoryUsage.current} / {categoryUsage.limit}개
            </span>
            {isAtLimit && (
              <button
                type="button"
                onClick={() => window.location.href = '/settings#subscription'}
                className="px-3 py-1 text-xs font-medium text-white bg-gradient-to-r from-purple-600 to-pink-600 rounded hover:from-purple-700 hover:to-pink-700 transition-all"
              >
                업그레이드
              </button>
            )}
          </div>
        </div>
      )}

      {/* 인라인 카테고리 생성 */}
      {showCreateCategory && (
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="font-medium text-gray-900 dark:text-gray-100">새 카테고리 만들기</h4>
              <button
                type="button"
                onClick={() => setShowCreateCategory(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>

            <input
              type="text"
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              placeholder="카테고리 이름 (예: 📚 영어학습, 💻 프로그래밍)"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              onKeyPress={(e) => e.key === 'Enter' && handleCreateCategory()}
            />

            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleCreateCategory}
                disabled={!newCategoryName.trim() || isCreatingCategory}
                className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors duration-200"
              >
                {isCreatingCategory ? '생성중...' : '생성'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateCategory(false);
                  setNewCategoryName('');
                }}
                className="px-3 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors duration-200"
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryField;