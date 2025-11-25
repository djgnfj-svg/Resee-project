import React from 'react';
import { ReviewSchedule } from '../../types';
import ObjectiveReviewCard from './ObjectiveReviewCard';
import DescriptiveReviewCard from './DescriptiveReviewCard';
import MultipleChoiceReviewCard from './MultipleChoiceReviewCard';
import { AIEvaluation } from './types';
import { logger } from '../../utils/logger';

interface ReviewCardProps {
  review: ReviewSchedule;
  isFlipped: boolean;
  showContent: boolean;
  onFlip: () => void;
  // Descriptive mode (제목 → 내용 작성)
  descriptiveAnswer: string;
  onDescriptiveAnswerChange: (value: string) => void;
  onSubmitDescriptive?: () => void;
  // Multiple choice mode (내용 → 제목 선택)
  selectedChoice?: string;
  onSelectChoice?: (choice: string) => void;
  onSubmitMultipleChoice?: () => void;
  // Common
  isSubmitting?: boolean;
  submittedAnswer?: string;
  aiEvaluation?: AIEvaluation | null;
}

/**
 * ReviewCard: Review 모드에 따라 적절한 컴포넌트로 라우팅
 *
 * 3가지 Review 모드:
 * - objective: 기억 확인 (제목 → 내용 확인)
 * - descriptive: 서술형 (제목 → 내용 작성 + AI 평가)
 * - multiple_choice: 객관식 (내용 → 제목 선택)
 */
const ReviewCard: React.FC<ReviewCardProps> = ({
  review,
  isFlipped,
  showContent,
  onFlip,
  descriptiveAnswer,
  onDescriptiveAnswerChange,
  onSubmitDescriptive,
  selectedChoice,
  onSelectChoice,
  onSubmitMultipleChoice,
  isSubmitting = false,
  submittedAnswer,
  aiEvaluation,
}) => {
  const reviewMode = review.content.review_mode;

  // Mode 1: Objective (기억 확인)
  if (reviewMode === 'objective') {
    return (
      <ObjectiveReviewCard
        review={review}
        showContent={showContent}
        onFlip={onFlip}
        isSubmitting={isSubmitting}
      />
    );
  }

  // Mode 2: Descriptive (제목 → 내용 작성)
  if (reviewMode === 'descriptive') {
    if (!onSubmitDescriptive) {
      logger.error('DescriptiveReviewCard requires onSubmitDescriptive');
      return null;
    }

    return (
      <DescriptiveReviewCard
        review={review}
        descriptiveAnswer={descriptiveAnswer}
        onDescriptiveAnswerChange={onDescriptiveAnswerChange}
        onSubmitDescriptive={onSubmitDescriptive}
        isSubmitting={isSubmitting}
        submittedAnswer={submittedAnswer}
        aiEvaluation={aiEvaluation}
      />
    );
  }

  // Mode 3: Multiple Choice (내용 → 제목 선택)
  if (reviewMode === 'multiple_choice') {
    if (!onSelectChoice || !onSubmitMultipleChoice) {
      logger.error('MultipleChoiceReviewCard requires onSelectChoice and onSubmitMultipleChoice');
      return null;
    }

    return (
      <MultipleChoiceReviewCard
        review={review}
        selectedChoice={selectedChoice}
        onSelectChoice={onSelectChoice}
        onSubmitMultipleChoice={onSubmitMultipleChoice}
        isSubmitting={isSubmitting}
        aiEvaluation={aiEvaluation}
      />
    );
  }

  // Unknown mode
  logger.error(`Unknown review mode: ${reviewMode}`);
  return null;
};

export default ReviewCard;
