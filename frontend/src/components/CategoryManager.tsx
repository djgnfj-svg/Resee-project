import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category, CreateCategoryData } from '../types';
import { extractResults } from '../utils/helpers';

interface CategoryManagerProps {
  onClose: () => void;
}

const CategoryManager: React.FC<CategoryManagerProps> = ({ onClose }) => {
  const queryClient = useQueryClient();
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editName, setEditName] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');

  // Fetch categories
  const { data: categories = [], isLoading } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Create category mutation
  const createCategoryMutation = useMutation({
    mutationFn: contentAPI.createCategory,
    onSuccess: () => {
      alert('Success: 카테고리가 성공적으로 생성되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setNewCategoryName('');
      setShowCreateForm(false);
    },
    onError: () => {
      alert('Error: 카테고리 생성에 실패했습니다.');
    },
  });

  // Update category mutation
  const updateCategoryMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: CreateCategoryData }) => 
      contentAPI.updateCategory(id, data),
    onSuccess: () => {
      alert('Success: 카테고리가 성공적으로 수정되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setEditingCategory(null);
      setEditName('');
    },
    onError: () => {
      alert('Error: 카테고리 수정에 실패했습니다.');
    },
  });

  // Delete category mutation
  const deleteCategoryMutation = useMutation({
    mutationFn: contentAPI.deleteCategory,
    onSuccess: () => {
      alert('Success: 카테고리가 성공적으로 삭제되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      queryClient.invalidateQueries({ queryKey: ['contents'] });
    },
    onError: () => {
      alert('Error: 카테고리 삭제에 실패했습니다.');
    },
  });

  const handleCreateCategory = () => {
    if (newCategoryName.trim()) {
      createCategoryMutation.mutate({ name: newCategoryName.trim() });
    }
  };

  const handleEditCategory = (category: Category) => {
    setEditingCategory(category);
    setEditName(category.name);
  };

  const handleUpdateCategory = () => {
    if (editingCategory && editName.trim()) {
      updateCategoryMutation.mutate({
        id: editingCategory.id,
        data: { name: editName.trim() }
      });
    }
  };

  const handleDeleteCategory = (category: Category) => {
    if (window.confirm(`"${category.name}" 카테고리를 정말 삭제하시겠습니까?\n이 카테고리를 사용하는 콘텐츠들의 카테고리는 해제됩니다.`)) {
      deleteCategoryMutation.mutate(category.id);
    }
  };

  const cancelEdit = () => {
    setEditingCategory(null);
    setEditName('');
  };

  const cancelCreate = () => {
    setShowCreateForm(false);
    setNewCategoryName('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            📂 카테고리 관리
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4 max-h-[60vh] overflow-y-auto">
          {/* Create Category Form */}
          {showCreateForm ? (
            <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                새 카테고리 만들기
              </h4>
              <input
                type="text"
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                placeholder="카테고리 이름 (예: 📚 영어학습, 💻 프로그래밍)"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 mb-2"
                onKeyPress={(e) => e.key === 'Enter' && handleCreateCategory()}
              />
              <div className="flex gap-2">
                <button
                  onClick={handleCreateCategory}
                  disabled={!newCategoryName.trim() || createCategoryMutation.isPending}
                  className="px-3 py-1.5 bg-primary-600 text-white rounded-md text-sm hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createCategoryMutation.isPending ? '생성 중...' : '생성'}
                </button>
                <button
                  onClick={cancelCreate}
                  className="px-3 py-1.5 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md text-sm hover:bg-gray-400 dark:hover:bg-gray-500"
                >
                  취소
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowCreateForm(true)}
              className="w-full mb-4 p-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-primary-500 hover:text-primary-500 transition-colors"
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                새 카테고리 추가
              </div>
            </button>
          )}

          {/* Category List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : categories.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg className="mx-auto h-12 w-12 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
              </svg>
              <p>생성된 카테고리가 없습니다</p>
              <p className="text-sm">새 카테고리를 추가해보세요</p>
            </div>
          ) : (
            <div className="space-y-2">
              {categories.map((category) => (
                <div
                  key={category.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                >
                  {editingCategory?.id === category.id ? (
                    <div className="flex-1 flex items-center gap-2">
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                        onKeyPress={(e) => e.key === 'Enter' && handleUpdateCategory()}
                        autoFocus
                      />
                      <button
                        onClick={handleUpdateCategory}
                        disabled={!editName.trim() || updateCategoryMutation.isPending}
                        className="px-2 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
                      >
                        ✓
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="px-2 py-1 bg-gray-400 text-white rounded text-sm hover:bg-gray-500"
                      >
                        ✕
                      </button>
                    </div>
                  ) : (
                    <>
                      <span className="flex-1 text-gray-900 dark:text-gray-100 font-medium">
                        {category.name}
                      </span>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleEditCategory(category)}
                          className="p-1.5 text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400"
                          title="수정"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteCategory(category)}
                          className="p-1.5 text-gray-500 hover:text-red-600 dark:hover:text-red-400"
                          title="삭제"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
};

export default CategoryManager;