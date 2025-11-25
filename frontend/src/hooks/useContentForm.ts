import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { contentAPI } from '../utils/api';
import { Category, ContentUsage, ReviewMode, CreateContentData } from '../types';
import { extractResults } from '../utils/helpers';

interface UseContentFormProps {
  initialData?: Partial<CreateContentData>;
  onSubmit: (data: CreateContentData) => void;
}

export const useContentForm = ({ initialData, onSubmit }: UseContentFormProps) => {
  const [content, setContent] = useState<string>(initialData?.content || '');
  const [contentUsage, setContentUsage] = useState<ContentUsage | null>(null);
  const [reviewMode, setReviewMode] = useState<ReviewMode>(
    initialData?.review_mode || 'objective'
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<CreateContentData>({
    mode: 'onChange',
    defaultValues: initialData,
  });

  const watchedTitle = watch('title');

  // Calculate content validation
  const contentLength = content.trim().length;
  const needsLongContent = reviewMode === 'descriptive' || reviewMode === 'multiple_choice';
  const minContentLength = needsLongContent ? 200 : 1;
  const hasValidContentLength = contentLength >= minContentLength;

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Fetch content usage
  useQuery({
    queryKey: ['content-usage'],
    queryFn: async () => {
      const response = await contentAPI.getContents();
      if (response.usage) {
        setContentUsage(response.usage);
      }
      return response;
    },
  });

  const canCreateContent = contentUsage ? contentUsage.can_create : true;

  const onFormSubmit = useCallback(
    (data: CreateContentData) => {
      onSubmit({
        ...data,
        content,
        review_mode: reviewMode,
      });
    },
    [content, reviewMode, onSubmit]
  );

  return {
    // Form
    register,
    handleSubmit,
    errors,
    watchedTitle,
    setValue,
    onFormSubmit,

    // Content state
    content,
    setContent,
    contentLength,
    hasValidContentLength,
    needsLongContent,
    minContentLength,

    // Review mode
    reviewMode,
    setReviewMode,

    // Usage & categories
    canCreateContent,
    categories,
  };
};
