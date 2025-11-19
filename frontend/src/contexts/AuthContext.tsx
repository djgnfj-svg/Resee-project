import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { User, LoginData, RegisterData, RegisterResponse } from '../types';
import { authAPI } from '../utils/api';
import { setAccessToken } from '../utils/api/index';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<RegisterResponse>;
  loginWithGoogle: (token: string) => Promise<any>;
  logout: () => void;
  isAuthenticated: boolean;
  showWelcome: boolean;
  setShowWelcome: (show: boolean) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);

  const isAuthenticated = !!user;

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to refresh token on page load (cookie-based)
        const response = await authAPI.refreshToken();
        setAccessToken(response.access);

        // Fetch user data
        const userData = await authAPI.getProfile();
        setUser(userData);
      } catch (error) {
        // No valid refresh token, user needs to login
        setAccessToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (data: LoginData) => {
    try {
      const response = await authAPI.login(data);
      // Access token stored in memory, refresh token in HttpOnly cookie
      setAccessToken(response.access);

      // Fetch user data after successful login
      const userData = await authAPI.getProfile();
      setUser(userData);
    } catch (error: any) {
      // Clean up any partial state
      setAccessToken(null);
      setUser(null);

      // Re-throw the error so the login component can handle it
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    const response = await authAPI.register(data);

    // If email verification is required, don't auto-login
    if (response.data?.requires_email_verification) {
      return response;
    }

    // Old behavior: automatically log in for users who don't need email verification
    await login({ email: data.email, password: data.password });
    // Skip welcome modal and go directly to dashboard

    return response;
  };

  const loginWithGoogle = async (token: string) => {
    try {
      const response = await authAPI.googleLogin(token);

      // Access token stored in memory, refresh token in HttpOnly cookie
      setAccessToken(response.access);

      // 사용자 정보 설정
      setUser(response.user);

      // Skip welcome modal for Google signups too

      return response;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint to clear HttpOnly cookie
      await authAPI.logout();
    } catch (error) {
      // Continue logout even if API call fails
      console.error('Logout API call failed:', error);
    }

    // Clear all React Query cache first to prevent data leakage between users
    await queryClient.clear();

    // Clear access token from memory
    setAccessToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
    } catch (error) {
    }
  };

  const value = {
    user,
    isLoading,
    login,
    register,
    loginWithGoogle,
    logout,
    isAuthenticated,
    showWelcome,
    setShowWelcome,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};