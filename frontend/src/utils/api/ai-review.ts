import api from './index';

export const aiReviewAPI = {
  // Health check
  getHealth: async (): Promise<any> => {
    const response = await api.get('/ai-review/health/');
    return response.data;
  },

  // Question types
  getQuestionTypes: async (): Promise<any> => {
    const response = await api.get('/ai-review/question-types/');
    return response.data;
  },

  // Question generation
  generateQuestions: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/generate-questions/', data);
    return response.data;
  },

  getContentQuestions: async (contentId: number): Promise<any> => {
    const response = await api.get(`/ai-review/content/${contentId}/questions/`);
    return response.data;
  },

  // Answer evaluation
  evaluateAnswer: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/evaluate-answer/', data);
    return response.data;
  },

  // Fill-in-the-blank generation
  generateFillBlanks: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/generate-fill-blanks/', data);
    return response.data;
  },

  // Blur regions identification
  identifyBlurRegions: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/identify-blur-regions/', data);
    return response.data;
  },

  // AI Chat
  chat: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/chat/', data);
    return response.data;
  },

  // Explanation evaluation
  evaluateExplanation: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/evaluate-explanation/', data);
    return response.data;
  },

  // Weekly test
  getWeeklyTest: async (): Promise<any> => {
    const response = await api.get('/ai-review/weekly-test/');
    return response.data;
  },

  createWeeklyTest: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/weekly-test/', data);
    return response.data;
  },

  startWeeklyTest: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/weekly-test/start/', data);
    return response.data;
  },

  answerWeeklyTest: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/weekly-test/answer/', data);
    return response.data;
  },

  // Instant content check
  instantCheck: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/instant-check/', data);
    return response.data;
  },

  // Adaptive test
  startAdaptiveTest: async (data: any): Promise<any> => {
    const response = await api.post('/ai-review/adaptive-test/start/', data);
    return response.data;
  },

  answerAdaptiveTest: async (testId: number, data: any): Promise<any> => {
    const response = await api.post(`/ai-review/adaptive-test/${testId}/answer/`, data);
    return response.data;
  },
};