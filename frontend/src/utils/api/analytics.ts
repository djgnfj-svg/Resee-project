import api from './index';
import { DashboardData } from '../../types';

export const analyticsAPI = {
  getDashboard: async (): Promise<DashboardData> => {
    const response = await api.get('/analytics/dashboard/');
    return response.data;
  },

};