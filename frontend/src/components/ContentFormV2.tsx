import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category, ContentUsage } from '../types';
import { extractResults } from '../utils/helpers';
import TipTapEditor from './TipTapEditor';
import FormHeader from './contentform/FormHeader';
import TitleField from './contentform/TitleField';
import CategoryField from './contentform/CategoryField';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-indigo-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl overflow-hidden backdrop-blur-lg">
          {/* Header */}
          <FormHeader isEdit={!!initialData} />

          <form onSubmit={handleSubmit(onFormSubmit)} className="p-8 space-y-8">
            {/* Content Usage Info */}
            {contentUsage && (
              <div className={`p-4 rounded-xl ${isAtLimit ? 'bg-red-50 dark:bg-red-900/20' : 'bg-blue-50 dark:bg-blue-900/20'}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className={`text-sm font-medium ${isAtLimit ? 'text-red-800 dark:text-red-200' : 'text-blue-800 dark:text-blue-200'}`}>
                      콘텐츠 사용량: {contentUsage.current} / {contentUsage.limit}개
                    </p>
                    <p className={`text-xs mt-1 ${isAtLimit ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'}`}>
                      {isAtLimit
                        ? '콘텐츠 생성 제한에 도달했습니다. 더 많은 콘텐츠를 생성하려면 구독을 업그레이드하세요.'
                        : `${contentUsage.remaining}개 더 생성 가능 (${contentUsage.tier === 'free' ? '무료' : contentUsage.tier === 'basic' ? '베이직' : '프로'} 플랜)`
                      }
                    </p>
                  </div>
                  {isAtLimit && (
                    <button
                      type="button"
                      onClick={() => window.location.href = '/settings#subscription'}
                      className="px-4 py-2 text-xs font-medium text-white bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-all"
                    >
                      업그레이드
                    </button>
                  )}
                </div>
                <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${isAtLimit ? 'bg-red-500' : 'bg-blue-500'}`}
                    style={{ width: `${Math.min(contentUsage.percentage, 100)}%` }}
                  />
                </div>
              </div>
            )}

            {/* Title */}
            <TitleField
              register={register}
              errors={errors}
              watchedTitle={watchedTitle}
            />

            {/* Category */}
            <CategoryField
              register={register}
              setValue={setValue}
              categories={categories}
            />


            {/* Content */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
                내용 <span className="text-red-500">*</span>
              </label>
              <TipTapEditor
                content={content}
                onChange={setContent}
                placeholder="내용을 입력하세요. # 제목, **굵게**, *기울임*, 1. 목록 등이 바로 적용됩니다!"
                className="w-full"
              />
              {content.trim().length > 0 && content.trim().length < 10 && (
                <p className="text-sm text-yellow-600 dark:text-yellow-400 flex items-center">
                  <span className="mr-1">⚠️</span>
                  내용을 조금 더 자세히 작성해주세요 (최소 10글자)
                </p>
              )}
              {content.trim().length >= 10 && (
                <p className="text-sm text-green-600 dark:text-green-400 flex items-center">
                  <span className="mr-1">✅</span>
                  훌륭해요! {content.trim().length}글자 작성완료
                </p>
              )}
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between pt-8 mt-8 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onCancel}
                className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-200"
              >
                <span className="mr-2">✕</span>
                취소
              </button>
              
              <div className="flex space-x-3">

                <button
                  type="submit"
                  disabled={isLoading || !content || content.trim().length < 10 || !canCreateContent}
                  className={`inline-flex items-center px-8 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                    !isLoading && content && content.trim().length >= 10 && canCreateContent
                      ? 'text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 shadow-lg'
                      : 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 cursor-not-allowed'
                  }`}
                  title={!canCreateContent ? '콘텐츠 생성 제한에 도달했습니다' : ''}
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
            </div>
          </form>
        </div>
      </div>

    </div>
  );
};

export default ContentFormV2;