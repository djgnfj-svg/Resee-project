import axios from 'axios';
import { 
  AuthTokens, 
  LoginData, 
  RegisterData, 
  RegisterResponse,
  User,
  CreateContentData,
  UpdateContentData,
  CreateCategoryData,
  CompleteReviewData,
  CreateReviewHistoryData,
  PaginatedResponse,
  Content,
  Category,
  ReviewSchedule,
  ReviewHistory,
  DashboardData,
  Subscription,
  SubscriptionTierInfo,
  SubscriptionUpgradeData
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh and errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const newAccessToken = response.data.access;
          localStorage.setItem('access_token', newAccessToken);
          
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          // Don't redirect automatically, let the component handle it
          error.isAuthError = true;
        }
      } else {
        // No refresh token available
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        error.isAuthError = true;
      }
    }
    
    // Handle other errors
    if (error.response) {
      // Server responded with error status
      let errorMessage = '';
      
      if (error.response.data?.non_field_errors && Array.isArray(error.response.data.non_field_errors)) {
        // Handle Django REST framework non_field_errors
        errorMessage = error.response.data.non_field_errors[0];
      } else if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response.data?.message) {
        errorMessage = error.response.data.message;
      } else if (typeof error.response.data === 'string') {
        errorMessage = error.response.data;
      } else {
        // Handle field-specific errors
        const fieldErrors = error.response.data;
        if (typeof fieldErrors === 'object') {
          const firstErrorKey = Object.keys(fieldErrors)[0];
          if (firstErrorKey && Array.isArray(fieldErrors[firstErrorKey])) {
            errorMessage = `${firstErrorKey}: ${fieldErrors[firstErrorKey][0]}`;
          } else if (firstErrorKey) {
            errorMessage = `${firstErrorKey}: ${fieldErrors[firstErrorKey]}`;
          }
        }
      }
      
      // Provide more user-friendly error messages based on status code
      if (!errorMessage) {
        switch (error.response.status) {
          case 400:
            errorMessage = '입력하신 정보가 올바르지 않습니다.';
            break;
          case 401:
            errorMessage = '인증이 필요합니다. 다시 로그인해주세요.';
            break;
          case 403:
            errorMessage = '권한이 없습니다.';
            break;
          case 404:
            errorMessage = '요청하신 정보를 찾을 수 없습니다.';
            break;
          case 500:
          case 502:
          case 503:
            errorMessage = '서버에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.';
            break;
          default:
            errorMessage = '요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요.';
        }
      }
      
      error.userMessage = errorMessage;
    } else if (error.request) {
      // Network error
      error.userMessage = '네트워크 연결을 확인해 주세요.';
    } else {
      // Other error
      error.userMessage = '예상치 못한 오류가 발생했습니다.';
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (data: LoginData): Promise<AuthTokens> => {
    const response = await api.post('/auth/token/', data);
    return response.data;
  },
  
  register: async (data: RegisterData): Promise<RegisterResponse> => {
    const response = await api.post('/accounts/users/register/', data);
    return response.data;
  },
  
  getProfile: async (): Promise<User> => {
    const response = await api.get('/accounts/profile/');
    return response.data;
  },
  
  googleLogin: async (token: string): Promise<any> => {
    const response = await api.post('/accounts/google-oauth/', { token });
    return response.data;
  },
  
  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await api.put('/accounts/profile/', data);
    return response.data;
  },
  
  changePassword: async (data: { current_password: string; new_password: string; new_password_confirm: string; }): Promise<{ message: string }> => {
    const response = await api.post('/accounts/password/change/', data);
    return response.data;
  },
  
  deleteAccount: async (data: { password: string; confirmation: string; }): Promise<{ message: string }> => {
    const response = await api.post('/accounts/account/delete/', data);
    return response.data;
  },
};

// Content API
export const contentAPI = {
  getContents: async (params?: string): Promise<PaginatedResponse<Content> | Content[]> => {
    const url = params ? `/content/contents/?${params}` : '/content/contents/';
    const response = await api.get(url);
    return response.data;
  },
  
  createContent: async (data: CreateContentData): Promise<Content> => {
    const response = await api.post('/content/contents/', data);
    return response.data;
  },
  
  updateContent: async (id: number, data: UpdateContentData): Promise<Content> => {
    const response = await api.put(`/content/contents/${id}/`, data);
    return response.data;
  },
  
  deleteContent: async (id: number): Promise<void> => {
    await api.delete(`/content/contents/${id}/`);
  },
  
  getCategories: async (): Promise<PaginatedResponse<Category> | Category[]> => {
    const response = await api.get('/content/categories/');
    return response.data;
  },
  
  createCategory: async (data: CreateCategoryData): Promise<Category> => {
    const response = await api.post('/content/categories/', data);
    return response.data;
  },
  
  getContentsByCategory: async (): Promise<Record<string, Content[]>> => {
    const response = await api.get('/content/contents/by_category/');
    return response.data;
  },
  
};

// Review API
export const reviewAPI = {
  getTodayReviews: async (params?: string): Promise<ReviewSchedule[]> => {
    const url = params ? `/review/today/${params}` : '/review/today/';
    const response = await api.get(url);
    return response.data;
  },
  
  getSchedules: async (): Promise<PaginatedResponse<ReviewSchedule> | ReviewSchedule[]> => {
    const response = await api.get('/review/schedules/');
    return response.data;
  },
  
  getHistory: async (): Promise<PaginatedResponse<ReviewHistory> | ReviewHistory[]> => {
    const response = await api.get('/review/history/');
    return response.data;
  },
  
  createHistory: async (data: CreateReviewHistoryData): Promise<ReviewHistory> => {
    const response = await api.post('/review/history/', data);
    return response.data;
  },
  
  completeReview: async (data: CompleteReviewData): Promise<{ message: string; next_review_date?: string }> => {
    const response = await api.post('/review/complete/', data);
    return response.data;
  },
  
  getCategoryStats: async (): Promise<Record<string, any>> => {
    const response = await api.get('/review/category-stats/');
    return response.data;
  },
};

// Analytics API
export const analyticsAPI = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await api.get('/analytics/dashboard/');
    return response.data;
  },
  
  getReviewStats: async (): Promise<Record<string, any>> => {
    const response = await api.get('/analytics/review-stats/');
    return response.data;
  },
};

// Email Verification API
export const verifyEmail = async (token: string, email: string): Promise<{ message: string; user: User }> => {
  const response = await api.post('/accounts/verify-email/', { token, email });
  return response.data;
};

export const resendVerificationEmail = async (email: string): Promise<{ message: string }> => {
  const response = await api.post('/accounts/resend-verification/', { email });
  return response.data;
};

// Subscription API
export const subscriptionAPI = {
  getSubscription: async (): Promise<Subscription> => {
    const response = await api.get('/accounts/subscription/');
    return response.data;
  },
  
  getSubscriptionTiers: async (): Promise<SubscriptionTierInfo[]> => {
    const response = await api.get('/accounts/subscription/tiers/');
    return response.data;
  },
  
  upgradeSubscription: async (data: SubscriptionUpgradeData): Promise<Subscription> => {
    const response = await api.post('/accounts/subscription/upgrade/', data);
    return response.data;
  },
};

// Weekly Goal API
export const weeklyGoalAPI = {
  updateWeeklyGoal: async (weeklyGoal: number): Promise<{ message: string; weekly_goal: number }> => {
    const response = await api.patch('/accounts/weekly-goal/', { weekly_goal: weeklyGoal });
    return response.data;
  },
};

// Export apiClient alias for compatibility
export const apiClient = api;

export default api;