import apiClient from './client';
import { Exam, ExamSubmission, ExamResult, PaginatedResponse } from '../types';

export const examsAPI = {
  getExams: async (): Promise<PaginatedResponse<Exam>> => {
    const response = await apiClient.get('/exams/');
    return response.data;
  },

  getExam: async (id: number): Promise<Exam> => {
    const response = await apiClient.get(`/exams/${id}/`);
    return response.data;
  },

  createExam: async (data: {
    content_ids: number[];
    title?: string;
    description?: string;
  }): Promise<Exam> => {
    const response = await apiClient.post('/exams/', data);
    return response.data;
  },

  submitExam: async (data: ExamSubmission): Promise<ExamResult> => {
    const response = await apiClient.post(
      `/exams/${data.exam_id}/submit/`,
      data
    );
    return response.data;
  },

  getExamResults: async (): Promise<PaginatedResponse<ExamResult>> => {
    const response = await apiClient.get('/exams/results/');
    return response.data;
  },

  getExamResult: async (id: number): Promise<ExamResult> => {
    const response = await apiClient.get(`/exams/results/${id}/`);
    return response.data;
  },

  deleteExam: async (id: number): Promise<void> => {
    await apiClient.delete(`/exams/${id}/`);
  },

  checkExamStatus: async (id: number): Promise<Exam> => {
    const response = await apiClient.get(`/exams/${id}/status/`);
    return response.data;
  },
};
