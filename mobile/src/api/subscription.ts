import apiClient from './client';
import { Subscription, SubscriptionTierInfo } from '../types';

export const subscriptionAPI = {
  getSubscription: async (): Promise<Subscription> => {
    const response = await apiClient.get('/subscriptions/');
    return response.data;
  },

  getTiers: async (): Promise<SubscriptionTierInfo[]> => {
    const response = await apiClient.get('/subscriptions/tiers/');
    return response.data;
  },

  upgrade: async (data: {
    tier: string;
    billing_cycle?: 'monthly' | 'yearly';
    password: string;
  }): Promise<{ message: string; subscription: Subscription }> => {
    const response = await apiClient.post('/subscriptions/upgrade/', data);
    return response.data;
  },

  cancel: async (): Promise<{ message: string }> => {
    const response = await apiClient.post('/subscriptions/cancel/', {});
    return response.data;
  },

  getUsage: async (): Promise<{
    content: {
      current: number;
      limit: number;
      remaining: number;
    };
    categories: {
      current: number;
      limit: number;
      remaining: number;
    };
  }> => {
    const response = await apiClient.get('/subscriptions/usage/');
    return response.data;
  },
};
