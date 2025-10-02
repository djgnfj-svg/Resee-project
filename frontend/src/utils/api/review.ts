import api from './index';
import {
  ReviewSchedule,
  ReviewHistory,
  CompleteReviewData,
  CreateReviewHistoryData,
  PaginatedResponse
} from '../../types';

export const reviewAPI = {
  getTodayReviews: async (params?: string): Promise<ReviewSchedule[]> => {
    const url = params ? `/review/today/${params}` : '/review/today/';
    const response = await api.get(url);
    return response.data;
  },

  getSchedules: async (): Promise<PaginatedResponse<ReviewSchedule> | ReviewSchedule[]> => {
    const response = await api.get('/review/schedules/');
    return response.data;
  },

  getHistory: async (): Promise<PaginatedResponse<ReviewHistory> | ReviewHistory[]> => {
    const response = await api.get('/review/history/');
    return response.data;
  },

  createHistory: async (data: CreateReviewHistoryData): Promise<ReviewHistory> => {
    const response = await api.post('/review/history/', data);
    return response.data;
  },

  completeReview: async (data: CompleteReviewData): Promise<{
    message: string;
    next_review_date?: string;
    ai_evaluation?: {
      score: number;
      feedback: string;
    };
  }> => {
    const response = await api.post('/review/complete/', data);
    return response.data;
  },

  getCategoryStats: async (): Promise<Record<string, any>> => {
    const response = await api.get('/review/category-stats/');
    return response.data;
  },
};