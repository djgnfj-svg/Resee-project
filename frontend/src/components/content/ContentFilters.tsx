import React from 'react';
import { Category } from '../../types';

interface ContentFiltersProps {
  categories: Category[];
  selectedCategory: string;
  selectedPriority: string;
  sortBy: string;
  searchQuery: string;
  onCategoryChange: (category: string) => void;
  onPriorityChange: (priority: string) => void;
  onSortChange: (sort: string) => void;
  onSearchChange: (query: string) => void;
  onCategoryManagerOpen: () => void;
}

const ContentFilters: React.FC<ContentFiltersProps> = ({
  categories,
  selectedCategory,
  selectedPriority,
  sortBy,
  searchQuery,
  onCategoryChange,
  onPriorityChange,
  onSortChange,
  onSearchChange,
  onCategoryManagerOpen,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">📂</span>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">필터</h2>
      </div>

      <div className="space-y-4">
        {/* Search */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm">🔍</span>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">콘텐츠 검색</span>
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="제목이나 내용으로 검색하세요..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Category Filter */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm">📂</span>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">카테고리</span>
              </div>
              <button
                onClick={onCategoryManagerOpen}
                className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-700 border border-blue-600 hover:border-blue-700 rounded transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                관리
              </button>
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => onCategoryChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">전체 카테고리</option>
              {categories.map((category) => (
                <option key={category.id} value={category.slug}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Filter */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm">⚡</span>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">우선순위</span>
            </div>
            <select
              value={selectedPriority}
              onChange={(e) => onPriorityChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="all">전체 우선순위</option>
              <option value="high">높음</option>
              <option value="medium">보통</option>
              <option value="low">낮음</option>
            </select>
          </div>

          {/* Sort Filter */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm">📊</span>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">정렬</span>
            </div>
            <select
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="-created_at">최신순</option>
              <option value="created_at">오래된순</option>
              <option value="title">제목순</option>
              <option value="-priority">우선순위 높은순</option>
              <option value="priority">우선순위 낮은순</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContentFilters;