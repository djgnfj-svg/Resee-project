/**
 * App Configuration
 *
 * Environment variables and constants
 */

// API Base URL - 개발 환경에 맞게 변경
// iOS Simulator: http://localhost:8000
// Android Emulator: http://10.0.2.2:8000
// Physical Device: http://<your-local-ip>:8000
// Production: https://resee-project-production.up.railway.app

export const API_CONFIG = {
  // 개발 환경
  DEV_BASE_URL: __DEV__
    ? 'http://localhost:8000' // iOS 시뮬레이터용
    : 'https://resee-project-production.up.railway.app',

  // 프로덕션 환경
  PROD_BASE_URL: 'https://resee-project-production.up.railway.app',

  // 현재 사용할 URL
  get BASE_URL() {
    return __DEV__ ? this.DEV_BASE_URL : this.PROD_BASE_URL;
  },

  // API 엔드포인트
  ENDPOINTS: {
    // Auth
    LOGIN: '/api/auth/token/',
    REFRESH: '/api/auth/token/refresh/',
    LOGOUT: '/api/auth/logout/',
    REGISTER: '/api/accounts/users/register/',
    GOOGLE_OAUTH: '/api/accounts/google-oauth/',

    // User
    USER_ME: '/api/accounts/users/me/',
    PROFILE: '/api/accounts/profile/',

    // Content
    CONTENTS: '/api/contents/',
    CATEGORIES: '/api/categories/',

    // Review
    REVIEW_SCHEDULES: '/api/review/schedules/',
    REVIEW_HISTORY: '/api/review/history/',
    REVIEW_DASHBOARD: '/api/review/dashboard/',
    TODAY_REVIEWS: '/api/review/schedules/today/',

    // Stats
    CATEGORY_STATS: '/api/review/category-stats/',

    // Exams
    EXAMS: '/api/exams/',
  },

  // Request timeout
  TIMEOUT: 30000,

  // Headers
  get HEADERS() {
    return {
      'Content-Type': 'application/json',
      'X-Client-Type': 'mobile', // 모바일 클라이언트 식별
    };
  },
};

// Storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_DATA: 'user_data',
  THEME: 'theme',
  LANGUAGE: 'language',
};

// App constants
export const APP_CONFIG = {
  NAME: 'Resee',
  VERSION: '1.0.0',
  SUPPORT_EMAIL: 'support@reseeall.com',
};
