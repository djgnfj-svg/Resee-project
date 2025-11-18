/**
 * Authentication API
 */

import {apiRequest} from '@utils/apiClient';
import {API_CONFIG} from '@utils/config';
import type {
  LoginData,
  RegisterData,
  RegisterResponse,
  LoginResponse,
  User,
} from '@types/index';

/**
 * Login with email and password
 */
export const login = async (data: LoginData): Promise<LoginResponse> => {
  return apiRequest<LoginResponse>({
    method: 'POST',
    url: API_CONFIG.ENDPOINTS.LOGIN,
    data,
  });
};

/**
 * Register new user
 */
export const register = async (
  data: RegisterData,
): Promise<RegisterResponse> => {
  return apiRequest<RegisterResponse>({
    method: 'POST',
    url: API_CONFIG.ENDPOINTS.REGISTER,
    data,
  });
};

/**
 * Logout
 */
export const logout = async (): Promise<{message: string}> => {
  return apiRequest<{message: string}>({
    method: 'POST',
    url: API_CONFIG.ENDPOINTS.LOGOUT,
  });
};

/**
 * Get current user info
 */
export const getCurrentUser = async (): Promise<User> => {
  return apiRequest<User>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.USER_ME,
  });
};

/**
 * Google OAuth login
 */
export const googleOAuth = async (token: string): Promise<LoginResponse> => {
  return apiRequest<LoginResponse>({
    method: 'POST',
    url: API_CONFIG.ENDPOINTS.GOOGLE_OAUTH,
    data: {token},
  });
};

/**
 * Request password reset
 */
export const requestPasswordReset = async (
  email: string,
): Promise<{message: string}> => {
  return apiRequest<{message: string}>({
    method: 'POST',
    url: '/api/accounts/password-reset/',
    data: {email},
  });
};

/**
 * Verify email
 */
export const verifyEmail = async (
  token: string,
): Promise<{message: string}> => {
  return apiRequest<{message: string}>({
    method: 'POST',
    url: '/api/accounts/verify-email/',
    data: {token},
  });
};

/**
 * Resend verification email
 */
export const resendVerificationEmail = async (): Promise<{message: string}> => {
  return apiRequest<{message: string}>({
    method: 'POST',
    url: '/api/accounts/resend-verification/',
  });
};
