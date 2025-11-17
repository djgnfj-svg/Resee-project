import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Store access token in memory (NOT localStorage)
let accessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Send cookies with requests
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
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

      try {
        // Refresh token is sent automatically via HttpOnly cookie
        const response = await axios.post(
          `${API_BASE_URL}/auth/token/refresh/`,
          {},
          { withCredentials: true }
        );

        const newAccessToken = response.data.access;
        setAccessToken(newAccessToken);

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, clear access token
        setAccessToken(null);
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

// Export apiClient alias for compatibility
export const apiClient = api;
export default api;