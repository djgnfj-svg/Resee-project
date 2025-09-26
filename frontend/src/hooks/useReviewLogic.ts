import { useCallback, useEffect, useMemo, useState } from 'react';
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

export const useReviewLogic = (
  onShowToast?: (message: string, type: 'success' | 'info' | 'warning' | 'error') => void,
  resetReviewState?: () => void
) => {
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
  } = useReviewState();

  const queryClient = useQueryClient();

  // Local reviews state management for card reordering
  const [localReviews, setLocalReviews] = useState<ReviewSchedule[]>([]);

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

  // Update local reviews when server data changes
  useEffect(() => {
    if (reviewData) {
      setLocalReviews([...reviewData]);
    }
  }, [reviewData]);

  // Move current card to end of array (for "forgot" case)
  const moveCurrentCardToEnd = useCallback(() => {
    if (localReviews.length === 1) {
      // Only one card - just reset its state
      if (resetReviewState) {
        resetReviewState();
      }
    } else if (localReviews.length > 1 && currentReviewIndex < localReviews.length) {
      const newReviews = [...localReviews];
      const currentCard = newReviews.splice(currentReviewIndex, 1)[0];
      newReviews.push(currentCard);
      setLocalReviews(newReviews);
      // Don't change currentReviewIndex - now points to the next card

      // Immediately reset UI state for new card
      if (resetReviewState) {
        resetReviewState();
      }
    }
  }, [localReviews, currentReviewIndex, resetReviewState]);

  // Remove current card from array (for "remembered" case)
  const removeCurrentCard = useCallback(() => {
    if (localReviews.length > 0 && currentReviewIndex < localReviews.length) {
      const newReviews = [...localReviews];
      newReviews.splice(currentReviewIndex, 1);
      setLocalReviews(newReviews);
      // Adjust index if needed
      if (currentReviewIndex >= newReviews.length && newReviews.length > 0) {
        setCurrentReviewIndex(0);
      }

      // Immediately reset UI state for new card
      if (resetReviewState) {
        resetReviewState();
      }
    }
  }, [localReviews, currentReviewIndex, setCurrentReviewIndex, resetReviewState]);

  const reviews: ReviewSchedule[] = localReviews;

  // Complete review mutation
  const completeReviewMutation = useMutation({
    mutationFn: reviewAPI.completeReview,
    onSuccess: async (data, variables) => {
      if (variables.result === 'remembered') {
        // "기억함": 완료 처리
        setReviewsCompleted(prev => prev + 1);
        removeCurrentCard();

        // Invalidate dashboard to update stats
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });

        if (onShowToast) {
          onShowToast('잘 기억하고 있어요!', 'success');
        }
      } else {
        // "모름": 카드를 맨 뒤로 이동
        moveCurrentCardToEnd();

        if (onShowToast) {
          onShowToast('괜찮아요, 나중에 다시 시도해보세요!', 'info');
        }
      }
    },
  });


  const handleReviewComplete = useCallback((result: 'remembered' | 'forgot') => {
    const currentReview = reviews[currentReviewIndex];
    if (currentReview) {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);

      completeReviewMutation.mutate({
        content_id: currentReview.content.id,
        result: result,
        time_spent: timeSpent,
      });
    }
  }, [reviews, currentReviewIndex, startTime, completeReviewMutation]);

  // No need for useEffect to reset state as we're doing it directly in card operations

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
    reviewsCompleted,
    totalSchedules: reviews.length + reviewsCompleted,
  };
};