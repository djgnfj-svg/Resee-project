import api from './index';
import {
  Content,
  Category,
  CreateContentData,
  UpdateContentData,
  CreateCategoryData,
  ContentListResponse,
  CategoryListResponse
} from '../../types';

// Service Worker에 캐시 무효화 메시지 전송
const invalidateContentCache = () => {
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
      type: 'INVALIDATE_CONTENT_CACHE'
    });
  }
};

export const contentAPI = {
  getContents: async (params?: string): Promise<ContentListResponse> => {
    const url = params ? `/contents/?${params}` : '/contents/';
    const response = await api.get(url);
    return response.data;
  },

  getContent: async (id: number): Promise<Content> => {
    const response = await api.get(`/contents/${id}/`);
    return response.data;
  },

  createContent: async (data: CreateContentData): Promise<Content> => {
    const response = await api.post('/contents/', data);
    invalidateContentCache(); // 캐시 무효화
    return response.data;
  },

  updateContent: async (id: number, data: UpdateContentData): Promise<Content> => {
    const response = await api.put(`/contents/${id}/`, data);
    invalidateContentCache(); // 캐시 무효화
    return response.data;
  },

  deleteContent: async (id: number): Promise<void> => {
    await api.delete(`/contents/${id}/`);
    invalidateContentCache(); // 캐시 무효화
  },

  getCategories: async (): Promise<CategoryListResponse> => {
    const response = await api.get('/categories/');
    return response.data;
  },

  createCategory: async (data: CreateCategoryData): Promise<Category> => {
    const response = await api.post('/categories/', data);
    invalidateContentCache(); // 캐시 무효화
    return response.data;
  },

  updateCategory: async (id: number, data: CreateCategoryData): Promise<Category> => {
    const response = await api.put(`/categories/${id}/`, data);
    invalidateContentCache(); // 캐시 무효화
    return response.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await api.delete(`/categories/${id}/`);
    invalidateContentCache(); // 캐시 무효화
  },

  validateContent: async (title: string, content: string): Promise<{
    is_valid: boolean;
    factual_accuracy: { score: number; issues: string[] };
    logical_consistency: { score: number; issues: string[] };
    title_relevance: { score: number; issues: string[] };
    overall_feedback: string;
  }> => {
    const response = await api.post('/contents/validate/', { title, content });
    return response.data;
  },

  // AI 검증 후 DB 저장
  validateAndSave: async (id: number): Promise<{
    message: string;
    is_valid: boolean;
    ai_validation_score?: number;
    validated_at?: string;
  }> => {
    const response = await api.post(`/contents/${id}/validate_and_save/`);
    invalidateContentCache(); // 캐시 무효화
    return response.data;
  },
};