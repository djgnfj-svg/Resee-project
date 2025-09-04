/**
 * AI Review API Client
 */
import api from './api';
import type {
  WeeklyTest,
  WeeklyTestQuestion,
  WeeklyTestCreateRequest,
  CategoryChoice,
  PaginatedResponse,
} from '../types/ai-review';

class AIReviewAPI {
  // Health check
  async checkHealth(): Promise<{ status: string; active_question_types: number; ai_service_available: boolean }> {
    const response = await api.get('/ai-review/health/');
    return response.data;
  }



  // AI Content Quality Check
  async checkContentQuality(title: string, content: string): Promise<any> {
    const response = await api.post('/ai-review/content-check/', {
      title,
      content
    });
    return response.data;
  }

  // Weekly Test
  async getWeeklyTestCategories(): Promise<CategoryChoice[]> {
    const response = await api.get('/ai-review/weekly-test/categories/');
    return response.data;
  }

  async createWeeklyTest(request: WeeklyTestCreateRequest): Promise<WeeklyTest> {
    const response = await api.post('/ai-review/weekly-test/', request);
    return response.data;
  }

  async startWeeklyTest(testId: number): Promise<WeeklyTest> {
    const response = await api.post('/ai-review/weekly-test/start/', { test_id: testId });
    return response.data;
  }

  async answerWeeklyTestQuestion(
    questionId: number, 
    userAnswer: string, 
    timeSpent?: number
  ): Promise<{ is_correct: boolean; ai_score?: number; next_question?: WeeklyTestQuestion }> {
    const response = await api.post('/ai-review/weekly-test/answer/', {
      question_id: questionId,
      user_answer: userAnswer,
      time_spent_seconds: timeSpent
    });
    return response.data;
  }

  async getWeeklyTest(testId: number): Promise<WeeklyTest> {
    const response = await api.get(`/ai-review/weekly-test/${testId}/`);
    return response.data;
  }

  async getUserWeeklyTests(): Promise<WeeklyTest[]> {
    const response = await api.get('/api/ai-review/weekly-tests/');
    return response.data.results;
  }


  // Utility functions

  getDifficultyLabel(difficulty: number): string {
    switch (difficulty) {
      case 1: return '매우 쉬움';
      case 2: return '쉬움';
      case 3: return '보통';
      case 4: return '어려움';
      case 5: return '매우 어려움';
      default: return '보통';
    }
  }


  getScoreLabel(score: number): string {
    if (score >= 0.9) return '우수';
    if (score >= 0.7) return '양호';
    if (score >= 0.5) return '보통';
    if (score >= 0.3) return '미흡';
    return '부족';
  }

  getScoreColor(score: number): string {
    if (score >= 0.9) return 'green';
    if (score >= 0.7) return 'blue';
    if (score >= 0.5) return 'yellow';
    if (score >= 0.3) return 'orange';
    return 'red';
  }
}

// Export singleton instance
export const aiReviewAPI = new AIReviewAPI();