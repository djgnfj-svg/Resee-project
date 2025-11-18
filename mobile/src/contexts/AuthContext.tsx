/**
 * Authentication Context
 *
 * Manages user authentication state and provides auth methods
 */

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';
import type {User, LoginData, RegisterData} from '@types/index';
import {TokenStorage, UserStorage} from '@utils/storage';
import * as authApi from '@api/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: React.ReactNode}> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Initialize auth state on app start
   */
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      const accessToken = await TokenStorage.getAccessToken();
      const savedUser = await UserStorage.getUser();

      if (accessToken && savedUser) {
        // Verify token is still valid by fetching current user
        try {
          const currentUser = await authApi.getCurrentUser();
          setUser(currentUser);
          await UserStorage.setUser(currentUser);
        } catch (error) {
          // Token expired or invalid, clear auth data
          await clearAuthData();
        }
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Login
   */
  const login = useCallback(async (data: LoginData) => {
    try {
      const response = await authApi.login(data);

      // Save tokens
      // 주의: 현재 백엔드는 refresh token을 cookie로만 반환
      // 모바일 지원을 위해 백엔드 수정 필요 (refresh token을 응답에 포함)
      await TokenStorage.setAccessToken(response.access);

      // Fetch user data
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
      await UserStorage.setUser(currentUser);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }, []);

  /**
   * Register
   */
  const register = useCallback(async (data: RegisterData) => {
    try {
      await authApi.register(data);
      // Registration successful, user needs to login
      // or auto-login if backend returns tokens
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }, []);

  /**
   * Logout
   */
  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with local cleanup even if API call fails
    } finally {
      await clearAuthData();
      setUser(null);
    }
  }, []);

  /**
   * Refresh user data
   */
  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
      await UserStorage.setUser(currentUser);
    } catch (error) {
      console.error('Failed to refresh user:', error);
      throw error;
    }
  }, []);

  /**
   * Clear auth data
   */
  const clearAuthData = async () => {
    await Promise.all([TokenStorage.clearTokens(), UserStorage.clearUser()]);
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to use auth context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
