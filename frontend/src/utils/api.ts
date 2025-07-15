import axios from 'axios';
import { AuthTokens, LoginData, RegisterData, User } from '../types';

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

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
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
          window.location.href = '/login';
        }
      }
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
};

// Content API
export const contentAPI = {
  getContents: async (params?: string) => {
    const url = params ? `/content/contents/?${params}` : '/content/contents/';
    const response = await api.get(url);
    return response.data;
  },
  
  createContent: async (data: any) => {
    const response = await api.post('/content/contents/', data);
    return response.data;
  },
  
  updateContent: async (id: number, data: any) => {
    const response = await api.put(`/content/contents/${id}/`, data);
    return response.data;
  },
  
  deleteContent: async (id: number) => {
    await api.delete(`/content/contents/${id}/`);
  },
  
  getCategories: async () => {
    const response = await api.get('/content/categories/');
    return response.data;
  },
  
  createCategory: async (data: { name: string; description: string }) => {
    const response = await api.post('/content/categories/', data);
    return response.data;
  },
  
  getTags: async () => {
    const response = await api.get('/content/tags/');
    return response.data;
  },
  
  getContentsByCategory: async () => {
    const response = await api.get('/content/contents/by_category/');
    return response.data;
  },
};

// Review API
export const reviewAPI = {
  getTodayReviews: async (params?: string) => {
    const url = params ? `/review/today/${params}` : '/review/today/';
    const response = await api.get(url);
    return response.data;
  },
  
  getSchedules: async () => {
    const response = await api.get('/review/schedules/');
    return response.data;
  },
  
  getHistory: async () => {
    const response = await api.get('/review/history/');
    return response.data;
  },
  
  createHistory: async (data: any) => {
    const response = await api.post('/review/history/', data);
    return response.data;
  },
  
  completeReview: async (data: any) => {
    const response = await api.post('/review/complete/', data);
    return response.data;
  },
  
  getCategoryStats: async () => {
    const response = await api.get('/review/category-stats/');
    return response.data;
  },
};

// Analytics API
export const analyticsAPI = {
  getDashboard: async () => {
    const response = await api.get('/analytics/dashboard/');
    return response.data;
  },
  
  getReviewStats: async () => {
    const response = await api.get('/analytics/review-stats/');
    return response.data;
  },
};

export default api;