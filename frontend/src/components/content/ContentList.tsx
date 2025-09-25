import React from 'react';
import { Content } from '../../types';
import ContentCard from './ContentCard';

interface ContentListProps {
  contents: Content[];
  isLoading: boolean;
  expandedContents: Set<number>;
  onToggleExpansion: (contentId: number) => void;
  onEdit: (content: Content) => void;
  onDelete: (id: number) => void;
  isDeleteLoading?: boolean;
}

const ContentList: React.FC<ContentListProps> = ({
  contents,
  isLoading,
  expandedContents,
  onToggleExpansion,
  onEdit,
  onDelete,
  isDeleteLoading = false,
}) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-32"></div>
                <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-16"></div>
              </div>
              <div className="flex gap-2">
                <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-12"></div>
                <div className="h-6 bg-gray-300 dark:bg-gray-600 rounded w-12"></div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-full"></div>
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (contents.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">콘텐츠 없음</h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">새로운 학습 콘텐츠를 추가해보세요.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {contents.map((content) => (
        <ContentCard
          key={content.id}
          content={content}
          isExpanded={expandedContents.has(content.id)}
          onToggleExpansion={onToggleExpansion}
          onEdit={onEdit}
          onDelete={onDelete}
          isDeleteLoading={isDeleteLoading}
        />
      ))}
    </div>
  );
};

export default ContentList;