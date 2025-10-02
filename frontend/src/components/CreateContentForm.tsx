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
    defaultValues: {
      ...initialData
    }
  });

  const [content, setContent] = useState<string>(initialData?.content || '');
  const [contentUsage, setContentUsage] = useState<ContentUsage | null>(null);
  const [reviewMode, setReviewMode] = useState<'objective' | 'subjective'>(
    initialData?.review_mode || 'objective'
  );
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    is_valid: boolean;
    factual_accuracy: { score: number; issues: string[] };
    logical_consistency: { score: number; issues: string[] };
    title_relevance: { score: number; issues: string[] };
    overall_feedback: string;
  } | null>(null);

  // Watch form values for real-time validation
  const watchedTitle = watch('title');

  // 서술 평가 모드에서 콘텐츠 길이 검증
  const contentLength = content.trim().length;
  const isSubjectiveMode = reviewMode === 'subjective';
  const minContentLength = isSubjectiveMode ? 200 : 1;
  const hasValidContentLength = contentLength >= minContentLength;

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


  const onFormSubmit = useCallback((data: ContentFormData) => {
    onSubmit({
      ...data,
      content: content,
      review_mode: reviewMode,
    });
  }, [content, reviewMode, onSubmit]);

  const handleValidateContent = useCallback(async () => {
    const title = watchedTitle?.trim();
    if (!title || !hasValidContentLength) return;

    setIsValidating(true);
    setValidationResult(null);

    try {
      const result = await contentAPI.validateContent(title, content);
      setValidationResult(result);
    } catch (error: any) {
      alert(`AI 검증 실패: ${error.response?.data?.error || error.message}`);
    } finally {
      setIsValidating(false);
    }
  }, [watchedTitle, content, hasValidContentLength]);




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

            {/* Review Mode */}
            <div className="mb-6">
              <label className="block text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                복습 방식
              </label>
              <div className="flex gap-4">
                <label className={`flex-1 flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  reviewMode === 'objective'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="radio"
                    value="objective"
                    checked={reviewMode === 'objective'}
                    onChange={(e) => setReviewMode(e.target.value as 'objective')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div className="ml-3">
                    <div className="font-medium text-gray-900 dark:text-gray-100">기억 확인</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">내용을 보고 기억함/모름 선택</div>
                  </div>
                </label>

                <label className={`flex-1 flex items-center p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  reviewMode === 'subjective'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }`}>
                  <input
                    type="radio"
                    value="subjective"
                    checked={reviewMode === 'subjective'}
                    onChange={(e) => setReviewMode(e.target.value as 'subjective')}
                    className="w-4 h-4 text-blue-600"
                  />
                  <div className="ml-3">
                    <div className="font-medium text-gray-900 dark:text-gray-100">서술 평가</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">먼저 작성하고 AI가 자동 평가 (최소 200자)</div>
                  </div>
                </label>
              </div>
            </div>

            {/* Content */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <label className="block text-lg font-semibold text-gray-900 dark:text-gray-100">
                  내용 <span className="text-red-500">*</span>
                </label>
                {isSubjectiveMode && (
                  <span className={`text-sm ${hasValidContentLength ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {contentLength}/200자 {hasValidContentLength ? '✓' : '(서술 평가는 최소 200자)'}
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
                  서술 평가 모드는 AI가 판단할 수 있도록 최소 200자 이상의 콘텐츠가 필요합니다.
                </p>
              )}

              {/* AI 검증 결과 */}
              {validationResult && (
                <div className="mt-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-blue-200 dark:border-blue-700 rounded-xl p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    AI 검증 결과 {validationResult.is_valid ? '✓' : '⚠️'}
                  </h3>

                  <div className="space-y-3 mb-4">
                    {/* 사실적 정확성 */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">사실적 정확성</span>
                        <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{validationResult.factual_accuracy.score}점</span>
                      </div>
                      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
                          style={{ width: `${validationResult.factual_accuracy.score}%` }}
                        />
                      </div>
                      {validationResult.factual_accuracy.issues.length > 0 && (
                        <ul className="mt-1 text-xs text-red-600 dark:text-red-400 list-disc list-inside">
                          {validationResult.factual_accuracy.issues.map((issue, i) => (
                            <li key={i}>{issue}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* 논리적 일관성 */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">논리적 일관성</span>
                        <span className="text-sm font-bold text-purple-600 dark:text-purple-400">{validationResult.logical_consistency.score}점</span>
                      </div>
                      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-purple-600 transition-all duration-500"
                          style={{ width: `${validationResult.logical_consistency.score}%` }}
                        />
                      </div>
                      {validationResult.logical_consistency.issues.length > 0 && (
                        <ul className="mt-1 text-xs text-red-600 dark:text-red-400 list-disc list-inside">
                          {validationResult.logical_consistency.issues.map((issue, i) => (
                            <li key={i}>{issue}</li>
                          ))}
                        </ul>
                      )}
                    </div>

                    {/* 제목 적합성 */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">제목 적합성</span>
                        <span className="text-sm font-bold text-green-600 dark:text-green-400">{validationResult.title_relevance.score}점</span>
                      </div>
                      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                          style={{ width: `${validationResult.title_relevance.score}%` }}
                        />
                      </div>
                      {validationResult.title_relevance.issues.length > 0 && (
                        <ul className="mt-1 text-xs text-red-600 dark:text-red-400 list-disc list-inside">
                          {validationResult.title_relevance.issues.map((issue, i) => (
                            <li key={i}>{issue}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>

                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {validationResult.overall_feedback}
                  </p>
                </div>
              )}
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
                {/* AI 검증 버튼 (서술 평가 모드에서만) */}
                {isSubjectiveMode && (
                  <button
                    type="button"
                    onClick={handleValidateContent}
                    disabled={isValidating || !watchedTitle || !hasValidContentLength}
                    className={`px-6 py-2.5 text-sm font-medium rounded-lg transition-all ${
                      !isValidating && watchedTitle && hasValidContentLength
                        ? 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-300 dark:border-purple-700 hover:bg-purple-100 dark:hover:bg-purple-900/30'
                        : 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-800 border-2 border-gray-300 dark:border-gray-700 cursor-not-allowed'
                    }`}
                  >
                    {isValidating ? 'AI 검증 중...' : 'AI 검증'}
                  </button>
                )}

                <button
                  type="submit"
                  disabled={isLoading || !content || !canCreateContent || !hasValidContentLength}
                  className={`px-8 py-2.5 text-sm font-medium rounded-lg transition-all ${
                    !isLoading && content && canCreateContent && hasValidContentLength
                      ? 'text-white bg-blue-600 hover:bg-blue-700 shadow-sm'
                      : 'text-gray-400 dark:text-gray-500 bg-gray-200 dark:bg-gray-700 cursor-not-allowed'
                  }`}
                  title={
                    !canCreateContent
                      ? '콘텐츠 생성 제한에 도달했습니다'
                      : !hasValidContentLength && isSubjectiveMode
                      ? '서술 평가는 최소 200자 이상 필요합니다'
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