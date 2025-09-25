import { useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewAPI } from '../utils/api';
import { ReviewSchedule, TodayReviewsResponse } from '../types';
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

export const useReviewLogic = (onShowToast?: (message: string, type: 'success' | 'info' | 'warning' | 'error') => void) => {
  const {
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

  // Fetch today's reviews (always all categories)
  const { data: reviewData, isLoading } = useQuery<ReviewSchedule[]>({
    queryKey: ['todayReviews'],
    queryFn: async () => {
      const data = await reviewAPI.getTodayReviews('');

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

  const reviews: ReviewSchedule[] = useMemo(() => reviewData || [], [reviewData]);

  // Complete review mutation
  const completeReviewMutation = useMutation({
    mutationFn: reviewAPI.completeReview,
    onSuccess: async () => {
      setReviewsCompleted(prev => prev + 1);

      // Only invalidate necessary queries
      queryClient.invalidateQueries({ queryKey: ['todayReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });

      // Move to next review - state will be reset by useEffect
      if (reviews && reviews.length > 1) {
        const newIndex = Math.min(currentReviewIndex, reviews.length - 2); // -2 because one review was completed
        setCurrentReviewIndex(newIndex);
      } else {
        setCurrentReviewIndex(0);
      }
    },
  });


  const handleReviewComplete = useCallback((result: 'remembered' | 'forgot') => {
    const currentReview = reviews[currentReviewIndex];
    if (currentReview) {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);

      const messages = {
        'remembered': '잘 기억하고 있어요!',
        'forgot': '괜찮아요, 다시 배워봐요!'
      };

      if (onShowToast) {
        onShowToast(messages[result], 'success');
      }

      completeReviewMutation.mutate({
        content_id: currentReview.content.id,
        result: result,
        time_spent: timeSpent,
      });
    }
  }, [reviews, currentReviewIndex, startTime, completeReviewMutation, onShowToast]);

  // Reset flip state when review changes
  useEffect(() => {
    resetReviewState();
  }, [currentReviewIndex, resetReviewState]);

  const currentReview = reviews[currentReviewIndex];

  // Calculate progress based on total reviews for today
  const totalTodayReviews = reviews.length + reviewsCompleted;
  const progress = totalTodayReviews > 0 ? (reviewsCompleted / totalTodayReviews) * 100 : 0;

  return {
    reviews,
    currentReview,
    progress,
    isLoading,
    completeReviewMutation,
    handleReviewComplete,
  };
};