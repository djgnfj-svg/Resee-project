import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category, Tag } from '../types';
import TiptapEditor from './TiptapEditor';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  tag_ids?: number[];
  priority: 'low' | 'medium' | 'high';
}

interface ContentFormProps {
  onSubmit: (data: ContentFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  initialData?: Partial<ContentFormData>;
}

const ContentForm: React.FC<ContentFormProps> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData
}) => {
  const queryClient = useQueryClient();
  const { register, handleSubmit, formState: { errors }, watch } = useForm<ContentFormData>({
    defaultValues: {
      priority: 'medium',
      ...initialData
    }
  });

  const [selectedTags, setSelectedTags] = useState<number[]>(initialData?.tag_ids || []);
  const [content, setContent] = useState<string>(initialData?.content || '');
  const [showNewCategoryForm, setShowNewCategoryForm] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDescription, setNewCategoryDescription] = useState('');
  const [activeTab, setActiveTab] = useState<'basic' | 'content' | 'settings'>('basic');

  // Fetch categories and tags
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(res => res.results || res),
  });

  const { data: tags = [] } = useQuery<Tag[]>({
    queryKey: ['tags'],
    queryFn: () => contentAPI.getTags().then(res => res.results || res),
  });

  // Create category mutation
  const createCategoryMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) => 
      contentAPI.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setShowNewCategoryForm(false);
      setNewCategoryName('');
      setNewCategoryDescription('');
    },
  });

  const handleTagToggle = (tagId: number) => {
    setSelectedTags(prev => 
      prev.includes(tagId) 
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const onFormSubmit = (data: ContentFormData) => {
    if (!content.trim()) {
      alert('내용을 입력해주세요.');
      return;
    }
    
    console.log('ContentForm 제출 데이터:', {
      ...data,
      content: content,
      tag_ids: selectedTags
    });
    onSubmit({
      ...data,
      content: content,
      tag_ids: selectedTags
    });
  };

  const handleCreateCategory = () => {
    if (newCategoryName.trim()) {
      createCategoryMutation.mutate({
        name: newCategoryName.trim(),
        description: newCategoryDescription.trim()
      });
    }
  };

  const handleImageUpload = async (file: File): Promise<string> => {
    try {
      const response = await contentAPI.uploadImage(file);
      return response.url || response.image_url;
    } catch (error) {
      console.error('Image upload failed:', error);
      throw error;
    }
  };

  const watchedTitle = watch('title');
  const watchedPriority = watch('priority');
  
  const isBasicComplete = watchedTitle && watchedTitle.trim().length > 0;
  const isContentComplete = content && content.trim().length > 10;
  const canSubmit = isBasicComplete && isContentComplete;
  
  const tabs = [
    { id: 'basic', label: '기본 정보', icon: '📝', complete: isBasicComplete },
    { id: 'content', label: '콘텐츠 작성', icon: '✍️', complete: isContentComplete },
    { id: 'settings', label: '추가 설정', icon: '⚙️', complete: true }
  ];
  
  const nextTab = () => {
    if (activeTab === 'basic' && isBasicComplete) {
      setActiveTab('content');
    } else if (activeTab === 'content' && isContentComplete) {
      setActiveTab('settings');
    }
  };
  
  const prevTab = () => {
    if (activeTab === 'settings') {
      setActiveTab('content');
    } else if (activeTab === 'content') {
      setActiveTab('basic');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-4">
      <div className="max-w-4xl mx-auto px-4">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white">
                  {initialData ? '콘텐츠 수정' : '새 콘텐츠 작성'}
                </h1>
                <p className="text-blue-100 mt-1">
                  단계별로 정보를 입력하여 콘텐츠를 만들어보세요
                </p>
              </div>
              <div className="text-white text-sm bg-white/20 px-3 py-1 rounded-full">
                {Math.round(((activeTab === 'basic' ? 1 : activeTab === 'content' ? 2 : 3) / 3) * 100)}%
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 bg-gray-50">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="text-lg">{tab.icon}</span>
                  <span>{tab.label}</span>
                  {tab.complete && (
                    <span className="ml-2 text-green-500">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>

          <form onSubmit={handleSubmit(onFormSubmit)} className="p-6">
            {/* Tab Content */}
            <div className="mt-6">
              {activeTab === 'basic' && (
                <div className="space-y-6">
                  <div className="text-center mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">기본 정보 입력</h2>
                    <p className="text-gray-600">콘텐츠의 제목과 카테고리, 중요도를 설정하세요</p>
                  </div>

                  {/* Title */}
                  <div className="space-y-2">
                    <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                      제목 *
                    </label>
                    <input
                      {...register('title', { required: '제목을 입력해주세요.' })}
                      type="text"
                      className="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200"
                      placeholder="예: React Hook 사용법 정리"
                    />
                    {errors.title && (
                      <p className="text-sm text-red-600 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {errors.title.message}
                      </p>
                    )}
                  </div>

                  {/* Category */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label htmlFor="category" className="block text-sm font-medium text-gray-700">
                        카테고리
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowNewCategoryForm(!showNewCategoryForm)}
                        className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                      >
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                        </svg>
                        새 카테고리
                      </button>
                    </div>
                    
                    {showNewCategoryForm && (
                      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <div className="space-y-3">
                          <input
                            type="text"
                            value={newCategoryName}
                            onChange={(e) => setNewCategoryName(e.target.value)}
                            placeholder="카테고리 이름"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          />
                          <div className="flex space-x-2">
                            <button
                              type="button"
                              onClick={handleCreateCategory}
                              disabled={!newCategoryName.trim() || createCategoryMutation.isPending}
                              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 text-sm"
                            >
                              {createCategoryMutation.isPending ? '생성 중...' : '생성'}
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                setShowNewCategoryForm(false);
                                setNewCategoryName('');
                                setNewCategoryDescription('');
                              }}
                              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 text-sm"
                            >
                              취소
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <select
                      {...register('category')}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">카테고리 선택 (선택사항)</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Priority */}
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-700">
                      중요도 *
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { value: 'high', label: '높음', color: 'red', description: '매우 중요' },
                        { value: 'medium', label: '보통', color: 'yellow', description: '일반적' },
                        { value: 'low', label: '낮음', color: 'green', description: '참고용' }
                      ].map((option) => (
                        <label key={option.value} className="relative">
                          <input
                            {...register('priority', { required: true })}
                            type="radio"
                            value={option.value}
                            className="sr-only"
                          />
                          <div className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                            watchedPriority === option.value
                              ? option.color === 'red' ? 'border-red-500 bg-red-50' :
                                option.color === 'yellow' ? 'border-yellow-500 bg-yellow-50' :
                                'border-green-500 bg-green-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}>
                            <div className="text-center">
                              <div className={`w-8 h-8 rounded-full mx-auto mb-2 ${
                                option.color === 'red' ? 'bg-red-500' :
                                option.color === 'yellow' ? 'bg-yellow-500' : 'bg-green-500'
                              }`}></div>
                              <div className="font-medium text-gray-900">{option.label}</div>
                              <div className="text-sm text-gray-600">{option.description}</div>
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'content' && (
                <div className="space-y-6">
                  <div className="text-center mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">콘텐츠 작성</h2>
                    <p className="text-gray-600">리치 텍스트 에디터로 내용을 작성하세요</p>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                      내용 *
                    </label>
                    <TiptapEditor
                      content={content}
                      onChange={setContent}
                      placeholder="여기에 내용을 입력하세요..."
                      className="w-full"
                      onImageUpload={handleImageUpload}
                    />
                    {!content.trim() && (
                      <p className="text-sm text-red-600 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        내용을 입력해주세요
                      </p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'settings' && (
                <div className="space-y-6">
                  <div className="text-center mb-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">추가 설정</h2>
                    <p className="text-gray-600">태그를 선택하여 콘텐츠를 더 세밀하게 분류할 수 있습니다</p>
                  </div>

                  {/* Tags */}
                  {tags.length > 0 ? (
                    <div className="space-y-3">
                      <label className="block text-sm font-medium text-gray-700">
                        태그 선택 (선택사항)
                      </label>
                      <div className="flex flex-wrap gap-2">
                        {tags.map((tag) => (
                          <button
                            key={tag.id}
                            type="button"
                            onClick={() => handleTagToggle(tag.id)}
                            className={`inline-flex items-center px-3 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                              selectedTags.includes(tag.id)
                                ? 'bg-blue-100 text-blue-800 border-2 border-blue-300'
                                : 'bg-gray-100 text-gray-700 border-2 border-gray-200 hover:bg-gray-200'
                            }`}
                          >
                            <span className="mr-1">
                              {selectedTags.includes(tag.id) ? '✓' : '+'}
                            </span>
                            {tag.name}
                          </button>
                        ))}
                      </div>
                      {selectedTags.length > 0 && (
                        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                          <p className="text-sm text-blue-800">
                            선택된 태그: {selectedTags.length}개
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="text-gray-400 text-4xl mb-4">🏷️</div>
                      <p className="text-gray-600">사용 가능한 태그가 없습니다</p>
                      <p className="text-sm text-gray-500 mt-2">관리자에게 태그 생성을 요청하세요</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Navigation and Submit buttons */}
            <div className="flex justify-between items-center pt-8 border-t border-gray-200">
              <div className="flex space-x-3">
                {activeTab !== 'basic' && (
                  <button
                    type="button"
                    onClick={prevTab}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-200"
                  >
                    <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    이전
                  </button>
                )}
                
                <button
                  type="button"
                  onClick={onCancel}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors duration-200"
                >
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  취소
                </button>
              </div>
              
              <div className="flex space-x-3">
                {activeTab !== 'settings' && (
                  <button
                    type="button"
                    onClick={nextTab}
                    disabled={(activeTab === 'basic' && !isBasicComplete) || (activeTab === 'content' && !isContentComplete)}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    다음
                    <svg className="w-4 h-4 ml-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                )}
                
                {activeTab === 'settings' && (
                  <button
                    type="submit"
                    disabled={isLoading || !canSubmit}
                    className="inline-flex items-center px-6 py-2 text-sm font-medium text-white bg-gradient-to-r from-green-600 to-green-700 rounded-lg hover:from-green-700 hover:to-green-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        저장 중...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        저장하기
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ContentForm;