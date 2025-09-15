import api from './index';
import { DashboardData } from '../../types';

export const analyticsAPI = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await api.get('/analytics/dashboard/');
    return response.data;
  },

  getReviewStats: async (): Promise<Record<string, any>> => {
    const response = await api.get('/analytics/review-stats/');
    return response.data;
  },
};