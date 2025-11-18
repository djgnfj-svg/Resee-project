/**
 * API Client
 *
 * Axios instance with interceptors for authentication
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
} from 'axios';
import {API_CONFIG} from './config';
import {TokenStorage} from './storage';

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

/**
 * Create axios instance
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: API_CONFIG.HEADERS,
});

/**
 * Request interceptor
 * Add access token to all requests
 */
apiClient.interceptors.request.use(
  async (config: any) => {
    const accessToken = await TokenStorage.getAccessToken();

    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  },
);

/**
 * Response interceptor
 * Handle token refresh on 401 errors
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest: any = error.config;

    // 401 에러이고, 재시도하지 않은 요청이며, refresh 엔드포인트가 아닌 경우
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes(API_CONFIG.ENDPOINTS.REFRESH)
    ) {
      if (isRefreshing) {
        // 이미 refresh 중이면 대기열에 추가
        return new Promise((resolve, reject) => {
          failedQueue.push({resolve, reject});
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return apiClient(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = await TokenStorage.getRefreshToken();

        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Refresh token 요청
        const response = await axios.post(
          `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.REFRESH}`,
          {refresh: refreshToken},
          {
            headers: {
              ...API_CONFIG.HEADERS,
            },
          },
        );

        const {access, refresh: newRefreshToken} = response.data;

        // 새 토큰 저장
        await TokenStorage.setTokens(
          access,
          newRefreshToken || refreshToken, // 백엔드가 새 refresh token을 반환하면 사용
        );

        // 대기 중인 요청들 처리
        processQueue(null, access);

        // 원래 요청 재시도
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh 실패 시 로그아웃 처리
        processQueue(refreshError, null);
        await TokenStorage.clearTokens();

        // 로그아웃 이벤트 발생 (AuthContext에서 처리)
        // EventEmitter 또는 다른 방식으로 처리 가능

        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

/**
 * API request wrapper with error handling
 */
export const apiRequest = async <T = any>(
  config: AxiosRequestConfig,
): Promise<T> => {
  try {
    const response = await apiClient(config);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      // API 에러 처리
      const apiError = {
        message: error.response?.data?.error ||
          error.response?.data?.detail ||
          error.message,
        status: error.response?.status,
        data: error.response?.data,
      };
      throw apiError;
    }
    throw error;
  }
};

export default apiClient;
