import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { contentAPI } from '../utils/api';
import { Content, Category, ContentListResponse } from '../types';
import { extractResults } from '../utils/helpers';
import CategoryManager from '../components/content/CategoryManager';
import ContentFilters from '../components/content/ContentFilters';
import ContentList from '../components/content/ContentList';
import { useAuth } from '../contexts/AuthContext';

const ContentPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('-created_at');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [expandedContents, setExpandedContents] = useState<Set<number>>(new Set());
  const [showCategoryManager, setShowCategoryManager] = useState<boolean>(false);


  // Fetch contents with pagination
  const { data: contentsData, isLoading: contentsLoading } = useQuery<ContentListResponse>({
    queryKey: ['contents', user?.id, selectedCategory, sortBy, searchQuery, currentPage],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category_slug', selectedCategory);
      }
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim());
      }
      params.append('ordering', sortBy);
      params.append('page', currentPage.toString());
      return contentAPI.getContents(params.toString());
    },
    enabled: !!user,
  });

  const contents = contentsData?.results || [];
  const totalPages = contentsData?.total_pages || 1;
  const totalCount = contentsData?.count || 0;

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories', user?.id],
    queryFn: () => contentAPI.getCategories().then(extractResults),
    enabled: !!user,
  });


  // Delete content mutation
  const deleteContentMutation = useMutation({
    mutationFn: contentAPI.deleteContent,
    onSuccess: () => {
      toast.success('콘텐츠가 성공적으로 삭제되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
    },
    onError: () => {
      toast.error('콘텐츠 삭제에 실패했습니다.');
    },
  });

  const handleDelete = useCallback((id: number) => {
    if (window.confirm('정말로 이 콘텐츠를 삭제하시겠습니까?')) {
      deleteContentMutation.mutate(id);
    }
  }, [deleteContentMutation]);

  const handleEdit = useCallback((content: Content) => {
    navigate(`/content/${content.id}/edit`);
  }, [navigate]);

  const toggleContentExpansion = useCallback((contentId: number) => {
    setExpandedContents(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(contentId)) {
        newExpanded.delete(contentId);
      } else {
        newExpanded.add(contentId);
      }
      return newExpanded;
    });
  }, []);

  // Reset to page 1 when filters change
  const handleCategoryChange = useCallback((category: string) => {
    setSelectedCategory(category);
    setCurrentPage(1);
  }, []);

  const handleSortChange = useCallback((sort: string) => {
    setSortBy(sort);
    setCurrentPage(1);
  }, []);

  const handleSearchChange = useCallback((query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  }, []);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="mb-8 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">📚 콘텐츠 관리</h1>
            <p className="text-indigo-100">
              학습 콘텐츠를 작성하고 효율적으로 관리하세요
            </p>
          </div>
          <Link
            to="/content/new"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-white text-indigo-600 px-6 py-3 text-sm font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-150 w-full sm:w-auto"
          >
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
            </svg>
            새 콘텐츠 만들기
          </Link>
        </div>
      </div>

      {/* Filters */}
      <ContentFilters
        categories={categories}
        selectedCategory={selectedCategory}
        sortBy={sortBy}
        searchQuery={searchQuery}
        onCategoryChange={handleCategoryChange}
        onSortChange={handleSortChange}
        onSearchChange={handleSearchChange}
        onCategoryManagerOpen={() => setShowCategoryManager(true)}
      />

      {/* Content List */}
      <ContentList
        contents={contents}
        isLoading={contentsLoading}
        expandedContents={expandedContents}
        onToggleExpansion={toggleContentExpansion}
        onEdit={handleEdit}
        onDelete={handleDelete}
        isDeleteLoading={deleteContentMutation.isPending}
      />

      {/* Pagination */}
      {!contentsLoading && totalPages > 1 && (
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-4 bg-white dark:bg-gray-800 rounded-xl p-6 shadow-md border border-gray-200 dark:border-gray-700">
          {/* Page Info */}
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <span className="font-medium text-gray-900 dark:text-white">
              {((currentPage - 1) * (contentsData?.page_size || 15)) + 1}
            </span>
            {' - '}
            <span className="font-medium text-gray-900 dark:text-white">
              {Math.min(currentPage * (contentsData?.page_size || 15), totalCount)}
            </span>
            {' / '}
            <span className="font-medium text-gray-900 dark:text-white">
              {totalCount}
            </span>
            {' 개'}
          </div>

          {/* Page Buttons */}
          <div className="flex items-center gap-2">
            {/* Previous Button */}
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              이전
            </button>

            {/* Page Numbers */}
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum: number;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                      currentPage === pageNum
                        ? 'bg-indigo-600 text-white shadow-md'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>

            {/* Next Button */}
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              다음
            </button>
          </div>

          {/* Page Jump */}
          <div className="text-sm text-gray-600 dark:text-gray-400">
            <span>페이지 </span>
            <span className="font-medium text-gray-900 dark:text-white">
              {currentPage} / {totalPages}
            </span>
          </div>
        </div>
      )}

      {/* Category Manager Modal */}
      {showCategoryManager && (
        <CategoryManager
          onClose={() => setShowCategoryManager(false)}
        />
      )}
    </div>
  );
};

export default ContentPage;