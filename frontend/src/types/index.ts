export interface User {
  id: number;
  email: string;
  username?: string;
  is_email_verified: boolean;
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
}

export interface RegisterResponse {
  message: string;
  user: User;
  requires_email_verification?: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string;
  created_at: string;
}

export interface Content {
  id: number;
  title: string;
  content: string;
  author: string;
  category?: Category;
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
  review_count: number;
  current_interval?: number;
  next_review_date?: string;
}

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

export interface DashboardData {
  today_reviews: number;
  pending_reviews: number;
  total_content: number;
  success_rate: number;
  total_reviews_30_days: number;
  streak_days: number;
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

// Content API types
export interface CreateContentData {
  title: string;
  content: string;
  category?: number;
  priority: 'low' | 'medium' | 'high';
}

export interface UpdateContentData extends Partial<CreateContentData> {}

export interface CreateCategoryData {
  name: string;
  description: string;
}

// Review API types
export interface CompleteReviewData {
  content_id: number;
  result: 'remembered' | 'partial' | 'forgot';
  time_spent?: number;
  notes?: string;
}

export interface CreateReviewHistoryData extends CompleteReviewData {}

// API Response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Subscription types
export type SubscriptionTier = 'free' | 'basic' | 'premium' | 'pro';

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
}

export interface SubscriptionTierInfo {
  name: SubscriptionTier;
  display_name: string;
  max_days: number;
  price: number;
  features: string[];
}

export interface SubscriptionUpgradeData {
  tier: SubscriptionTier;
}

export interface SubscriptionUpgradeError {
  error?: string;
  email_verified?: boolean;
  tier?: string[];
}
