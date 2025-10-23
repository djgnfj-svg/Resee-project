import React from 'react';
import { Category } from '../../types';

interface CategorySelectorModalProps {
  show: boolean;
  categories: Category[];
  selectedCategoryIds: number[];
  error: string;
  isLoading: boolean;
  onToggleCategory: (categoryId: number) => void;
  onCreate: () => void;
  onClose: () => void;
}

const CategorySelectorModal: React.FC<CategorySelectorModalProps> = ({
  show,
  categories,
  selectedCategoryIds,
  error,
  isLoading,
  onToggleCategory,
  onCreate,
  onClose,
}) => {
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          카테고리 선택
        </h3>

        <div className="mb-6">
          <select
            value={selectedCategoryIds[0] || ''}
            onChange={(e) => {
              const categoryId = parseInt(e.target.value);
              if (categoryId) {
                onToggleCategory(categoryId);
              }
            }}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">카테고리를 선택하세요</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border-2 border-red-400 dark:border-red-600 rounded-lg">
            <div className="flex items-start">
              <span className="text-red-500 mr-2 text-lg">⚠️</span>
              <p className="text-red-800 dark:text-red-200 text-sm font-medium">{error}</p>
            </div>
          </div>
        )}

        <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {selectedCategoryIds.length === 0
            ? "카테고리를 선택하세요. 선택된 카테고리에서 200자 이상 콘텐츠 7개가 필요합니다."
            : `선택된 카테고리에서 200자 이상 콘텐츠 7개가 필요합니다.`
          }
        </div>

        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            취소
          </button>
          <button
            onClick={onCreate}
            disabled={isLoading || selectedCategoryIds.length === 0}
            className="flex-1 px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {isLoading ? '생성 중...' : '시험 생성'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CategorySelectorModal;
