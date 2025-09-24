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
  next_review_date?: string;
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
  description?: string;
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
  payment_method?: string;
}

export interface SubscriptionTierInfo {
  name: SubscriptionTier;
  display_name: string;
  max_days: number;
  price: number | string;
  features: string[];
  coming_soon?: boolean;
}

export interface SubscriptionUpgradeData {
  tier: SubscriptionTier;
  billing_cycle?: 'monthly' | 'yearly';
}

export interface SubscriptionUpgradeError {
  error?: string;
  email_verified?: boolean;
  tier?: string[];
}

export interface PaymentHistory {
  id: number;
  payment_type: 'upgrade' | 'downgrade' | 'cancellation' | 'renewal' | 'initial';
  payment_type_display: string;
  from_tier?: string;
  from_tier_display?: string;
  to_tier: string;
  to_tier_display: string;
  tier_display: string;
  amount: number;
  description: string;
  created_at: string;
}

export interface PaymentHistoryResponse {
  count: number;
  results: PaymentHistory[];
}
