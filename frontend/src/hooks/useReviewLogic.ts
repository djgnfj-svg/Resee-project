import { useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewAPI, contentAPI } from '../utils/api';
import { aiReviewAPI } from '../utils/ai-review-api';
import { ReviewSchedule, Category, TodayReviewsResponse } from '../types';
import { extractResults } from '../utils/helpers';
import { useReviewState } from './useReviewState';

// Type guard function
const isTodayReviewsResponse = (data: any): data is TodayReviewsResponse => {
  if (!data || typeof data !== 'object') return false;
  
  const hasRequiredProps = 
    'results' in data && Array.isArray(data.results) &&
    'total_count' in data && typeof data.total_count === 'number' &&
    'count' in data && typeof data.count === 'number';
  
  if (!hasRequiredProps) return false;
  
  return data.results.every((item: any) => 
    item && 
    typeof item === 'object' &&
    typeof item.id === 'number' &&
    typeof item.next_review_date === 'string' &&
    item.content && 
    typeof item.content === 'object'
  );
};

export const useReviewLogic = () => {
  const {
    selectedCategory,
    currentReviewIndex,
    setCurrentReviewIndex,
    startTime,
    setStartTime,
    reviewsCompleted,
    setReviewsCompleted,
    setTotalSchedules,
    setShowContent,
    setIsFlipped,
    userExplanation,
    setEvaluationResult,
    setShowEvaluation,
    setIsEvaluating,
    setUserExplanation,
    resetReviewState,
  } = useReviewState();

  const queryClient = useQueryClient();

  // Fetch today's reviews
  const { data: reviewData, isLoading, refetch } = useQuery<ReviewSchedule[]>({
    queryKey: ['todayReviews', selectedCategory],
    queryFn: async () => {
      const params = selectedCategory !== 'all' ? `?category_slug=${selectedCategory}` : '';
      const data = await reviewAPI.getTodayReviews(params);
      
      if (isTodayReviewsResponse(data)) {
        setTotalSchedules(data.total_count || 0);
        return data.results;
      } else {
        return extractResults(data) as ReviewSchedule[];
      }
    }
  });

  const reviews: ReviewSchedule[] = reviewData || [];

  // Fetch categories
  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ['categories'],
    queryFn: () => contentAPI.getCategories().then(extractResults),
  });

  // Complete review mutation
  const completeReviewMutation = useMutation({
    mutationFn: reviewAPI.completeReview,
    onSuccess: async () => {
      setReviewsCompleted(prev => prev + 1);
      setShowContent(false);
      setIsFlipped(false);
      
      queryClient.invalidateQueries({ queryKey: ['todayReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['learning-calendar'] });
      queryClient.invalidateQueries({ queryKey: ['advanced-analytics'] });
      
      const { data: updatedReviews } = await refetch();
      
      if (updatedReviews && updatedReviews.length > 0) {
        const newIndex = Math.min(currentReviewIndex, updatedReviews.length - 1);
        setCurrentReviewIndex(newIndex);
      } else {
        setCurrentReviewIndex(0);
      }
      
      setStartTime(Date.now());
    },
  });

  // Explanation evaluation mutation
  const evaluateExplanationMutation = useMutation({
    mutationFn: aiReviewAPI.evaluateExplanation,
    onSuccess: (result) => {
      setEvaluationResult(result);
      setShowEvaluation(true);
      setIsEvaluating(false);
    },
    onError: (error) => {
      console.error('Explanation evaluation failed:', error);
      setIsEvaluating(false);
    },
  });

  const handleExplanationSubmit = useCallback(() => {
    const currentReview = reviews[currentReviewIndex];
    if (!userExplanation.trim() || !currentReview) return;

    // AI 기능 준비중 메시지 표시
    import('react-hot-toast').then(({ default: toast }) => {
      toast('🚧 AI 기능은 현재 준비 중입니다');
    });
    return;

    /* 준비중 - 아래 코드는 일시적으로 비활성화
    setIsEvaluating(true);
    evaluateExplanationMutation.mutate({
      content_id: currentReview.content.id,
      user_explanation: userExplanation.trim(),
    });
    */
  }, [userExplanation, reviews, currentReviewIndex, evaluateExplanationMutation, setIsEvaluating]);

  const handleExplanationReviewComplete = useCallback((result: 'remembered' | 'partial' | 'forgot') => {
    setUserExplanation('');
    setEvaluationResult(null);
    setShowEvaluation(false);
    handleReviewComplete(result);
  }, [setUserExplanation, setEvaluationResult, setShowEvaluation]);

  const handleReviewComplete = useCallback((result: 'remembered' | 'partial' | 'forgot') => {
    const currentReview = reviews[currentReviewIndex];
    if (currentReview) {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      
      const messages = {
        'remembered': '✅ 잘 기억하고 있어요!',
        'partial': '🤔 애매하군요, 다시 복습할게요.',
        'forgot': '😅 괜찮아요, 다시 배워봐요!'
      };
      alert('Success: ' + messages[result]);
      
      completeReviewMutation.mutate({
        content_id: currentReview.content.id,
        result: result,
        time_spent: timeSpent,
      });
    }
  }, [reviews, currentReviewIndex, startTime, completeReviewMutation]);

  // Reset flip state when review changes
  useEffect(() => {
    resetReviewState();
  }, [currentReviewIndex, resetReviewState]);

  const currentReview = reviews[currentReviewIndex];
  const progress = reviews.length > 0 ? (reviewsCompleted / (reviews.length + reviewsCompleted)) * 100 : 0;

  return {
    reviews,
    categories,
    currentReview,
    progress,
    isLoading,
    completeReviewMutation,
    evaluateExplanationMutation,
    handleExplanationSubmit,
    handleExplanationReviewComplete,
    handleReviewComplete,
  };
};