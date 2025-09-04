import React, { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { contentAPI, apiClient } from '../utils/api';
import { Category } from '../types';
import { extractResults } from '../utils/helpers';
import TipTapEditor from './TipTapEditor';
import LoadingSpinner from './LoadingSpinner';
import { useAuth } from '../contexts/AuthContext';

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
  const { user } = useAuth();
  const { 
    register, 
    handleSubmit, 
    formState: { errors }, 
    watch,
    setValue,
  } = useForm<ContentFormData>({
    mode: 'onChange',
    defaultValues: {
      priority: 'medium',
      ...initialData
    }
  });

  const [content, setContent] = useState<string>(initialData?.content || '');
  
  // 카테고리 생성 관련 상태
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  
  // AI 콘텐츠 검사 관련 상태
  const [showCheckResult, setShowCheckResult] = useState(false);
  const [checkResult, setCheckResult] = useState<any>(null);
  const [isChecking, setIsChecking] = useState(false);
  
  const queryClient = useQueryClient();

  // Check if user can access AI features
  const canUseAI = user?.subscription?.is_active && user?.is_email_verified;

  // Watch form values for real-time validation
  const watchedTitle = watch('title');
  const watchedPriority = watch('priority');

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // 카테고리 생성 mutation
  const createCategoryMutation = useMutation({
    mutationFn: contentAPI.createCategory,
    onSuccess: (newCategory) => {
      // 기존 카테고리 목록에 새 카테고리를 즉시 추가
      queryClient.setQueryData<Category[]>(['categories'], (oldCategories = []) => {
        const categoryExists = oldCategories.some(cat => cat.id === newCategory.id);
        return categoryExists ? oldCategories : [...oldCategories, newCategory];
      });
      
      // React가 새 카테고리로 리렌더링할 시간을 준 후 자동 선택
      setTimeout(() => {
        setValue('category', newCategory.id);
      }, 100);
      
      // UI 초기화
      setShowCreateCategory(false);
      setNewCategoryName('');
      setIsCreatingCategory(false);
      
      alert(`카테고리 "${newCategory.name}"가 생성되어 선택되었습니다! 🎉`);
    },
    onError: (error: any) => {
      setIsCreatingCategory(false);
      const errorMessage = error.response?.data?.name?.[0] || '카테고리 생성에 실패했습니다.';
      alert(`오류: ${errorMessage}`);
    }
  });

  const handleCreateCategory = useCallback(async () => {
    const categoryName = newCategoryName.trim();
    if (!categoryName) return;
    
    setIsCreatingCategory(true);
    createCategoryMutation.mutate({ 
      name: categoryName,
      description: `개인 커스텀 카테고리: ${categoryName}` 
    });
  }, [newCategoryName, createCategoryMutation]);

  const onFormSubmit = useCallback((data: ContentFormData) => {
    onSubmit({
      ...data,
      content: content,
    });
  }, [content, onSubmit]);

  // AI 콘텐츠 검사 함수
  const handleAIContentCheck = async () => {
    if (!content.trim() || !watchedTitle?.trim()) {
      toast.error('제목과 내용을 입력해주세요.');
      return;
    }

    setIsChecking(true);
    try {
      const response = await apiClient.post('/api/ai-review/content-check/', {
        title: watchedTitle,
        content: content.trim()
      });
      
      setCheckResult(response.data);
      setShowCheckResult(true);
      toast.success('AI 콘텐츠 검사가 완료되었습니다!');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'AI 콘텐츠 검사에 실패했습니다.';
      toast.error(message);
    } finally {
      setIsChecking(false);
    }
  };


  const priorityOptions = [
    { value: 'high', label: '높음', color: 'red', emoji: '🔴', description: '매우 중요한 내용' },
    { value: 'medium', label: '보통', color: 'yellow', emoji: '🟡', description: '일반적인 내용' },
    { value: 'low', label: '낮음', color: 'green', emoji: '🟢', description: '참고용 내용' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-indigo-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl overflow-hidden backdrop-blur-lg">
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-4 sm:p-6 lg:p-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-white">
                  {initialData ? '콘텐츠 수정' : '새 콘텐츠 만들기'}
                </h1>
                <p className="text-sm sm:text-base text-indigo-100 dark:text-indigo-200 mt-2">
                  정보를 입력하여 학습 콘텐츠를 만들어보세요
                </p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit(onFormSubmit)} className="p-8 space-y-8">
            {/* Title */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
                제목 <span className="text-red-500">*</span>
              </label>
              <input
                {...register('title', { 
                  required: '제목을 입력해주세요.',
                  minLength: { value: 3, message: '제목은 최소 3글자 이상이어야 합니다.' }
                })}
                type="text"
                className={`w-full px-4 py-4 text-lg border-2 rounded-xl transition-all duration-200 focus:outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${
                  errors.title 
                    ? 'border-red-300 focus:border-red-500 focus:ring-red-200 dark:border-red-500 dark:focus:border-red-400 dark:focus:ring-red-800' 
                    : watchedTitle && watchedTitle.trim().length >= 3
                    ? 'border-green-300 focus:border-green-500 focus:ring-green-200 dark:border-green-500 dark:focus:border-green-400 dark:focus:ring-green-800'
                    : 'border-gray-200 focus:border-indigo-500 focus:ring-indigo-200 dark:border-gray-600 dark:focus:border-indigo-400 dark:focus:ring-indigo-800'
                } focus:ring-4`}
                placeholder="예: React Hook 완벽 가이드"
              />
              {errors.title && (
                <p className="text-sm text-red-600 dark:text-red-400 flex items-center">
                  <span className="mr-1">❌</span>
                  {errors.title.message}
                </p>
              )}
              {watchedTitle && watchedTitle.trim().length >= 3 && !errors.title && (
                <p className="text-sm text-green-600 dark:text-green-400 flex items-center">
                  <span className="mr-1">✅</span>
                  좋은 제목이에요!
                </p>
              )}
            </div>

            {/* Category */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
                카테고리
              </label>
              
              <div className="flex gap-2">
                <select
                  {...register('category')}
                  className="flex-1 px-4 py-4 border-2 border-gray-200 dark:border-gray-600 rounded-xl focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-4 focus:ring-indigo-200 dark:focus:ring-indigo-800 focus:outline-none transition-all duration-200 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">카테고리를 선택하세요 (선택사항)</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
                
                <button
                  type="button"
                  onClick={() => setShowCreateCategory(true)}
                  className="px-4 py-4 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium transition-colors duration-200 whitespace-nowrap"
                  title="새 카테고리 만들기"
                >
                  + 새 카테고리
                </button>
              </div>
              
              {/* 인라인 카테고리 생성 */}
              {showCreateCategory && (
                <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-600">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">새 카테고리 만들기</h4>
                      <button
                        type="button"
                        onClick={() => setShowCreateCategory(false)}
                        className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                      >
                        ✕
                      </button>
                    </div>
                    
                    <input
                      type="text"
                      value={newCategoryName}
                      onChange={(e) => setNewCategoryName(e.target.value)}
                      placeholder="카테고리 이름 (예: 📚 영어학습, 💻 프로그래밍)"
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      onKeyPress={(e) => e.key === 'Enter' && handleCreateCategory()}
                    />
                    
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={handleCreateCategory}
                        disabled={!newCategoryName.trim() || isCreatingCategory}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors duration-200"
                      >
                        {isCreatingCategory ? '생성중...' : '생성'}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowCreateCategory(false);
                          setNewCategoryName('');
                        }}
                        className="px-3 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors duration-200"
                      >
                        취소
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Priority */}
            <div className="space-y-3">
              <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
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
                            ? 'border-red-400 bg-red-50 dark:bg-red-900/20 ring-2 ring-red-200 dark:ring-red-800'
                            : option.color === 'yellow'
                            ? 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 ring-2 ring-yellow-200 dark:ring-yellow-800'
                            : 'border-green-400 bg-green-50 dark:bg-green-900/20 ring-2 ring-green-200 dark:ring-green-800'
                          : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                      }`}>
                      <div className="text-xl mb-1">{option.emoji}</div>
                      <div className="font-medium text-gray-900 dark:text-gray-100 text-sm">{option.label}</div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">{option.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

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
                {/* AI 콘텐츠 검사 버튼 */}
                {canUseAI && (
                  <button
                    type="button"
                    onClick={handleAIContentCheck}
                    disabled={isChecking || !content?.trim() || !watchedTitle?.trim() || content.trim().length < 300}
                    className={`inline-flex items-center px-6 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                      !isChecking && content?.trim() && watchedTitle?.trim() && content.trim().length >= 300
                        ? 'text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg'
                        : 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 cursor-not-allowed'
                    }`}
                    title={content.trim().length < 300 ? `AI 검사는 300자 이상에서 가능합니다 (현재 ${content.trim().length}자)` : ''}
                  >
                    {isChecking ? (
                      <LoadingSpinner className="w-4 h-4 mr-2" />
                    ) : (
                      <span className="mr-2">🤖</span>
                    )}
                    {isChecking ? 'AI 검사 중...' : content.trim().length < 300 ? 'AI 콘텐츠 검사 (300자 이상)' : 'AI 콘텐츠 검사'}
                  </button>
                )}

                <button
                  type="submit"
                  disabled={isLoading || !content || content.trim().length < 10}
                  className={`inline-flex items-center px-8 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                    !isLoading && content && content.trim().length >= 10
                      ? 'text-white bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 shadow-lg'
                      : 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-700 cursor-not-allowed'
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
            </div>
          </form>
        </div>
      </div>

      {/* AI 콘텐츠 검사 결과 모달 */}
      {showCheckResult && checkResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* 모달 헤더 */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">🤖</span>
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    AI 콘텐츠 검사 결과
                  </h3>
                </div>
                <button
                  onClick={() => setShowCheckResult(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* 검사 점수 */}
              <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg">
                <div className="text-center">
                  <div className={`text-3xl font-bold mb-2 ${
                    checkResult.score >= 80 ? 'text-green-600' :
                    checkResult.score >= 60 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {checkResult.score}/100
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">콘텐츠 품질 점수</div>
                </div>
              </div>

              {/* AI 피드백 */}
              <div className="mb-6">
                <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">📝 AI 피드백</h4>
                <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
                  <p className="text-gray-700 dark:text-gray-300">{checkResult.feedback}</p>
                </div>
              </div>

              {/* 장점 */}
              {checkResult.strengths && checkResult.strengths.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                    <span className="text-green-500 mr-2">✅</span>
                    좋은 점
                  </h4>
                  <div className="space-y-2">
                    {checkResult.strengths.map((strength: string, index: number) => (
                      <div key={index} className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 rounded-lg">
                        <span className="text-green-800 dark:text-green-200">{strength}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 개선사항 */}
              {checkResult.improvements && checkResult.improvements.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                    <span className="text-yellow-500 mr-2">💡</span>
                    개선 제안
                  </h4>
                  <div className="space-y-2">
                    {checkResult.improvements.map((improvement: string, index: number) => (
                      <div key={index} className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-3 rounded-lg">
                        <span className="text-yellow-800 dark:text-yellow-200">{improvement}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 종합 의견 */}
              <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <h5 className="font-medium text-blue-900 dark:text-blue-200 mb-2">🎯 종합 평가</h5>
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  {checkResult.score >= 80 
                    ? "훌륭한 콘텐츠입니다! 학습자에게 도움이 될 것 같습니다."
                    : checkResult.score >= 60
                    ? "괜찮은 콘텐츠네요. 몇 가지 개선사항을 반영하면 더 좋아질 것 같습니다."
                    : "내용을 다시 검토해보세요. AI 제안사항을 참고하여 개선해보시기 바랍니다."
                  }
                </p>
              </div>

              {/* 확인 버튼 */}
              <div className="text-right">
                <button
                  onClick={() => setShowCheckResult(false)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  확인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContentFormV2;