/**
 * TypeScript types for AI Review system
 */


// AI Content Quality Check Request/Response
export interface ContentQualityCheckRequest {
  title: string;
  content: string;
}

export interface ContentQualityCheckResponse {
  score: number;
  feedback: string;
  strengths?: string[];
  improvements?: string[];
  processing_time_ms?: number;
}




// API Response wrapper
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}


// Weekly Test Types
export interface WeeklyTest {
  id: number;
  user: number;
  category?: number;
  category_name?: string;
  week_start_date: string;
  week_end_date: string;
  total_questions: number;
  completed_questions: number;
  correct_answers: number;
  score?: number;
  time_limit_minutes: number;
  started_at?: string;
  completed_at?: string;
  adaptive_mode: boolean;
  current_difficulty: 'easy' | 'medium' | 'hard';
  consecutive_correct: number;
  consecutive_wrong: number;
  question_type_distribution: Record<string, number>;
  estimated_proficiency?: number;
  difficulty_distribution: Record<string, number>;
  content_coverage: number[];
  weak_areas: string[];
  improvement_from_last_week?: number;
  status: 'draft' | 'ready' | 'in_progress' | 'completed' | 'expired';
  accuracy_rate: number;
  completion_rate: number;
  time_spent_minutes: number;
  created_at: string;
}

export interface WeeklyTestQuestion {
  id: number;
  weekly_test: number;
  ai_question: number;
  order: number;
  question_text: string;
  correct_answer: string;
  options?: string[];
  difficulty: number;
  user_answer?: string;
  is_correct?: boolean;
  ai_score?: number;
  time_spent_seconds?: number;
  answered_at?: string;
}

export interface WeeklyTestCreateRequest {
  category_id?: number;
  time_limit_minutes: number;
  adaptive_mode: boolean;
  total_questions: number;
}

export interface CategoryChoice {
  id: number;
  name: string;
  description?: string;
}

// Pagination for list responses
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}