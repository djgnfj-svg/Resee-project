import apiClient from './client';
import {
  Content,
  Category,
  ContentListResponse,
  CategoryListResponse,
} from '../types';

export const contentAPI = {
  getContents: async (params?: string): Promise<ContentListResponse> => {
    const url = params ? `/contents/?${params}` : '/contents/';
    const response = await apiClient.get(url);
    return response.data;
  },

  getContent: async (id: number): Promise<Content> => {
    const response = await apiClient.get(`/contents/${id}/`);
    return response.data;
  },

  createContent: async (data: {
    title: string;
    content: string;
    category?: number;
    review_mode?: string;
  }): Promise<Content> => {
    const response = await apiClient.post('/contents/', data);
    return response.data;
  },

  updateContent: async (
    id: number,
    data: {
      title?: string;
      content?: string;
      category?: number;
      review_mode?: string;
    }
  ): Promise<Content> => {
    const response = await apiClient.put(`/contents/${id}/`, data);
    return response.data;
  },

  deleteContent: async (id: number): Promise<void> => {
    await apiClient.delete(`/contents/${id}/`);
  },

  getCategories: async (): Promise<CategoryListResponse> => {
    const response = await apiClient.get('/categories/');
    return response.data;
  },

  createCategory: async (data: {
    name: string;
    description?: string;
  }): Promise<Category> => {
    const response = await apiClient.post('/categories/', data);
    return response.data;
  },

  updateCategory: async (
    id: number,
    data: {
      name: string;
      description?: string;
    }
  ): Promise<Category> => {
    const response = await apiClient.put(`/categories/${id}/`, data);
    return response.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await apiClient.delete(`/categories/${id}/`);
  },

  validateContent: async (
    title: string,
    content: string
  ): Promise<{
    is_valid: boolean;
    factual_accuracy: { score: number; issues: string[] };
    logical_consistency: { score: number; issues: string[] };
    title_relevance: { score: number; issues: string[] };
    overall_feedback: string;
  }> => {
    const response = await apiClient.post('/contents/validate/', {
      title,
      content,
    });
    return response.data;
  },

  validateAndSave: async (
    id: number
  ): Promise<{
    message: string;
    is_valid: boolean;
    ai_validation_score?: number;
    validated_at?: string;
  }> => {
    const response = await apiClient.post(`/contents/${id}/validate_and_save/`);
    return response.data;
  },
};
