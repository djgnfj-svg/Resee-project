import React, { createContext, useContext, useEffect, useState } from 'react';
import { authAPI, setAccessToken, getAccessToken } from '../api';
import { User, LoginData, RegisterData, RegisterResponse } from '../types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<RegisterResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
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

  const isAuthenticated = !!user;

  useEffect(() => {
    initAuth();
  }, []);

  const initAuth = async () => {
    try {
      const token = await getAccessToken();
      if (token) {
        const userData = await authAPI.getProfile();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      await setAccessToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (data: LoginData) => {
    try {
      const response = await authAPI.login(data);
      await setAccessToken(response.access);

      const userData = await authAPI.getProfile();
      setUser(userData);
    } catch (error: any) {
      await setAccessToken(null);
      setUser(null);
      throw error;
    }
  };

  const register = async (data: RegisterData): Promise<RegisterResponse> => {
    const response = await authAPI.register(data);

    // If email verification is required, don't auto-login
    if (response.data?.requires_email_verification) {
      return response;
    }

    // Auto-login if verification not required
    await login({ email: data.email, password: data.password });
    return response;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      await setAccessToken(null);
      setUser(null);
    }
  };

  const refreshUser = async () => {
    try {
      const userData = await authAPI.getProfile();
      setUser(userData);
    } catch (error) {
      console.error('Refresh user error:', error);
      await setAccessToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
