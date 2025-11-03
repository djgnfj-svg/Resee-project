import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category, ContentUsage } from '../types';
import { extractResults } from '../utils/helpers';
import TipTapEditor from './TipTapEditor';
import CategoryField from './contentform/CategoryField';
import ValidationResultCard from './contentform/ValidationResultCard';
import { useContentValidation } from '../hooks/useContentValidation';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  review_mode?: 'objective' | 'subjective';
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
    defaultValues: initialData
  });

  const [content, setContent] = useState<string>(initialData?.content || '');
  const [contentUsage, setContentUsage] = useState<ContentUsage | null>(null);
  const [reviewMode, setReviewMode] = useState<'objective' | 'subjective'>(
    initialData?.review_mode || 'objective'
  );

  const { isValidating, validationResult, validateContent } = useContentValidation();
  const watchedTitle = watch('title');

  const contentLength = content.trim().length;
  const isSubjectiveMode = reviewMode === 'subjective';
  const minContentLength = isSubjectiveMode ? 200 : 1;
  const hasValidContentLength = contentLength >= minContentLength;

  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

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

  const canCreateContent = contentUsage ? contentUsage.can_create : true;

  const onFormSubmit = useCallback((data: ContentFormData) => {
    onSubmit({
      ...data,
      content,
      review_mode: reviewMode,
    });
  }, [content, reviewMode, onSubmit]);

  const handleValidate = useCallback(() => {
    const title = watchedTitle?.trim();
    if (title && hasValidContentLength) {
      validateContent(title, content);
    }
  }, [watchedTitle, content, hasValidContentLength, validateContent]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form onSubmit={handleSubmit(onFormSubmit)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-12">
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
                    : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 dark:border-gray-600 dark:focus:border-indigo-400'
                }`}
                placeholder="예: React Hook 완벽 가이드"
              />
              {errors.title && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                  {errors.title.message}
                </p>
              )}
            </div>

            <div className="mb-6">
              <CategoryField
                register={register}
                setValue={setValue}
                categories={categories}
              />
            </div>

            <div className="mb-6">
              <label className="block text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                복습 방식
              </label>
              <div className="flex gap-4">
                <label className={`flex-1 flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  reviewMode === 'objective'
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="radio"
                    value="objective"
                    checked={reviewMode === 'objective'}
                    onChange={(e) => setReviewMode(e.target.value as 'objective')}
                    className="w-4 h-4 text-indigo-600"
                  />
                  <div className="ml-3">
                    <div className="font-medium text-gray-900 dark:text-gray-100">기억 확인</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">내용을 보고 기억함/모름 선택</div>
                  </div>
                </label>

                <label className={`flex-1 flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  reviewMode === 'subjective'
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="radio"
                    value="subjective"
                    checked={reviewMode === 'subjective'}
                    onChange={(e) => setReviewMode(e.target.value as 'subjective')}
                    className="w-4 h-4 text-indigo-600"
                  />
                  <div className="ml-3">
                    <div className="font-medium text-gray-900 dark:text-gray-100">주관식 평가</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">먼저 작성하고 AI가 자동 평가 (최소 200자)</div>
                  </div>
                </label>
              </div>
            </div>

            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <label className="block text-lg font-semibold text-gray-900 dark:text-gray-100">
                  내용 <span className="text-red-500">*</span>
                </label>
                {isSubjectiveMode && (
                  <span className={`text-sm ${hasValidContentLength ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {contentLength}/200자 {hasValidContentLength ? '✓' : '(주관식 평가는 최소 200자)'}
                  </span>
                )}
              </div>
              <TipTapEditor
                content={content}
                onChange={setContent}
                placeholder="학습할 내용을 입력하세요. # 제목, **굵게**, *기울임*, 1. 목록 등이 바로 적용됩니다!"
                className="w-full"
              />
              {isSubjectiveMode && !hasValidContentLength && content.length > 0 && (
                <p className="text-sm text-red-600 dark:text-red-400 mt-2">
                  주관식 평가 모드는 AI가 판단할 수 있도록 최소 200자 이상의 콘텐츠가 필요합니다.
                </p>
              )}

              {validationResult && <ValidationResultCard result={validationResult} />}
            </div>

            <div className="flex items-center justify-between pt-6 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-2.5 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                취소
              </button>

              <div className="flex items-center space-x-4">
                <button
                  type="button"
                  onClick={handleValidate}
                  disabled={isValidating || !watchedTitle || !hasValidContentLength}
                  className={`px-6 py-2.5 text-sm font-medium rounded-lg transition-all ${
                    !isValidating && watchedTitle && hasValidContentLength
                      ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-300 dark:border-purple-700 hover:bg-purple-100 dark:hover:bg-purple-900/30'
                      : 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-700 cursor-not-allowed'
                  }`}
                  title={!watchedTitle || !hasValidContentLength ? 'AI 검증을 사용하려면 제목과 충분한 내용을 입력하세요' : ''}
                >
                  {isValidating ? 'AI 검증 중...' : 'AI 검증'}
                </button>

                <button
                  type="submit"
                  disabled={isLoading || !content || !canCreateContent || !hasValidContentLength}
                  className={`px-8 py-2.5 text-sm font-medium rounded-lg transition-all ${
                    !isLoading && content && canCreateContent && hasValidContentLength
                      ? 'text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm'
                      : 'text-gray-400 dark:text-gray-500 bg-gray-200 dark:bg-gray-700 cursor-not-allowed'
                  }`}
                  title={
                    !canCreateContent
                      ? '콘텐츠 생성 제한에 도달했습니다'
                      : !hasValidContentLength && isSubjectiveMode
                      ? '주관식 평가는 최소 200자 이상 필요합니다'
                      : ''
                  }
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
