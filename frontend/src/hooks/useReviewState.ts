import { useState, useCallback } from 'react';
import { ExplanationEvaluationResponse } from '../types/ai-review';

export interface ReviewState {
  selectedCategory: string;
  currentReviewIndex: number;
  showContent: boolean;
  isFlipped: boolean;
  startTime: number;
  reviewsCompleted: number;
  totalSchedules: number;
  reviewMode: 'card' | 'explanation';
  userExplanation: string;
  evaluationResult: ExplanationEvaluationResponse | null;
  isEvaluating: boolean;
  showUpgradeModal: boolean;
  showEvaluation: boolean;
}

export const useReviewState = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);
  const [showContent, setShowContent] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [reviewsCompleted, setReviewsCompleted] = useState(0);
  const [totalSchedules, setTotalSchedules] = useState(0);
  
  // Review mode states
  const [reviewMode, setReviewMode] = useState<'card' | 'explanation'>('card');
  const [userExplanation, setUserExplanation] = useState('');
  const [evaluationResult, setEvaluationResult] = useState<ExplanationEvaluationResponse | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [showEvaluation, setShowEvaluation] = useState(false);

  const resetReviewState = useCallback(() => {
    setIsFlipped(false);
    setShowContent(false);
    setStartTime(Date.now());
    setUserExplanation('');
    setEvaluationResult(null);
    setShowEvaluation(false);
  }, []);

  const resetCategoryState = useCallback(() => {
    setCurrentReviewIndex(0);
    setShowContent(false);
    setIsFlipped(false);
  }, []);

  return {
    selectedCategory,
    setSelectedCategory,
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
    reviewMode,
    setReviewMode,
    userExplanation,
    setUserExplanation,
    evaluationResult,
    setEvaluationResult,
    isEvaluating,
    setIsEvaluating,
    showUpgradeModal,
    setShowUpgradeModal,
    showEvaluation,
    setShowEvaluation,
    resetReviewState,
    resetCategoryState,
  };
};