import React, { useState, useCallback } from 'react';
import { UseFormRegister, UseFormSetValue } from 'react-hook-form';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { contentAPI } from '../../utils/api';
import { Category, CategoryUsage, CreateContentData } from '../../types';

type ContentFormData = CreateContentData;

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
  useQuery({
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
    <div>
      <div className="flex gap-2">
        <select
          {...register('category')}
          className="flex-1 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:border-blue-500 dark:focus:border-blue-400 focus:ring-1 focus:ring-blue-500 focus:outline-none transition-colors bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        >
          <option value="">카테고리 선택 (선택사항)</option>
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
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors whitespace-nowrap ${
            canCreateCategory
              ? 'bg-gray-100 hover:bg-gray-200 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed dark:bg-gray-700 dark:text-gray-500'
          }`}
          title={!canCreateCategory ? '카테고리 생성 제한에 도달했습니다. 구독을 업그레이드하세요.' : '새 카테고리 만들기'}
        >
          + 새 카테고리
        </button>
      </div>

      {/* 인라인 카테고리 생성 */}
      {showCreateCategory && (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">새 카테고리 만들기</h4>
              <button
                type="button"
                onClick={() => setShowCreateCategory(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>

            <input
              type="text"
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              placeholder="카테고리 이름 (예: 📚 영어학습, 💻 프로그래밍)"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
              onKeyPress={(e) => e.key === 'Enter' && handleCreateCategory()}
            />

            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleCreateCategory}
                disabled={!newCategoryName.trim() || isCreatingCategory}
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium transition-colors"
              >
                {isCreatingCategory ? '생성중...' : '생성'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateCategory(false);
                  setNewCategoryName('');
                }}
                className="px-3 py-1.5 bg-gray-400 hover:bg-gray-500 text-white rounded-md text-sm font-medium transition-colors"
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