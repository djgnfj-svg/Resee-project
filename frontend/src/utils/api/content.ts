import api from './index';
import {
  Content,
  Category,
  CreateContentData,
  UpdateContentData,
  CreateCategoryData,
  PaginatedResponse
} from '../../types';

export const contentAPI = {
  getContents: async (params?: string): Promise<PaginatedResponse<Content> | Content[]> => {
    const url = params ? `/content/contents/?${params}` : '/content/contents/';
    const response = await api.get(url);
    return response.data;
  },

  createContent: async (data: CreateContentData): Promise<Content> => {
    const response = await api.post('/content/contents/', data);
    return response.data;
  },

  updateContent: async (id: number, data: UpdateContentData): Promise<Content> => {
    const response = await api.put(`/content/contents/${id}/`, data);
    return response.data;
  },

  deleteContent: async (id: number): Promise<void> => {
    await api.delete(`/content/contents/${id}/`);
  },

  getCategories: async (): Promise<PaginatedResponse<Category> | Category[]> => {
    const response = await api.get('/content/categories/');
    return response.data;
  },

  createCategory: async (data: CreateCategoryData): Promise<Category> => {
    const response = await api.post('/content/categories/', data);
    return response.data;
  },

  updateCategory: async (id: number, data: CreateCategoryData): Promise<Category> => {
    const response = await api.put(`/content/categories/${id}/`, data);
    return response.data;
  },

  deleteCategory: async (id: number): Promise<void> => {
    await api.delete(`/content/categories/${id}/`);
  },

  getContentsByCategory: async (): Promise<Record<string, Content[]>> => {
    const response = await api.get('/content/contents/by_category/');
    return response.data;
  },
};