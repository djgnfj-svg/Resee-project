/**
 * Content API
 */

import {apiRequest} from '@utils/apiClient';
import {API_CONFIG} from '@utils/config';
import type {
  Content,
  ContentListResponse,
  CreateContentData,
  UpdateContentData,
  Category,
  CategoryListResponse,
  CreateCategoryData,
  AIValidationResult,
} from '@types/index';

/**
 * Get content list
 */
export const getContents = async (params?: {
  category?: number;
  category_slug?: string;
  search?: string;
  ordering?: string;
  page?: number;
}): Promise<ContentListResponse> => {
  return apiRequest<ContentListResponse>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.CONTENTS,
    params,
  });
};

/**
 * Get single content
 */
export const getContent = async (id: number): Promise<Content> => {
  return apiRequest<Content>({
    method: 'GET',
    url: `${API_CONFIG.ENDPOINTS.CONTENTS}${id}/`,
  });
};

/**
 * Create new content
 */
export const createContent = async (
  data: CreateContentData,
): Promise<Content> => {
  return apiRequest<Content>({
    method: 'POST',
    url: API_CONFIG.ENDPOINTS.CONTENTS,
    data,
  });
};

/**
 * Update content
 */
export const updateContent = async (
  id: number,
  data: UpdateContentData,
): Promise<Content> => {
  return apiRequest<Content>({
    method: 'PATCH',
    url: `${API_CONFIG.ENDPOINTS.CONTENTS}${id}/`,
    data,
  });
};

/**
 * Delete content
 */
export const deleteContent = async (id: number): Promise<void> => {
  return apiRequest<void>({
    method: 'DELETE',
    url: `${API_CONFIG.ENDPOINTS.CONTENTS}${id}/`,
  });
};

/**
 * Validate content with AI
 */
export const validateContent = async (data: {
  title: string;
  content: string;
}): Promise<AIValidationResult> => {
  return apiRequest<AIValidationResult>({
    method: 'POST',
    url: `${API_CONFIG.ENDPOINTS.CONTENTS}validate/`,
    data,
  });
};

/**
 * Validate and save content
 */
export const validateAndSaveContent = async (
  id: number,
): Promise<{
  message: string;
  is_valid: boolean;
  ai_validation_score: number;
  validated_at: string;
  result: AIValidationResult;
}> => {
  return apiRequest({
    method: 'POST',
    url: `${API_CONFIG.ENDPOINTS.CONTENTS}${id}/validate_and_save/`,
  });
};

// ========== Categories ==========

/**
 * Get category list
 */
export const getCategories = async (): Promise<CategoryListResponse> => {
  return apiRequest<CategoryListResponse>({
    method: 'GET',
    url: API_CONFIG.ENDPOINTS.CATEGORIES,
  });
};

/**
 * Get single category
 */
export const getCategory = async (id: number): Promise<Category> => {
  return apiRequest<Category>({
    method: 'GET',
    url: `${API_CONFIG.ENDPOINTS.CATEGORIES}${id}/`,
  });
};

/**
 * Create new category
 */
export const createCategory = async (
  data: CreateCategoryData,
): Promise<Category> => {
  return apiRequest<Category>({
    method: 'POST',
    url: API_CONFIG.ENDPOINTS.CATEGORIES,
    data,
  });
};

/**
 * Update category
 */
export const updateCategory = async (
  id: number,
  data: Partial<CreateCategoryData>,
): Promise<Category> => {
  return apiRequest<Category>({
    method: 'PATCH',
    url: `${API_CONFIG.ENDPOINTS.CATEGORIES}${id}/`,
    data,
  });
};

/**
 * Delete category
 */
export const deleteCategory = async (id: number): Promise<void> => {
  return apiRequest<void>({
    method: 'DELETE',
    url: `${API_CONFIG.ENDPOINTS.CATEGORIES}${id}/`,
  });
};
