import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { contentAPI } from '../utils/api';
import { Content, Category } from '../types';
import { extractResults } from '../utils/helpers';
import CategoryManager from '../components/CategoryManager';
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
  const [expandedContents, setExpandedContents] = useState<Set<number>>(new Set());
  const [showCategoryManager, setShowCategoryManager] = useState<boolean>(false);


  // Fetch contents
  const { data: contents = [], isLoading: contentsLoading } = useQuery<Content[]>({
    queryKey: ['contents', user?.id, selectedCategory, sortBy, searchQuery],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category_slug', selectedCategory);
      }
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim());
      }
      params.append('ordering', sortBy);
      return contentAPI.getContents(params.toString()).then(extractResults);
    },
    enabled: !!user,
  });

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
      alert('Success: 콘텐츠가 성공적으로 삭제되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
    },
    onError: () => {
      alert('Error: 콘텐츠 삭제에 실패했습니다.');
    },
  });

  const handleDelete = (id: number) => {
    if (window.confirm('정말로 이 콘텐츠를 삭제하시겠습니까?')) {
      deleteContentMutation.mutate(id);
    }
  };

  const handleEdit = (content: Content) => {
    navigate(`/content/${content.id}/edit`);
  };


  const toggleContentExpansion = (contentId: number) => {
    const newExpanded = new Set(expandedContents);
    if (newExpanded.has(contentId)) {
      newExpanded.delete(contentId);
    } else {
      newExpanded.add(contentId);
    }
    setExpandedContents(newExpanded);
  };




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
        onCategoryChange={setSelectedCategory}
        onSortChange={setSortBy}
        onSearchChange={setSearchQuery}
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