// User & Auth types
export interface User {
  id: number;
  email: string;
  username?: string;
  is_email_verified: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  created_at: string;
  updated_at: string;
  subscription?: Subscription;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  terms_agreed: boolean;
  privacy_agreed: boolean;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  data: {
    user: User;
    requires_email_verification?: boolean;
  };
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

// Content types
export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  created_at: string;
}

export type ReviewMode = 'objective' | 'descriptive' | 'multiple_choice' | 'subjective';

export interface MultipleChoiceOptions {
  choices: string[];
  correct_answer: string;
}

export interface Content {
  id: number;
  title: string;
  content: string;
  author: string;
  category?: Category;
  created_at: string;
  updated_at: string;
  review_count: number;
  next_review_date?: string;
  review_mode: ReviewMode;
  mc_choices?: MultipleChoiceOptions;
  is_ai_validated: boolean;
  ai_validation_score?: number;
  ai_validation_result?: {
    is_valid: boolean;
    factual_accuracy: {
      score: number;
      issues: string[];
    };
    logical_consistency: {
      score: number;
      issues: string[];
    };
    title_relevance: {
      score: number;
      issues: string[];
    };
    overall_feedback: string;
  };
  ai_validated_at?: string;
}

export interface ContentUsage {
  current: number;
  limit: number;
  remaining: number;
  percentage: number;
  can_create: boolean;
  tier: 'free' | 'basic' | 'pro';
}

export interface ContentListResponse {
  results: Content[];
  usage: ContentUsage;
  count: number;
  next: string | null;
  previous: string | null;
}

export interface CategoryUsage {
  current: number;
  limit: number;
  remaining: number;
  percentage: number;
  can_create: boolean;
  tier: 'free' | 'basic' | 'pro';
}

export interface CategoryListResponse {
  results: Category[];
  usage: CategoryUsage;
  count: number;
  next: string | null;
  previous: string | null;
}

// Review types
export interface ReviewSchedule {
  id: number;
  content: Content;
  user: string;
  next_review_date: string;
  interval_index: number;
  is_active: boolean;
  initial_review_completed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TodayReviewsResponse {
  results: ReviewSchedule[];
  count: number;
  total_count: number;
  subscription_tier: string;
  max_interval_days: number;
}

export interface ReviewHistory {
  id: number;
  content: Content;
  user: string;
  review_date: string;
  result: 'remembered' | 'partial' | 'forgot';
  time_spent?: number;
  notes?: string;
}

export interface CompleteReviewData {
  content_id: number;
  result?: 'remembered' | 'partial' | 'forgot';
  time_spent?: number;
  notes?: string;
  descriptive_answer?: string;
  selected_choice?: string;
  user_title?: string;
}

// Dashboard types
export interface DashboardData {
  today_reviews: number;
  pending_reviews: number;
  total_content: number;
  success_rate: number;
  total_reviews_30_days: number;
}

export interface ResultDistribution {
  result: string;
  name: string;
  count: number;
  percentage: number;
}

export interface DailyReviewData {
  date: string;
  count: number;
  success_rate: number;
  remembered: number;
  partial: number;
  forgot: number;
}

export interface WeeklyPerformanceData {
  week_start: string;
  week_end: string;
  week_label: string;
  total_reviews: number;
  success_rate: number;
  consistency: number;
  days_active: number;
  remembered: number;
  partial: number;
  forgot: number;
}

export interface ReviewTrends {
  review_count_change: number;
  success_rate_change: number;
  current_period_total: number;
  previous_period_total: number;
  current_success_rate: number;
  previous_success_rate: number;
}

export interface ReviewStatsData {
  result_distribution: {
    all_time: ResultDistribution[];
    recent_30_days: ResultDistribution[];
    all_time_total: number;
    recent_total: number;
  };
  daily_reviews: DailyReviewData[];
  weekly_performance: WeeklyPerformanceData[];
  trends: ReviewTrends;
}

// Subscription types
export type SubscriptionTier = 'free' | 'basic' | 'pro';

export interface Subscription {
  id: number;
  tier: SubscriptionTier;
  tier_display: string;
  max_interval_days: number;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  days_remaining: number | null;
  is_expired: boolean;
  auto_renewal?: boolean;
  next_billing_date?: string | null;
}

export interface SubscriptionTierInfo {
  name: SubscriptionTier;
  display_name: string;
  max_days: number;
  price: number | string;
  features: string[];
  coming_soon?: boolean;
}

// API Response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Exam types
export interface Exam {
  id: number;
  title: string;
  description?: string;
  created_at: string;
  status: 'pending' | 'ready' | 'failed';
  questions?: ExamQuestion[];
  total_questions: number;
  duration_minutes?: number;
}

export interface ExamQuestion {
  id: number;
  question_text: string;
  choices: string[];
  correct_answer: string;
  explanation?: string;
  content_id: number;
  content_title: string;
}

export interface ExamSubmission {
  exam_id: number;
  answers: {
    question_id: number;
    selected_choice: string;
  }[];
}

export interface ExamResult {
  id: number;
  exam: Exam;
  score: number;
  total_questions: number;
  correct_answers: number;
  submitted_at: string;
  time_spent_minutes?: number;
  answers: {
    question_id: number;
    selected_choice: string;
    is_correct: boolean;
    correct_answer: string;
  }[];
}
