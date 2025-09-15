import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Content } from '../../types';

interface ContentCardProps {
  content: Content;
  isExpanded: boolean;
  onToggleExpansion: (contentId: number) => void;
  onEdit: (content: Content) => void;
  onDelete: (id: number) => void;
  isDeleteLoading?: boolean;
}

const ContentCard: React.FC<ContentCardProps> = ({
  content,
  isExpanded,
  onToggleExpansion,
  onEdit,
  onDelete,
  isDeleteLoading = false,
}) => {
  const getFirstLinePreview = (content: string, maxLength: number = 30): string => {
    if (!content) return '';

    // 첫 번째 줄 가져오기
    const firstLine = content.split('\n')[0];

    // 30글자로 자르기
    if (firstLine.length <= maxLength) {
      return firstLine;
    }

    return firstLine.substring(0, maxLength) + '...';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20';
      case 'medium': return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20';
      case 'low': return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
      default: return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-700/20';
    }
  };

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case 'high': return '높음';
      case 'medium': return '보통';
      case 'low': return '낮음';
      default: return priority;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
              {content.title}
            </h3>
            <div className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(content.priority)}`}>
              {getPriorityText(content.priority)}
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              내일 복습
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              {new Date(content.created_at).toLocaleDateString('ko-KR')}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={() => onEdit(content)}
            className="px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 hover:border-blue-700 rounded transition-colors"
          >
            편집
          </button>
          <button
            onClick={() => onDelete(content.id)}
            disabled={isDeleteLoading}
            className="px-3 py-1 text-sm font-medium text-red-600 hover:text-red-700 border border-red-600 hover:border-red-700 rounded transition-colors disabled:opacity-50"
          >
            {isDeleteLoading ? '삭제 중...' : '삭제'}
          </button>
        </div>
      </div>

      {/* Content Preview/Full */}
      <div className="mb-4">
        {isExpanded ? (
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content.content}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="text-gray-600 dark:text-gray-300">
            {getFirstLinePreview(content.content)}
          </div>
        )}
      </div>


      {/* Toggle Button */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={() => onToggleExpansion(content.id)}
          className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
        >
          <svg
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
          {isExpanded ? '접기' : '더 보기'}
        </button>
      </div>
    </div>
  );
};

export default ContentCard;