/**
 * Secure Storage Utility
 *
 * Uses encrypted storage for sensitive data like tokens
 */

import EncryptedStorage from 'react-native-encrypted-storage';
import {STORAGE_KEYS} from './config';
import type {User} from '@types/index';

/**
 * Token Storage
 */
export const TokenStorage = {
  /**
   * Save access token
   */
  async setAccessToken(token: string): Promise<void> {
    try {
      await EncryptedStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
    } catch (error) {
      console.error('Failed to save access token:', error);
      throw error;
    }
  },

  /**
   * Get access token
   */
  async getAccessToken(): Promise<string | null> {
    try {
      return await EncryptedStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    } catch (error) {
      console.error('Failed to get access token:', error);
      return null;
    }
  },

  /**
   * Save refresh token
   */
  async setRefreshToken(token: string): Promise<void> {
    try {
      await EncryptedStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
    } catch (error) {
      console.error('Failed to save refresh token:', error);
      throw error;
    }
  },

  /**
   * Get refresh token
   */
  async getRefreshToken(): Promise<string | null> {
    try {
      return await EncryptedStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
    } catch (error) {
      console.error('Failed to get refresh token:', error);
      return null;
    }
  },

  /**
   * Save both tokens
   */
  async setTokens(accessToken: string, refreshToken: string): Promise<void> {
    try {
      await Promise.all([
        this.setAccessToken(accessToken),
        this.setRefreshToken(refreshToken),
      ]);
    } catch (error) {
      console.error('Failed to save tokens:', error);
      throw error;
    }
  },

  /**
   * Clear all tokens
   */
  async clearTokens(): Promise<void> {
    try {
      await Promise.all([
        EncryptedStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN),
        EncryptedStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
      ]);
    } catch (error) {
      console.error('Failed to clear tokens:', error);
      throw error;
    }
  },
};

/**
 * User Data Storage
 */
export const UserStorage = {
  /**
   * Save user data
   */
  async setUser(user: User): Promise<void> {
    try {
      await EncryptedStorage.setItem(
        STORAGE_KEYS.USER_DATA,
        JSON.stringify(user),
      );
    } catch (error) {
      console.error('Failed to save user data:', error);
      throw error;
    }
  },

  /**
   * Get user data
   */
  async getUser(): Promise<User | null> {
    try {
      const userData = await EncryptedStorage.getItem(STORAGE_KEYS.USER_DATA);
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Failed to get user data:', error);
      return null;
    }
  },

  /**
   * Clear user data
   */
  async clearUser(): Promise<void> {
    try {
      await EncryptedStorage.removeItem(STORAGE_KEYS.USER_DATA);
    } catch (error) {
      console.error('Failed to clear user data:', error);
      throw error;
    }
  },
};

/**
 * Clear all stored data
 */
export const clearAllData = async (): Promise<void> => {
  try {
    await EncryptedStorage.clear();
  } catch (error) {
    console.error('Failed to clear all data:', error);
    throw error;
  }
};
