import api from './index';
import { AuthTokens, LoginData, RegisterData, RegisterResponse, User } from '../../types';

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

  changePassword: async (data: {
    current_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<{ message: string }> => {
    const response = await api.put('/accounts/users/me/password/', data);
    return response.data;
  },

  deleteAccount: async (data: {
    password: string;
    confirmation: string;
  }): Promise<{ message: string }> => {
    const response = await api.delete('/accounts/users/me/', { data });
    return response.data;
  },

  verifyEmail: async (token: string, email: string): Promise<{ message: string; user: User }> => {
    const response = await api.post('/accounts/verify-email/', { token, email });
    return response.data;
  },

  resendVerificationEmail: async (email: string): Promise<{ message: string }> => {
    const response = await api.post('/accounts/resend-verification/', { email });
    return response.data;
  },

  updateWeeklyGoal: async (weeklyGoal: number): Promise<{ message: string; weekly_goal: number }> => {
    const response = await api.patch('/accounts/weekly-goal/', { weekly_goal: weeklyGoal });
    return response.data;
  },

  refreshToken: async (): Promise<{ access: string }> => {
    const response = await api.post('/auth/token/refresh/', {});
    return response.data;
  },

  logout: async (): Promise<{ message: string }> => {
    const response = await api.post('/auth/logout/', {});
    return response.data;
  },

  getNotificationPreferences: async (): Promise<any> => {
    const response = await api.get('/accounts/notification-preferences/');
    return response.data;
  },

  updateNotificationPreferences: async (data: any): Promise<any> => {
    const response = await api.put('/accounts/notification-preferences/', data);
    return response.data;
  },
};