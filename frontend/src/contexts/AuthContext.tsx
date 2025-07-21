import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, LoginData, RegisterData, RegisterResponse } from '../types';
import { authAPI } from '../utils/api';

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
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);

  const isAuthenticated = !!user;

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null); // Properly clear user state
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (data: LoginData) => {
    try {
      const tokens = await authAPI.login(data);
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      await fetchUser();
    } catch (error: any) {
      // Clean up any partial state
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      
      // Re-throw the error so the login component can handle it
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    const response = await authAPI.register(data);
    
    // If email verification is required, don't auto-login
    if (response.requires_email_verification) {
      return response;
    }
    
    // Old behavior: automatically log in for users who don't need email verification
    await login({ email: data.email, password: data.password });
    // Show welcome modal for new users
    setShowWelcome(true);
    
    return response;
  };

  const loginWithGoogle = async (token: string) => {
    try {
      const response = await authAPI.googleLogin(token);
      
      // JWT 토큰 저장
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      
      // 사용자 정보 설정
      setUser(response.user);
      
      // 신규 사용자인 경우 환영 모달 표시
      if (response.is_new_user) {
        setShowWelcome(true);
      }
      
      return response;
    } catch (error) {
      console.error('Google login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
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
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};