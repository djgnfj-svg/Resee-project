import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category } from '../types';
import { extractResults } from '../utils/helpers';
import BlockNoteEditor from './BlockNoteEditor';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  priority: 'low' | 'medium' | 'high';
}

interface ContentFormV2Props {
  onSubmit: (data: ContentFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  initialData?: Partial<ContentFormData>;
}

const ContentFormV2: React.FC<ContentFormV2Props> = ({
  onSubmit,
  onCancel,
  isLoading = false,
  initialData
}) => {
  const { 
    register, 
    handleSubmit, 
    formState: { errors }, 
    watch,
  } = useForm<ContentFormData>({
    mode: 'onChange',
    defaultValues: {
      priority: 'medium',
      ...initialData
    }
  });

  const [content, setContent] = useState<string>(initialData?.content || '');

  // Watch form values for real-time validation
  const watchedTitle = watch('title');
  const watchedPriority = watch('priority');

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  const onFormSubmit = useCallback((data: ContentFormData) => {
    onSubmit({
      ...data,
      content: content,
    });
  }, [content, onSubmit]);

  const handleImageUpload = async (file: File): Promise<string> => {
    try {
      const response = await contentAPI.uploadImage(file);
      return response.url;
    } catch (error) {
      console.error('Image upload failed:', error);
      throw error;
    }
  };

  const priorityOptions = [
    { value: 'high', label: '높음', color: 'red', emoji: '🔴', description: '매우 중요한 내용' },
    { value: 'medium', label: '보통', color: 'yellow', emoji: '🟡', description: '일반적인 내용' },
    { value: 'low', label: '낮음', color: 'green', emoji: '🟢', description: '참고용 내용' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden backdrop-blur-lg">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-4 sm:p-6 lg:p-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-white">
                  {initialData ? '콘텐츠 수정' : '새 콘텐츠 만들기'}
                </h1>
                <p className="text-sm sm:text-base text-indigo-100 mt-2">
                  정보를 입력하여 학습 콘텐츠를 만들어보세요
                </p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit(onFormSubmit)} className="p-8 space-y-8">
            {/* Title */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900">
                제목 <span className="text-red-500">*</span>
              </label>
              <input
                {...register('title', { 
                  required: '제목을 입력해주세요.',
                  minLength: { value: 3, message: '제목은 최소 3글자 이상이어야 합니다.' }
                })}
                type="text"
                className={`w-full px-4 py-4 text-lg border-2 rounded-xl transition-all duration-200 focus:outline-none ${
                  errors.title 
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
                    : watchedTitle && watchedTitle.trim().length >= 3
                    ? 'border-green-300 focus:border-green-500 focus:ring-green-200'
                    : 'border-gray-200 focus:border-indigo-500 focus:ring-indigo-200'
                } focus:ring-4`}
                placeholder="예: React Hook 완벽 가이드"
              />
              {errors.title && (
                <p className="text-sm text-red-600 flex items-center">
                  <span className="mr-1">❌</span>
                  {errors.title.message}
                </p>
              )}
              {watchedTitle && watchedTitle.trim().length >= 3 && !errors.title && (
                <p className="text-sm text-green-600 flex items-center">
                  <span className="mr-1">✅</span>
                  좋은 제목이에요!
                </p>
              )}
            </div>

            {/* Category */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900">
                카테고리
              </label>
              
              <select
                {...register('category')}
                className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-200 focus:outline-none transition-all duration-200"
              >
                <option value="">카테고리를 선택하세요 (선택사항)</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Priority */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900">
                중요도 <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {priorityOptions.map((option) => (
                  <label key={option.value} className="relative cursor-pointer">
                    <input
                      {...register('priority', { required: true })}
                      type="radio"
                      value={option.value}
                      className="sr-only"
                    />
                    <div className={`p-3 rounded-lg border-2 text-center transition-all duration-200 ${
                        watchedPriority === option.value
                          ? option.color === 'red' 
                            ? 'border-red-400 bg-red-50 ring-2 ring-red-200'
                            : option.color === 'yellow'
                            ? 'border-yellow-400 bg-yellow-50 ring-2 ring-yellow-200'
                            : 'border-green-400 bg-green-50 ring-2 ring-green-200'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}>
                      <div className="text-xl mb-1">{option.emoji}</div>
                      <div className="font-medium text-gray-900 text-sm">{option.label}</div>
                      <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900">
                내용 <span className="text-red-500">*</span>
              </label>
              <BlockNoteEditor
                content={content}
                onChange={setContent}
                placeholder="여기에 학습할 내용을 작성하세요..."
                className="w-full"
                onImageUpload={handleImageUpload}
              />
              {content.trim().length > 0 && content.trim().length < 10 && (
                <p className="text-sm text-yellow-600 flex items-center">
                  <span className="mr-1">⚠️</span>
                  내용을 조금 더 자세히 작성해주세요 (최소 10글자)
                </p>
              )}
              {content.trim().length >= 10 && (
                <p className="text-sm text-green-600 flex items-center">
                  <span className="mr-1">✅</span>
                  훌륭해요! {content.trim().length}글자 작성완료
                </p>
              )}
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between pt-8 mt-8 border-t border-gray-200">
              <button
                type="button"
                onClick={onCancel}
                className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200"
              >
                <span className="mr-2">✕</span>
                취소
              </button>
              
              <button
                type="submit"
                disabled={isLoading || !content || content.trim().length < 10}
                className={`inline-flex items-center px-8 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  !isLoading && content && content.trim().length >= 10
                    ? 'text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 shadow-lg'
                    : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                }`}
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
                    <span className="mr-2">💾</span>
                    완료
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ContentFormV2;