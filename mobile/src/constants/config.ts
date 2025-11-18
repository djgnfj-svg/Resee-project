import Constants from 'expo-constants';

// API Configuration
export const API_CONFIG = {
  // Development: Django backend running in Docker
  // Production: Railway deployment
  BASE_URL: __DEV__
    ? 'http://localhost:8000/api'  // For web browser testing
    // ? 'http://172.23.100.45:8000/api'  // WSL IP for real device testing
    : 'https://resee-project-production.up.railway.app/api',

  TIMEOUT: 30000, // 30 seconds
};

// App Configuration
export const APP_CONFIG = {
  APP_NAME: 'Resee',
  VERSION: Constants.expoConfig?.version || '1.0.0',
};

// Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  USER_DATA: 'user_data',
  THEME_MODE: 'theme_mode',
};

// Review Modes
export const REVIEW_MODES = {
  OBJECTIVE: 'objective',
  DESCRIPTIVE: 'descriptive',
  MULTIPLE_CHOICE: 'multiple_choice',
} as const;

// Subscription Tiers
export const SUBSCRIPTION_TIERS = {
  FREE: 'free',
  BASIC: 'basic',
  PRO: 'pro',
} as const;
