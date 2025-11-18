/**
 * Review API
 */

import {apiRequest} from '@utils/apiClient';
import {API_CONFIG} from '@utils/config';
import type {
  ReviewSchedule,
  TodayReviewsResponse,
  ReviewHistory,
  CompleteReviewData,
  DashboardData,
  ReviewStatsData,
  PaginatedResponse,
} from '@types/index';

/**
 * Get review schedules
 */
export const getReviewSchedules = async (params?: {
  is_active?: boolean;
  page?: number;
}): Promise<PaginatedResponse<ReviewSchedule>> => {
  return apiRequest<PaginatedResponse<ReviewSchedule>>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.REVIEW_SCHEDULES,
    params,
  });
};

/**
 * Get today's reviews
 */
export const getTodayReviews = async (): Promise<TodayReviewsResponse> => {
  return apiRequest<TodayReviewsResponse>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.TODAY_REVIEWS,
  });
};

/**
 * Get single review schedule
 */
export const getReviewSchedule = async (
  id: number,
): Promise<ReviewSchedule> => {
  return apiRequest<ReviewSchedule>({
    method: 'GET',
    url: `${API_CONFIG.ENDPOINTS.REVIEW_SCHEDULES}${id}/`,
  });
};

/**
 * Complete a review
 */
export const completeReview = async (
  data: CompleteReviewData,
): Promise<ReviewHistory> => {
  return apiRequest<ReviewHistory>({
    method: 'POST',
    url: `${API_CONFIG.ENDPOINTS.REVIEW_SCHEDULES}complete/`,
    data,
  });
};

/**
 * Get review history
 */
export const getReviewHistory = async (params?: {
  content?: number;
  result?: 'remembered' | 'partial' | 'forgot';
  page?: number;
}): Promise<PaginatedResponse<ReviewHistory>> => {
  return apiRequest<PaginatedResponse<ReviewHistory>>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.REVIEW_HISTORY,
    params,
  });
};

/**
 * Get dashboard stats
 */
export const getDashboardStats = async (): Promise<DashboardData> => {
  return apiRequest<DashboardData>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.REVIEW_DASHBOARD,
  });
};

/**
 * Get review stats (detailed)
 */
export const getReviewStats = async (params?: {
  period?: number;
}): Promise<ReviewStatsData> => {
  return apiRequest<ReviewStatsData>({
    method: 'GET',
    url: `${API_CONFIG.ENDPOINTS.REVIEW_HISTORY}stats/`,
    params,
  });
};

/**
 * Get category review stats
 */
export const getCategoryStats = async (): Promise<any> => {
  return apiRequest({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.CATEGORY_STATS,
  });
};
