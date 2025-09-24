import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Content, Category, CreateContentData, UpdateContentData } from '../types';
import { extractResults } from '../utils/helpers';
import ContentFormV2 from '../components/ContentFormV2';
import CategoryManager from '../components/CategoryManager';
import ContentFilters from '../components/content/ContentFilters';
import ContentList from '../components/content/ContentList';

const ContentPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingContent, setEditingContent] = useState<Content | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('-created_at');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedContents, setExpandedContents] = useState<Set<number>>(new Set());
  const [showCategoryManager, setShowCategoryManager] = useState<boolean>(false);


  // Fetch contents
  const { data: contents = [], isLoading: contentsLoading } = useQuery<Content[]>({
    queryKey: ['contents', selectedCategory, selectedPriority, sortBy, searchQuery],
    queryFn: () => {
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category_slug', selectedCategory);
      }
      if (selectedPriority !== 'all') {
        params.append('priority', selectedPriority);
      }
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim());
      }
      params.append('ordering', sortBy);
      return contentAPI.getContents(params.toString()).then(extractResults);
    },
  });

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Create content mutation
  const createContentMutation = useMutation({
    mutationFn: contentAPI.createContent,
    onSuccess: () => {
      alert('Success: 콘텐츠가 성공적으로 생성되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setShowForm(false);
    },
    onError: () => {
      alert('Error: 콘텐츠 생성에 실패했습니다.');
    },
  });

  // Update content mutation
  const updateContentMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateContentData }) => 
      contentAPI.updateContent(id, data),
    onSuccess: () => {
      alert('Success: 콘텐츠가 성공적으로 수정되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      setEditingContent(null);
      setShowForm(false);
    },
    onError: () => {
      alert('Error: 콘텐츠 수정에 실패했습니다.');
    },
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

  const handleSubmit = (data: CreateContentData | UpdateContentData) => {
    if (editingContent) {
      updateContentMutation.mutate({ id: editingContent.id, data });
    } else {
      createContentMutation.mutate(data as CreateContentData);
    }
  };

  const handleEdit = (content: Content) => {
    setEditingContent(content);
    setShowForm(true);
  };

  const handleDelete = (id: number) => {
    if (window.confirm('정말로 이 콘텐츠를 삭제하시겠습니까?')) {
      deleteContentMutation.mutate(id);
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingContent(null);
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


  if (showForm) {
    return (
      <ContentFormV2
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        isLoading={createContentMutation.isPending || updateContentMutation.isPending}
        initialData={editingContent ? {
          title: editingContent.title,
          content: editingContent.content,
          category: editingContent.category?.id,
          priority: editingContent.priority,
        } : undefined}
      />
    );
  }


  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100">콘텐츠 관리</h1>
          <p className="mt-2 text-sm sm:text-base text-gray-600 dark:text-gray-400">
            학습 콘텐츠를 작성하고 관리합니다.
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center justify-center rounded-md bg-blue-600 dark:bg-blue-500 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-500 dark:hover:bg-blue-400 w-full sm:w-auto transition-colors"
          >
            <svg className="-ml-0.5 mr-1.5 h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.75 4.75a.75.75 0 00-1.5 0v4.5h-4.5a.75.75 0 000 1.5h4.5v4.5a.75.75 0 001.5 0v-4.5h4.5a.75.75 0 000-1.5h-4.5v-4.5z" />
            </svg>
            새 콘텐츠
          </button>
        </div>
      </div>

      {/* Filters */}
      <ContentFilters
        categories={categories}
        selectedCategory={selectedCategory}
        selectedPriority={selectedPriority}
        sortBy={sortBy}
        searchQuery={searchQuery}
        onCategoryChange={setSelectedCategory}
        onPriorityChange={setSelectedPriority}
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