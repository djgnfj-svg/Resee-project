import axios, { AxiosError, AxiosInstance } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';
import { API_CONFIG, STORAGE_KEYS } from '../constants/config';

// Token management
let accessToken: string | null = null;

// Storage helper that works on both native and web
const storage = {
  async setItem(key: string, value: string) {
    if (Platform.OS === 'web') {
      localStorage.setItem(key, value);
    } else {
      await SecureStore.setItemAsync(key, value);
    }
  },
  async getItem(key: string): Promise<string | null> {
    if (Platform.OS === 'web') {
      return localStorage.getItem(key);
    } else {
      return await SecureStore.getItemAsync(key);
    }
  },
  async deleteItem(key: string) {
    if (Platform.OS === 'web') {
      localStorage.removeItem(key);
    } else {
      await SecureStore.deleteItemAsync(key);
    }
  },
};

export const setAccessToken = async (token: string | null) => {
  accessToken = token;
  if (token) {
    await storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
  } else {
    await storage.deleteItem(STORAGE_KEYS.ACCESS_TOKEN);
  }
};

export const getAccessToken = async (): Promise<string | null> => {
  if (accessToken) return accessToken;

  try {
    const token = await storage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (token) {
      accessToken = token;
    }
    return token;
  } catch (error) {
    console.error('Error getting access token:', error);
    return null;
  }
};

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  async (config) => {
    const token = await getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest: any = error.config;

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Try to refresh token
        // Note: For mobile, we'll need to implement refresh token storage
        // For now, we'll just clear the token and redirect to login
        await setAccessToken(null);
        // You can emit an event here to navigate to login
        return Promise.reject(error);
      } catch (refreshError) {
        await setAccessToken(null);
        return Promise.reject(refreshError);
      }
    }

    // Format error message
    let errorMessage = '';

    if (error.response) {
      const data = error.response.data as any;

      if (data?.non_field_errors && Array.isArray(data.non_field_errors)) {
        errorMessage = data.non_field_errors[0];
      } else if (data?.detail) {
        errorMessage = data.detail;
      } else if (data?.message) {
        errorMessage = data.message;
      } else if (typeof data === 'string') {
        errorMessage = data;
      } else if (typeof data === 'object') {
        const firstErrorKey = Object.keys(data)[0];
        if (firstErrorKey && Array.isArray(data[firstErrorKey])) {
          errorMessage = `${firstErrorKey}: ${data[firstErrorKey][0]}`;
        } else if (firstErrorKey) {
          errorMessage = `${firstErrorKey}: ${data[firstErrorKey]}`;
        }
      }

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
    } else if (error.request) {
      errorMessage = '네트워크 연결을 확인해 주세요.';
    } else {
      errorMessage = '예상치 못한 오류가 발생했습니다.';
    }

    (error as any).userMessage = errorMessage;
    return Promise.reject(error);
  }
);

export default apiClient;
