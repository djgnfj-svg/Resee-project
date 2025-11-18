import apiClient from './client';
import {
  ReviewSchedule,
  ReviewHistory,
  CompleteReviewData,
  PaginatedResponse,
  DashboardData,
  TodayReviewsResponse,
} from '../types';

export const reviewAPI = {
  getTodayReviews: async (
    params?: string
  ): Promise<TodayReviewsResponse | ReviewSchedule[]> => {
    const url = params
      ? `/review/schedules/today/${params}`
      : '/review/schedules/today/';
    const response = await apiClient.get(url);
    return response.data;
  },

  getSchedules: async (): Promise<
    PaginatedResponse<ReviewSchedule> | ReviewSchedule[]
  > => {
    const response = await apiClient.get('/review/schedules/');
    return response.data;
  },

  getHistory: async (): Promise<
    PaginatedResponse<ReviewHistory> | ReviewHistory[]
  > => {
    const response = await apiClient.get('/review/history/');
    return response.data;
  },

  createHistory: async (data: CompleteReviewData): Promise<ReviewHistory> => {
    const response = await apiClient.post('/review/history/', data);
    return response.data;
  },

  completeReview: async (
    scheduleId: number,
    data: Omit<CompleteReviewData, 'content_id'>
  ): Promise<{
    message: string;
    next_review_date?: string;
    ai_evaluation?: {
      score: number;
      feedback: string;
      auto_result?: 'remembered' | 'forgot';
      is_correct?: boolean;
    };
  }> => {
    const response = await apiClient.post(
      `/review/schedules/${scheduleId}/completions/`,
      data
    );
    return response.data;
  },

  getCategoryStats: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get('/review/category-stats/');
    return response.data;
  },

  getDashboard: async (): Promise<DashboardData> => {
    const response = await apiClient.get('/review/dashboard/');
    return response.data;
  },
};
