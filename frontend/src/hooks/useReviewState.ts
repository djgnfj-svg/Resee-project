import { useState, useCallback } from 'react';

export interface ReviewState {
  currentReviewIndex: number;
  showContent: boolean;
  isFlipped: boolean;
  startTime: number;
  reviewsCompleted: number;
  totalSchedules: number;
  showUpgradeModal: boolean;
}

export const useReviewState = () => {
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [reviewsCompleted, setReviewsCompleted] = useState(0);
  const [totalSchedules, setTotalSchedules] = useState(0);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  const resetReviewState = useCallback(() => {
    setIsFlipped(false);
    setShowContent(false);
    setStartTime(Date.now());
  }, []);

  return {
    currentReviewIndex,
    setCurrentReviewIndex,
    showContent,
    setShowContent,
    isFlipped,
    setIsFlipped,
    startTime,
    setStartTime,
    reviewsCompleted,
    setReviewsCompleted,
    totalSchedules,
    setTotalSchedules,
    showUpgradeModal,
    setShowUpgradeModal,
    resetReviewState,
  };
};