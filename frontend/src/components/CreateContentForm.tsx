import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category, ContentUsage } from '../types';
import { extractResults } from '../utils/helpers';
import TipTapEditor from './TipTapEditor';
import CategoryField from './contentform/CategoryField';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
}

interface CreateContentFormProps {
  onSubmit: (data: ContentFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
  initialData?: Partial<ContentFormData>;
}

const CreateContentForm: React.FC<CreateContentFormProps> = ({
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
    setValue,
  } = useForm<ContentFormData>({
    mode: 'onChange',
    defaultValues: {
      ...initialData
    }
  });

  const [content, setContent] = useState<string>(initialData?.content || '');
  const [contentUsage, setContentUsage] = useState<ContentUsage | null>(null);

  // Watch form values for real-time validation
  const watchedTitle = watch('title');

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Fetch content usage
  useQuery({
    queryKey: ['contents-usage'],
    queryFn: async () => {
      const response = await contentAPI.getContents();
      if (response.usage) {
        setContentUsage(response.usage);
      }
      return response;
    },
  });

  // Check if user can create content
  const canCreateContent = contentUsage ? contentUsage.can_create : true;
  const isAtLimit = contentUsage ? contentUsage.current >= contentUsage.limit : false;


  const onFormSubmit = useCallback((data: ContentFormData) => {
    onSubmit({
      ...data,
      content: content,
    });
  }, [content, onSubmit]);




  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12">
            {/* Title */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-4">
                <label className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  제목 <span className="text-red-500">*</span>
                </label>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {watchedTitle?.length || 0}/30
                </span>
              </div>
              <input
                {...register('title', {
                  required: '제목을 입력해주세요.',
                  minLength: { value: 1, message: '제목을 입력해주세요.' },
                  maxLength: { value: 30, message: '제목은 30자 이내로 입력해주세요.' }
                })}
                type="text"
                maxLength={30}
                className={`w-full px-4 py-3 text-2xl font-bold border rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${
                  errors.title
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-500 dark:border-red-500'
                    : watchedTitle && watchedTitle.trim().length >= 1
                    ? 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:focus:border-blue-400'
                    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:focus:border-blue-400'
                }`}
                placeholder="예: React Hook 완벽 가이드"
              />
              {errors.title && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                  {errors.title.message}
                </p>
              )}
            </div>

            {/* Category */}
            <div className="mb-6">
              <CategoryField
                register={register}
                setValue={setValue}
                categories={categories}
              />
            </div>

            {/* Content */}
            <div className="mb-8">
              <label className="block text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                내용 <span className="text-red-500">*</span>
              </label>
              <TipTapEditor
                content={content}
                onChange={setContent}
                placeholder="학습할 내용을 입력하세요. # 제목, **굵게**, *기울임*, 1. 목록 등이 바로 적용됩니다!"
                className="w-full"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                취소
              </button>

              <div className="flex items-center space-x-4">
                {/* Compact Content Usage Info */}
                {contentUsage && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {contentUsage.current}/{contentUsage.limit}
                    {isAtLimit && (
                      <button
                        type="button"
                        onClick={() => window.location.href = '/settings#subscription'}
                        className="ml-2 text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        업그레이드
                      </button>
                    )}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isLoading || !content || !canCreateContent}
                  className={`px-8 py-2.5 text-sm font-medium rounded-lg transition-all ${
                    !isLoading && content && canCreateContent
                      ? 'text-white bg-blue-600 hover:bg-blue-700 shadow-sm'
                      : 'text-gray-400 dark:text-gray-500 bg-gray-200 dark:bg-gray-700 cursor-not-allowed'
                  }`}
                  title={!canCreateContent ? '콘텐츠 생성 제한에 도달했습니다' : ''}
                >
                  {isLoading ? '저장 중...' : '저장'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateContentForm;