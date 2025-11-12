import api from './index';
import {
  Subscription,
  SubscriptionTierInfo,
  SubscriptionUpgradeData,
  PaymentHistoryResponse
} from '../../types';

export const subscriptionAPI = {
  getSubscription: async (): Promise<Subscription> => {
    const response = await api.get('/accounts/subscription/');
    return response.data;
  },

  getSubscriptionTiers: async (): Promise<SubscriptionTierInfo[]> => {
    const response = await api.get('/accounts/subscription/tiers/');
    return response.data;
  },

  upgradeSubscription: async (data: SubscriptionUpgradeData): Promise<Subscription> => {
    const response = await api.patch('/accounts/subscriptions/me/', data);
    return response.data;
  },

  downgradeSubscription: async (data: SubscriptionUpgradeData): Promise<Subscription> => {
    const response = await api.patch('/accounts/subscriptions/me/', data);
    return response.data;
  },

  cancelSubscription: async (password: string): Promise<Subscription> => {
    const response = await api.delete('/accounts/subscriptions/me/', { data: { password } });
    return response.data;
  },

  getPaymentHistory: async (): Promise<PaymentHistoryResponse> => {
    const response = await api.get('/accounts/payment-history/');
    return response.data;
  },

  toggleAutoRenewal: async (password: string, autoRenewal: boolean): Promise<Subscription> => {
    const response = await api.patch('/accounts/subscriptions/me/', {
      auto_renewal: autoRenewal,
      password
    });
    return response.data;
  },

  getBillingSchedule: async (): Promise<any> => {
    const response = await api.get('/accounts/billing-schedule/');
    return response.data;
  },
};