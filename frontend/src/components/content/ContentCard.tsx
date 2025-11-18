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
  const getFirstLinePreview = (content: string, maxLength: number = 80): string => {
    if (!content) return '';
    const firstLine = content.split('\n')[0];
    if (firstLine.length <= maxLength) {
      return firstLine;
    }
    return firstLine.substring(0, maxLength) + '...';
  };

  const formatDate = (dateString: string, isFutureDate: boolean = false) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    // 미래 날짜인 경우 (다음 복습 날짜)
    if (isFutureDate) {
      if (diffDays === 0) return '오늘';
      if (diffDays === 1) return '내일';
      if (diffDays > 0) return `D-${diffDays}`;
      // 과거 날짜인 경우 (복습 기한 지남)
      if (diffDays === -1) return '어제';
      if (diffDays < 0) return `D+${Math.abs(diffDays)}`;
    }

    // 과거 날짜인 경우 (생성 날짜)
    const pastDiffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    if (pastDiffDays === 0) return '오늘';
    if (pastDiffDays === 1) return '어제';
    if (pastDiffDays < 7) return `${pastDiffDays}일 전`;
    return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const getModeInfo = () => {
    if (content.review_mode === 'objective') {
      return {
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
        label: '기억 확인',
        color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
      };
    }
    if (content.review_mode === 'descriptive') {
      return {
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        ),
        label: '서술형',
        color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
      };
    }
    if (content.review_mode === 'multiple_choice') {
      return {
        icon: (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        ),
        label: '객관식',
        color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300'
      };
    }
    // subjective
    return {
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
        </svg>
      ),
      label: '주관식',
      color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
    };
  };

  const modeInfo = getModeInfo();

  return (
    <div className="group bg-white dark:bg-gray-800 rounded-xl shadow-md border border-gray-200 dark:border-gray-700 hover:shadow-xl hover:border-indigo-300 dark:hover:border-indigo-700 transition-all duration-200 overflow-hidden">
      {/* Top accent line */}
      <div className="h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>

      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {/* Title */}
              <h3 className="text-xl font-bold text-gray-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                {content.title}
              </h3>
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-3 flex-wrap">
              {/* Category Badge */}
              {content.category && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300">
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  {content.category.name}
                </span>
              )}

              {/* Review Mode Badge */}
              <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${modeInfo.color}`}>
                {modeInfo.icon}
                {modeInfo.label}
              </span>

              {/* Review Count */}
              <span className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                복습 {content.review_count}회
              </span>

              {/* Created Date */}
              <span className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {formatDate(content.created_at)}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2 ml-4">
            <button
              onClick={() => onEdit(content)}
              className="p-2 text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 dark:text-gray-400 dark:hover:text-indigo-400 dark:hover:bg-gray-700 rounded-lg transition-colors"
              title="편집"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button
              onClick={() => onDelete(content.id)}
              disabled={isDeleteLoading}
              className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 dark:text-gray-400 dark:hover:text-red-400 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
              title="삭제"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content Preview/Full */}
        <div className="mb-4">
          {isExpanded ? (
            <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-gray-900 dark:prose-headings:text-white prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:max-w-none prose-headings:max-w-none prose-ul:max-w-none prose-ol:max-w-none prose-pre:max-w-none break-words overflow-hidden whitespace-pre-wrap">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content.content}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 line-clamp-2">
              {getFirstLinePreview(content.content)}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          {/* Next Review Date */}
          <div className="flex items-center gap-2 text-sm">
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-gray-700 dark:to-gray-750 rounded-lg">
              <svg className="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="font-medium text-indigo-700 dark:text-indigo-300">
                {content.next_review_date ? `다음 복습: ${formatDate(content.next_review_date, true)}` : '복습 대기 중'}
              </span>
            </div>
          </div>

          {/* Toggle Button */}
          <button
            onClick={() => onToggleExpansion(content.id)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-indigo-600 dark:text-gray-300 dark:hover:text-indigo-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <span>{isExpanded ? '접기' : '전체 보기'}</span>
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContentCard;
