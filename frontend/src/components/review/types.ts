import { ReviewSchedule } from '../../types';

/**
 * AI 평가 결과
 */
export interface AIEvaluation {
  score: number;
  feedback: string;
  auto_result?: string;
  is_correct?: boolean;
}

/**
 * 모든 Review 모드의 공통 Props
 */
export interface BaseReviewProps {
  review: ReviewSchedule;
  isSubmitting?: boolean;
}

/**
 * Objective Review Mode Props
 */
export interface ObjectiveReviewProps extends BaseReviewProps {
  showContent: boolean;
  onFlip: () => void;
}

/**
 * Descriptive Review Mode Props
 */
export interface DescriptiveReviewProps extends BaseReviewProps {
  descriptiveAnswer: string;
  onDescriptiveAnswerChange: (value: string) => void;
  onSubmitDescriptive: () => void;
  submittedAnswer?: string;
  aiEvaluation?: AIEvaluation | null;
}

/**
 * Multiple Choice Review Mode Props
 */
export interface MultipleChoiceReviewProps extends BaseReviewProps {
  selectedChoice?: string;
  onSelectChoice: (choice: string) => void;
  onSubmitMultipleChoice: () => void;
  aiEvaluation?: AIEvaluation | null;
}
