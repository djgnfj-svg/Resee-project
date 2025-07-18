import axios from 'axios';
import { 
  AuthTokens, 
  LoginData, 
  RegisterData, 
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
  DashboardData
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
      const errorMessage = error.response.data?.message || 
                          error.response.data?.detail || 
                          `서버 오류 (${error.response.status})`;
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
  
  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post('/accounts/users/register/', data);
    return response.data;
  },
  
  getProfile: async (): Promise<User> => {
    const response = await api.get('/accounts/profile/');
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

export default api;