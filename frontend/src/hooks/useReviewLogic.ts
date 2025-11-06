import { useCallback, useEffect, useState } from 'react';
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
    reviewsCompleted,
    setReviewsCompleted,
    totalSchedules,
    setTotalSchedules,
  } = useReviewState();

  const queryClient = useQueryClient();

  // Local reviews state management for card reordering
  const [localReviews, setLocalReviews] = useState<ReviewSchedule[]>([]);

  // Fetch today's reviews (always all categories)
  const { data: reviewData, isLoading } = useQuery<TodayReviewsResponse | ReviewSchedule[]>({
    queryKey: ['todayReviews'],
    queryFn: async () => {
      return await reviewAPI.getTodayReviews('');
    }
  });

  // Extract reviews and total count from response
  useEffect(() => {
    if (reviewData) {
      let reviews: ReviewSchedule[];
      let todayCount = 0;

      if (isTodayReviewsResponse(reviewData)) {
        reviews = reviewData.results;
        // Use 'count' (today's reviews) instead of 'total_count' (all active schedules)
        todayCount = reviewData.count || reviews.length;
      } else {
        reviews = extractResults(reviewData) as ReviewSchedule[];
        todayCount = reviews.length;
      }

      setLocalReviews([...reviews]);
      setTotalSchedules(todayCount);  // 오늘 복습할 총 개수
    }
  }, [reviewData, setTotalSchedules]);

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
      // AI 평가 모드 (descriptive, subjective, multiple_choice): 카드 이동 안함
      // 사용자가 "다음으로" 버튼 눌렀을 때 이동
      const isAIMode =
        (variables.descriptive_answer && variables.descriptive_answer.length > 0) ||
        (variables.user_title && variables.user_title.length > 0) ||
        (variables.selected_choice && variables.selected_choice.length > 0);

      if (isAIMode) {
        // AI 평가 모드는 "다음으로" 버튼에서 reviewsCompleted 증가
        // Invalidate dashboard to update stats
        queryClient.invalidateQueries({ queryKey: ['dashboard'] });

        // 토스트는 ReviewPage에서 처리
        return;
      }

      // 기억 확인 모드 (objective): 기존 로직
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


  const handleReviewComplete = useCallback((
    result: 'remembered' | 'partial' | 'forgot' | null,
    descriptiveAnswer?: string,
    selectedChoice?: string,
    userTitle?: string
  ) => {
    const currentReview = reviews[currentReviewIndex];
    if (currentReview) {
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);

      return new Promise((resolve, reject) => {
        completeReviewMutation.mutate({
          content_id: currentReview.content.id,
          result: result || undefined,
          time_spent: timeSpent,
          descriptive_answer: descriptiveAnswer || '',
          selected_choice: selectedChoice || '',
          user_title: userTitle || '',
        }, {
          onSuccess: (data) => {
            resolve(data);
          },
          onError: (error) => {
            reject(error);
          }
        });
      });
    }
    return Promise.resolve(null);
  }, [reviews, currentReviewIndex, startTime, completeReviewMutation]);

  // No need for useEffect to reset state as we're doing it directly in card operations

  const currentReview = reviews[currentReviewIndex];

  // Calculate progress based on total reviews for today
  const progress = totalSchedules > 0 ? (reviewsCompleted / totalSchedules) * 100 : 0;

  return {
    reviews,
    currentReview,
    progress,
    isLoading,
    completeReviewMutation,
    handleReviewComplete,
    reviewsCompleted,
    setReviewsCompleted,
    totalSchedules,
    removeCurrentCard,
    moveCurrentCardToEnd,
  };
};