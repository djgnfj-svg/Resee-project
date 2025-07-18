import React, { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { contentAPI } from '../utils/api';
import { Content, Category } from '../types';
import { extractResults, getPriorityInfo } from '../utils/helpers';

interface SearchFilters {
  query: string;
  categories: string[];
  priorities: string[];
  dateRange: {
    start: string;
    end: string;
  };
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

const SearchPage: React.FC = () => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: '',
    categories: [],
    priorities: [],
    dateRange: { start: '', end: '' },
    sortBy: 'created_at',
    sortOrder: 'desc'
  });

  const [showFilters, setShowFilters] = useState(false);
  const [selectedContent, setSelectedContent] = useState<Content | null>(null);

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Search results
  const { data: searchResults = [], isLoading } = useQuery<Content[]>({
    queryKey: ['search', filters],
    queryFn: () => {
      const params = new URLSearchParams();
      
      if (filters.query) {
        params.append('search', filters.query);
      }
      
      if (filters.categories.length > 0) {
        filters.categories.forEach(cat => params.append('category', cat));
      }
      
      if (filters.priorities.length > 0) {
        filters.priorities.forEach(priority => params.append('priority', priority));
      }
      
      if (filters.dateRange.start) {
        params.append('created_after', filters.dateRange.start);
      }
      
      if (filters.dateRange.end) {
        params.append('created_before', filters.dateRange.end);
      }
      
      const ordering = filters.sortOrder === 'desc' ? `-${filters.sortBy}` : filters.sortBy;
      params.append('ordering', ordering);
      
      return contentAPI.getContents(params.toString()).then(extractResults);
    },
    enabled: filters.query.length >= 2 || filters.categories.length > 0
  });

  const updateFilter = useCallback((key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const toggleArrayFilter = useCallback((key: 'categories' | 'priorities', value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: prev[key].includes(value) 
        ? prev[key].filter(item => item !== value)
        : [...prev[key], value]
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      query: '',
      categories: [],
      priorities: [],
      dateRange: { start: '', end: '' },
      sortBy: 'created_at',
      sortOrder: 'desc'
    });
  }, []);

  const hasActiveFilters = useMemo(() => {
    return filters.query || 
           filters.categories.length > 0 || 
           filters.priorities.length > 0 ||
           filters.dateRange.start ||
           filters.dateRange.end;
  }, [filters]);

  const priorityOptions = ['high', 'medium', 'low'].map(priority => ({
    value: priority,
    ...getPriorityInfo(priority as 'high' | 'medium' | 'low')
  }));

  const sortOptions = [
    { value: 'created_at', label: '생성일' },
    { value: 'updated_at', label: '수정일' },
    { value: 'title', label: '제목' },
    { value: 'priority', label: '우선순위' }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">고급 검색</h1>
        <p className="text-sm sm:text-base text-gray-600">
          다양한 필터를 사용하여 원하는 콘텐츠를 찾아보세요
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 sm:gap-8">
        {/* Search Filters Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-lg overflow-hidden sticky top-4">
            {/* Mobile Filter Toggle */}
            <div className="lg:hidden">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="w-full px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between text-left"
              >
                <span className="font-medium text-gray-900">검색 필터</span>
                <svg
                  className={`w-5 h-5 transform transition-transform ${showFilters ? 'rotate-180' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            {/* Filter Content */}
            <div className={`${showFilters ? 'block' : 'hidden'} lg:block p-4 sm:p-6 space-y-6`}>
              {/* Search Query */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  🔍 검색어
                </label>
                <input
                  type="text"
                  value={filters.query}
                  onChange={(e) => updateFilter('query', e.target.value)}
                  placeholder="제목이나 내용으로 검색..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Categories */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  📂 카테고리
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {categories.map((category) => (
                    <label key={category.id} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.categories.includes(category.slug)}
                        onChange={() => toggleArrayFilter('categories', category.slug)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">{category.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  ⚡ 우선순위
                </label>
                <div className="space-y-2">
                  {priorityOptions.map((option) => (
                    <label key={option.value} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.priorities.includes(option.value)}
                        onChange={() => toggleArrayFilter('priorities', option.value)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">
                        {option.emoji} {option.label}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Date Range */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  📅 생성일 범위
                </label>
                <div className="space-y-2">
                  <input
                    type="date"
                    value={filters.dateRange.start}
                    onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, start: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="시작일"
                  />
                  <input
                    type="date"
                    value={filters.dateRange.end}
                    onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, end: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="종료일"
                  />
                </div>
              </div>

              {/* Sort Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  📊 정렬
                </label>
                <select
                  value={filters.sortBy}
                  onChange={(e) => updateFilter('sortBy', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mb-2"
                >
                  {sortOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <div className="flex space-x-2">
                  <button
                    onClick={() => updateFilter('sortOrder', 'desc')}
                    className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
                      filters.sortOrder === 'desc'
                        ? 'bg-blue-50 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    내림차순
                  </button>
                  <button
                    onClick={() => updateFilter('sortOrder', 'asc')}
                    className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
                      filters.sortOrder === 'asc'
                        ? 'bg-blue-50 border-blue-300 text-blue-700'
                        : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    오름차순
                  </button>
                </div>
              </div>

              {/* Clear Filters */}
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                >
                  필터 초기화
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Search Results */}
        <div className="lg:col-span-3">
          {/* Results Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 space-y-4 sm:space-y-0">
            <div>
              {isLoading ? (
                <div className="animate-pulse">
                  <div className="h-6 w-32 bg-gray-200 rounded"></div>
                </div>
              ) : (
                <p className="text-sm text-gray-600">
                  {searchResults.length}개의 검색 결과
                </p>
              )}
            </div>
            
            {hasActiveFilters && (
              <div className="flex flex-wrap gap-2">
                {filters.query && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                    검색: "{filters.query}"
                  </span>
                )}
                {filters.categories.map((cat) => (
                  <span key={cat} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                    {categories.find(c => c.slug === cat)?.name || cat}
                  </span>
                ))}
                {filters.priorities.map((priority) => (
                  <span key={priority} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
                    {priorityOptions.find(p => p.value === priority)?.emoji} {priorityOptions.find(p => p.value === priority)?.label}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!isLoading && searchResults.length === 0 && hasActiveFilters && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">검색 결과가 없습니다</h3>
              <p className="text-gray-600 mb-6">
                다른 검색어나 필터를 시도해보세요
              </p>
              <button
                onClick={clearFilters}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                필터 초기화
              </button>
            </div>
          )}

          {/* No Search State */}
          {!isLoading && !hasActiveFilters && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">고급 검색 시작하기</h3>
              <p className="text-gray-600">
                왼쪽 필터를 사용하여 원하는 콘텐츠를 찾아보세요
              </p>
            </div>
          )}

          {/* Search Results */}
          {!isLoading && searchResults.length > 0 && (
            <div className="space-y-4">
                {searchResults.map((content) => (
                  <div
                    key={content.id}
                    className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-4 sm:p-6"
                  >
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 space-y-2 sm:space-y-0">
                      <div className="flex-1">
                        <Link
                          to={`/content/${content.id}`}
                          className="text-lg sm:text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {content.title}
                        </Link>
                        {content.category && (
                          <span className="inline-block mt-1 px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                            📂 {content.category.name}
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          content.priority === 'high' 
                            ? 'bg-red-100 text-red-700'
                            : content.priority === 'medium'
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {priorityOptions.find(p => p.value === content.priority)?.emoji} {priorityOptions.find(p => p.value === content.priority)?.label}
                        </span>
                      </div>
                    </div>

                    {/* Content Preview */}
                    <div className="text-gray-600 text-sm sm:text-base mb-4 line-clamp-3">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                      >
                        {content.content.length > 200 
                          ? content.content.substring(0, 200) + '...' 
                          : content.content}
                      </ReactMarkdown>
                    </div>

                    {/* Meta Info */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs text-gray-500 space-y-2 sm:space-y-0">
                      <div className="flex items-center space-x-4">
                        <span>📅 {new Date(content.created_at).toLocaleDateString('ko-KR')}</span>
                        {content.updated_at !== content.created_at && (
                          <span>🔄 {new Date(content.updated_at).toLocaleDateString('ko-KR')}</span>
                        )}
                      </div>
                      <button
                        onClick={() => setSelectedContent(content)}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        자세히 보기 →
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Content Detail Modal */}
        {selectedContent && (
          <div
            className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-50 flex items-center justify-center p-4"
            onClick={() => setSelectedContent(null)}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
            >
              <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex-1 pr-4">
                  {selectedContent.title}
                </h2>
                <button
                  onClick={() => setSelectedContent(null)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="p-4 sm:p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
                <div className="prose prose-sm sm:prose-base max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                  >
                    {selectedContent.content}
                  </ReactMarkdown>
                </div>
                
                {/* Meta Information */}
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>📅 생성일: {new Date(selectedContent.created_at).toLocaleString('ko-KR')}</div>
                    <div>🔄 수정일: {new Date(selectedContent.updated_at).toLocaleString('ko-KR')}</div>
                    {selectedContent.category && (
                      <div>📂 카테고리: {selectedContent.category.name}</div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="p-4 sm:p-6 border-t border-gray-200 bg-gray-50">
                <Link
                  to={`/content/${selectedContent.id}`}
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  onClick={() => setSelectedContent(null)}
                >
                  편집하기 →
                </Link>
              </div>
            </div>
          </div>
        )}
    </div>
  );
};

export default SearchPage;