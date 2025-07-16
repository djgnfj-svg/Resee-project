import React, { useState, useCallback, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { contentAPI } from '../utils/api';
import { Category, Tag } from '../types';
import NotionEditor from './NotionEditor';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  tag_ids?: number[];
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
  const queryClient = useQueryClient();
  const { 
    register, 
    handleSubmit, 
    formState: { errors, isValid }, 
    watch,
    setValue,
    trigger
  } = useForm<ContentFormData>({
    mode: 'onChange',
    defaultValues: {
      priority: 'medium',
      ...initialData
    }
  });

  const [selectedTags, setSelectedTags] = useState<number[]>(initialData?.tag_ids || []);
  const [content, setContent] = useState<string>(initialData?.content || '');
  const [activeStep, setActiveStep] = useState(0);
  const [tagSearchQuery, setTagSearchQuery] = useState('');
  const [showNewCategoryModal, setShowNewCategoryModal] = useState(false);
  const [newCategoryData, setNewCategoryData] = useState({ name: '', description: '' });

  // Watch form values for real-time validation
  const watchedTitle = watch('title');
  const watchedCategory = watch('category');
  const watchedPriority = watch('priority');

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
    onSuccess: (newCategory) => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
      setValue('category', newCategory.id);
      setShowNewCategoryModal(false);
      setNewCategoryData({ name: '', description: '' });
    },
  });

  // Filtered tags based on search
  const filteredTags = useMemo(() => {
    if (!tagSearchQuery) return tags;
    return tags.filter(tag => 
      tag.name.toLowerCase().includes(tagSearchQuery.toLowerCase())
    );
  }, [tags, tagSearchQuery]);

  // Form steps configuration
  const steps = [
    {
      id: 'basic',
      title: '기본 정보',
      description: '제목과 카테고리를 설정하세요',
      icon: '📝',
      isValid: watchedTitle && watchedTitle.trim().length >= 3,
      fields: ['title', 'category', 'priority']
    },
    {
      id: 'content',
      title: '콘텐츠 작성',
      description: '학습할 내용을 작성하세요',
      icon: '✍️',
      isValid: content && content.trim().length >= 10,
      fields: ['content']
    },
    {
      id: 'tags',
      title: '태그 설정',
      description: '콘텐츠를 분류할 태그를 선택하세요',
      icon: '🏷️',
      isValid: true, // Tags are optional
      fields: ['tag_ids']
    }
  ];

  const currentStep = steps[activeStep];
  const isLastStep = activeStep === steps.length - 1;
  const canProceed = currentStep.isValid;
  const allStepsValid = steps.every(step => step.isValid);

  const handleNext = useCallback(async () => {
    const isStepValid = await trigger(currentStep.fields as any);
    if (isStepValid && canProceed && !isLastStep) {
      setActiveStep(prev => prev + 1);
    }
  }, [activeStep, canProceed, isLastStep, trigger, currentStep.fields]);

  const handlePrevious = useCallback(() => {
    if (activeStep > 0) {
      setActiveStep(prev => prev - 1);
    }
  }, [activeStep]);

  const handleTagToggle = useCallback((tagId: number) => {
    setSelectedTags(prev => 
      prev.includes(tagId) 
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  }, []);

  const onFormSubmit = useCallback((data: ContentFormData) => {
    onSubmit({
      ...data,
      content: content,
      tag_ids: selectedTags
    });
  }, [content, selectedTags, onSubmit]);

  const handleImageUpload = async (file: File): Promise<string> => {
    try {
      const response = await contentAPI.uploadImage(file);
      return response.url || response.image_url;
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
      <div className="max-w-4xl mx-auto px-4 py-8">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-3xl shadow-2xl overflow-hidden backdrop-blur-lg"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-8">
            <div className="flex items-center justify-between">
              <div>
                <motion.h1 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-3xl font-bold text-white"
                >
                  {initialData ? '콘텐츠 수정' : '새 콘텐츠 만들기'}
                </motion.h1>
                <motion.p 
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  className="text-indigo-100 mt-2"
                >
                  단계별로 정보를 입력하여 학습 콘텐츠를 만들어보세요
                </motion.p>
              </div>
              <motion.div 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-white/20 backdrop-blur-sm rounded-full px-4 py-2"
              >
                <span className="text-white text-sm font-medium">
                  {Math.round(((activeStep + 1) / steps.length) * 100)}% 완료
                </span>
              </motion.div>
            </div>
          </div>

          {/* Progress Steps */}
          <div className="px-8 py-6 bg-gray-50 border-b">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <div key={step.id} className="flex items-center">
                  <motion.div
                    initial={{ scale: 0.8, opacity: 0.5 }}
                    animate={{ 
                      scale: index === activeStep ? 1.1 : 1,
                      opacity: index <= activeStep ? 1 : 0.5
                    }}
                    className={`relative flex items-center justify-center w-12 h-12 rounded-full text-2xl font-medium transition-all duration-300 ${
                      index < activeStep 
                        ? 'bg-green-500 text-white shadow-lg' 
                        : index === activeStep
                        ? 'bg-indigo-600 text-white shadow-lg ring-4 ring-indigo-200'
                        : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    {index < activeStep ? '✓' : step.icon}
                  </motion.div>
                  <div className="ml-4 min-w-0 flex-1">
                    <p className={`text-sm font-medium ${
                      index === activeStep ? 'text-indigo-600' : 
                      index < activeStep ? 'text-green-600' : 'text-gray-400'
                    }`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`w-16 h-1 mx-4 rounded-full transition-all duration-300 ${
                      index < activeStep ? 'bg-green-500' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit(onFormSubmit)} className="p-8">
            <AnimatePresence mode="wait">
              {/* Step 1: Basic Info */}
              {activeStep === 0 && (
                <motion.div
                  key="basic"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
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
                      <motion.p 
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-sm text-red-600 flex items-center"
                      >
                        <span className="mr-1">❌</span>
                        {errors.title.message}
                      </motion.p>
                    )}
                    {watchedTitle && watchedTitle.trim().length >= 3 && !errors.title && (
                      <motion.p 
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-sm text-green-600 flex items-center"
                      >
                        <span className="mr-1">✅</span>
                        좋은 제목이에요!
                      </motion.p>
                    )}
                  </div>

                  {/* Category */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label className="block text-sm font-semibold text-gray-900">
                        카테고리
                      </label>
                      <button
                        type="button"
                        onClick={() => setShowNewCategoryModal(true)}
                        className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center font-medium"
                      >
                        <span className="mr-1">➕</span>
                        새 카테고리
                      </button>
                    </div>
                    
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
                  <div className="space-y-4">
                    <label className="block text-sm font-semibold text-gray-900">
                      중요도 <span className="text-red-500">*</span>
                    </label>
                    <div className="grid grid-cols-3 gap-4">
                      {priorityOptions.map((option) => (
                        <label key={option.value} className="relative cursor-pointer">
                          <input
                            {...register('priority', { required: true })}
                            type="radio"
                            value={option.value}
                            className="sr-only"
                          />
                          <motion.div 
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className={`p-6 rounded-xl border-2 text-center transition-all duration-200 ${
                              watchedPriority === option.value
                                ? option.color === 'red' 
                                  ? 'border-red-400 bg-red-50 ring-4 ring-red-200'
                                  : option.color === 'yellow'
                                  ? 'border-yellow-400 bg-yellow-50 ring-4 ring-yellow-200'
                                  : 'border-green-400 bg-green-50 ring-4 ring-green-200'
                                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                            }`}
                          >
                            <div className="text-3xl mb-2">{option.emoji}</div>
                            <div className="font-semibold text-gray-900">{option.label}</div>
                            <div className="text-xs text-gray-600 mt-1">{option.description}</div>
                          </motion.div>
                        </label>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Step 2: Content */}
              {activeStep === 1 && (
                <motion.div
                  key="content"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  <div className="text-center mb-8">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">콘텐츠 작성</h3>
                    <p className="text-gray-600">Notion 스타일 에디터로 풍부한 내용을 작성하세요</p>
                  </div>

                  <div className="space-y-3">
                    <label className="block text-sm font-semibold text-gray-900">
                      내용 <span className="text-red-500">*</span>
                    </label>
                    <NotionEditor
                      content={content}
                      onChange={setContent}
                      placeholder="여기에 학습할 내용을 작성하세요. '/'를 입력하여 다양한 포맷을 사용할 수 있습니다..."
                      className="w-full"
                      onImageUpload={handleImageUpload}
                    />
                    {content.trim().length > 0 && content.trim().length < 10 && (
                      <motion.p 
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-sm text-yellow-600 flex items-center"
                      >
                        <span className="mr-1">⚠️</span>
                        내용을 조금 더 자세히 작성해주세요 (최소 10글자)
                      </motion.p>
                    )}
                    {content.trim().length >= 10 && (
                      <motion.p 
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-sm text-green-600 flex items-center"
                      >
                        <span className="mr-1">✅</span>
                        훌륭해요! {content.trim().length}글자 작성완료
                      </motion.p>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Step 3: Tags */}
              {activeStep === 2 && (
                <motion.div
                  key="tags"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  <div className="text-center mb-8">
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">태그 설정</h3>
                    <p className="text-gray-600">콘텐츠를 쉽게 찾을 수 있도록 태그를 선택하세요</p>
                  </div>

                  {tags.length > 0 ? (
                    <div className="space-y-4">
                      {/* Tag Search */}
                      <div className="relative">
                        <input
                          type="text"
                          value={tagSearchQuery}
                          onChange={(e) => setTagSearchQuery(e.target.value)}
                          placeholder="태그 검색..."
                          className="w-full px-4 py-3 pl-10 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-200 focus:outline-none transition-all duration-200"
                        />
                        <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                          🔍
                        </div>
                      </div>

                      {/* Tags Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 max-h-80 overflow-y-auto">
                        {filteredTags.map((tag) => (
                          <motion.button
                            key={tag.id}
                            type="button"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => handleTagToggle(tag.id)}
                            className={`p-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                              selectedTags.includes(tag.id)
                                ? 'bg-indigo-100 text-indigo-700 border-2 border-indigo-300 ring-2 ring-indigo-200'
                                : 'bg-gray-50 text-gray-700 border-2 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
                            }`}
                          >
                            <span className="mr-1">
                              {selectedTags.includes(tag.id) ? '✓' : '+'}
                            </span>
                            {tag.name}
                          </motion.button>
                        ))}
                      </div>

                      {selectedTags.length > 0 && (
                        <motion.div 
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mt-4 p-4 bg-indigo-50 rounded-xl border border-indigo-200"
                        >
                          <p className="text-sm text-indigo-800 font-medium">
                            선택된 태그: {selectedTags.length}개
                          </p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            {selectedTags.map(tagId => {
                              const tag = tags.find(t => t.id === tagId);
                              return tag ? (
                                <span key={tagId} className="inline-flex items-center px-2 py-1 rounded-md bg-indigo-100 text-indigo-700 text-xs">
                                  {tag.name}
                                </span>
                              ) : null;
                            })}
                          </div>
                        </motion.div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-16">
                      <div className="text-6xl mb-4">🏷️</div>
                      <h4 className="text-lg font-medium text-gray-900 mb-2">아직 태그가 없어요</h4>
                      <p className="text-gray-600">관리자에게 태그 생성을 요청하거나 나중에 추가할 수 있습니다</p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Navigation */}
            <div className="flex items-center justify-between pt-8 mt-8 border-t border-gray-200">
              <div className="flex space-x-3">
                {activeStep > 0 && (
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="button"
                    onClick={handlePrevious}
                    className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200"
                  >
                    <span className="mr-2">←</span>
                    이전
                  </motion.button>
                )}
                
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="button"
                  onClick={onCancel}
                  className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200"
                >
                  <span className="mr-2">✕</span>
                  취소
                </motion.button>
              </div>
              
              <div className="flex space-x-3">
                {!isLastStep ? (
                  <motion.button
                    whileHover={{ scale: canProceed ? 1.02 : 1 }}
                    whileTap={{ scale: canProceed ? 0.98 : 1 }}
                    type="button"
                    onClick={handleNext}
                    disabled={!canProceed}
                    className={`inline-flex items-center px-8 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                      canProceed
                        ? 'text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg'
                        : 'text-gray-400 bg-gray-100 cursor-not-allowed'
                    }`}
                  >
                    다음
                    <span className="ml-2">→</span>
                  </motion.button>
                ) : (
                  <motion.button
                    whileHover={{ scale: allStepsValid && !isLoading ? 1.02 : 1 }}
                    whileTap={{ scale: allStepsValid && !isLoading ? 0.98 : 1 }}
                    type="submit"
                    disabled={isLoading || !allStepsValid}
                    className={`inline-flex items-center px-8 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                      allStepsValid && !isLoading
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
                  </motion.button>
                )}
              </div>
            </div>
          </form>
        </motion.div>
      </div>

      {/* New Category Modal */}
      <AnimatePresence>
        {showNewCategoryModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowNewCategoryModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 w-full max-w-md shadow-2xl"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">새 카테고리 만들기</h3>
              <div className="space-y-4">
                <input
                  type="text"
                  value={newCategoryData.name}
                  onChange={(e) => setNewCategoryData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="카테고리 이름"
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-200 focus:outline-none transition-all duration-200"
                />
                <textarea
                  value={newCategoryData.description}
                  onChange={(e) => setNewCategoryData(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="카테고리 설명 (선택사항)"
                  rows={3}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-200 focus:outline-none transition-all duration-200 resize-none"
                />
                <div className="flex space-x-3 pt-4">
                  <button
                    onClick={() => setShowNewCategoryModal(false)}
                    className="flex-1 px-4 py-3 text-sm font-medium text-gray-700 bg-gray-100 rounded-xl hover:bg-gray-200 transition-all duration-200"
                  >
                    취소
                  </button>
                  <button
                    onClick={() => createCategoryMutation.mutate(newCategoryData)}
                    disabled={!newCategoryData.name.trim() || createCategoryMutation.isPending}
                    className="flex-1 px-4 py-3 text-sm font-medium text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {createCategoryMutation.isPending ? '생성 중...' : '생성'}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ContentFormV2;