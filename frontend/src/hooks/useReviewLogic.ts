import { useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewAPI, contentAPI } from '../utils/api';
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
    resetReviewState,
  } = useReviewState();

  const queryClient = useQueryClient();

  // Fetch today's reviews
  const { data: reviewData, isLoading, refetch } = useQuery<ReviewSchedule[]>({
    queryKey: ['todayReviews', selectedCategory],
    queryFn: async () => {
      const params = selectedCategory !== 'all' ? `?category_slug=${selectedCategory}` : '';
      const data = await reviewAPI.getTodayReviews(params);

      // Always try to extract total_count if it exists
      if (data && typeof data === 'object' && 'total_count' in data) {
        setTotalSchedules((data as any).total_count || 0);
      }

      if (isTodayReviewsResponse(data)) {
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

      // Don't refetch immediately to avoid state reset
      // const { data: updatedReviews } = await refetch();

      // Update index based on current reviews (will be updated by invalidateQueries)
      if (reviews && reviews.length > 1) {
        const newIndex = Math.min(currentReviewIndex, reviews.length - 2); // -2 because one review was completed
        setCurrentReviewIndex(newIndex);
      } else {
        setCurrentReviewIndex(0);
      }
      
      setStartTime(Date.now());
    },
  });


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
    handleReviewComplete,
  };
};