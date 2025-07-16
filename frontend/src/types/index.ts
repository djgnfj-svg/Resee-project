export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  timezone: string;
  notification_enabled: boolean;
  date_joined: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
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

export interface Tag {
  id: number;
  name: string;
  slug: string;
  created_at: string;
}

export interface Content {
  id: number;
  title: string;
  content: string;
  author: string;
  category?: Category;
  tags: Tag[];
  priority: 'low' | 'medium' | 'high';
  created_at: string;
  updated_at: string;
}

export interface ReviewSchedule {
  id: number;
  content: Content;
  user: string;
  next_review_date: string;
  interval_index: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
}

// Content API types
export interface CreateContentData {
  title: string;
  content: string;
  category?: number;
  priority: 'low' | 'medium' | 'high';
  tag_ids?: number[];
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

export interface ImageUploadResponse {
  image_url: string;
  filename: string;
}