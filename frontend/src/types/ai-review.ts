/**
 * TypeScript types for AI Review system
 */

// AI Question Types
export interface AIQuestionType {
  id: number;
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
}

// AI Question
export interface AIQuestion {
  id: number;
  content: number;
  content_title: string;
  question_type: number;
  question_type_display: string;
  question_text: string;
  correct_answer: string;
  options?: string[];
  difficulty: number;
  explanation?: string;
  keywords?: string[];
  is_active: boolean;
  created_at: string;
}

// Question Generation Request
export interface GenerateQuestionsRequest {
  content_id: number;
  question_types: string[];
  difficulty: number;
  count: number;
}

// Answer Evaluation Request
export interface EvaluateAnswerRequest {
  question_id: number;
  user_answer: string;
}

// Answer Evaluation Result
export interface AnswerEvaluationResult {
  evaluation_id: number;
  score: number;
  feedback: string;
  similarity_score?: number;
  evaluation_details?: {
    strengths: string[];
    weaknesses: string[];
    suggestions: string[];
  };
  ai_model_used?: string;
  processing_time_ms?: number;
}

// AI Evaluation
export interface AIEvaluation {
  id: number;
  question: number;
  question_text: string;
  user: number;
  user_email: string;
  user_answer: string;
  ai_score: number;
  feedback: string;
  similarity_score?: number;
  evaluation_details?: {
    strengths: string[];
    weaknesses: string[];
    suggestions: string[];
  };
  ai_model_used?: string;
  processing_time_ms?: number;
  created_at: string;
}

// Fill-in-blank Request/Response
export interface FillBlankRequest {
  content_id: number;
  num_blanks: number;
}

export interface FillBlankResponse {
  blanked_text: string;
  answers: Record<string, string>;
  keywords: string[];
  ai_model_used?: string;
  processing_time_ms?: number;
}

// Blur Regions Request/Response
export interface BlurRegionsRequest {
  content_id: number;
}

export interface BlurRegion {
  text: string;
  start_pos: number;
  end_pos: number;
  importance: number;
  concept_type: string;
}

export interface BlurRegionsResponse {
  blur_regions: BlurRegion[];
  concepts: string[];
  ai_model_used?: string;
  processing_time_ms?: number;
}

// UI State Types
export interface QuestionGenerationState {
  isLoading: boolean;
  selectedTypes: string[];
  difficulty: number;
  count: number;
  questions: AIQuestion[];
  error?: string;
}

export interface ReviewSessionState {
  currentQuestionIndex: number;
  questions: AIQuestion[];
  answers: Record<number, string>;
  evaluations: Record<number, AnswerEvaluationResult>;
  isEvaluating: boolean;
  sessionComplete: boolean;
  score?: number;
}

export interface BlurProcessingState {
  blurredText: string;
  blurRegions: BlurRegion[];
  revealedRegions: Set<number>;
  concepts: string[];
  isLoading: boolean;
}

export interface FillBlankState {
  blankedText: string;
  answers: Record<string, string>;
  userAnswers: Record<string, string>;
  keywords: string[];
  isChecking: boolean;
  score?: number;
}

// Question Type Names (matching backend)
export const QUESTION_TYPES = {
  MULTIPLE_CHOICE: 'multiple_choice',
  SHORT_ANSWER: 'short_answer', 
  FILL_BLANK: 'fill_blank',
  BLUR_PROCESSING: 'blur_processing'
} as const;

export type QuestionTypeName = typeof QUESTION_TYPES[keyof typeof QUESTION_TYPES];

// Difficulty Levels
export const DIFFICULTY_LEVELS = {
  VERY_EASY: 1,
  EASY: 2, 
  MEDIUM: 3,
  HARD: 4,
  VERY_HARD: 5
} as const;

export type DifficultyLevel = typeof DIFFICULTY_LEVELS[keyof typeof DIFFICULTY_LEVELS];

// Score Ranges for UI display
export const SCORE_RANGES = {
  EXCELLENT: { min: 0.9, label: '우수', color: 'green' },
  GOOD: { min: 0.7, label: '양호', color: 'blue' },
  FAIR: { min: 0.5, label: '보통', color: 'yellow' },
  POOR: { min: 0.3, label: '미흡', color: 'orange' },
  FAIL: { min: 0.0, label: '부족', color: 'red' }
} as const;

// API Response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// Pagination for list responses
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}