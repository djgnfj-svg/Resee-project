/**
 * AI Review API Client
 */
import api from './api';
import type {
  AIQuestionType,
  AIQuestion,
  GenerateQuestionsRequest,
  AIAnswerEvaluationRequest,
  AIAnswerEvaluationResponse,
  FillBlankRequest,
  FillBlankResponse,
  BlurRegionsRequest,
  BlurRegionsResponse,
  AIChatRequest,
  AIChatResponse,
  PaginatedResponse,
} from '../types/ai-review';

class AIReviewAPI {
  // Health check
  async checkHealth(): Promise<{ status: string; active_question_types: number; ai_service_available: boolean }> {
    const response = await api.get('/ai-review/health/');
    return response.data;
  }

  // Question Types
  async getQuestionTypes(): Promise<AIQuestionType[]> {
    const response = await api.get<PaginatedResponse<AIQuestionType>>('/ai-review/question-types/');
    return response.data.results;
  }

  // Question Generation
  async generateQuestions(request: GenerateQuestionsRequest): Promise<AIQuestion[]> {
    // AI 서비스 미구현 - 에러 던지기
    throw new Error('AI 질문 생성 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려주세요! 🚀');
    
    // 추후 구현 시 활성화
    // const response = await api.post('/ai-review/generate-questions/', request);
    // return response.data;
  }

  // Get questions for specific content
  async getContentQuestions(contentId: number): Promise<AIQuestion[]> {
    const response = await api.get<PaginatedResponse<AIQuestion>>(`/ai-review/content/${contentId}/questions/`);
    return response.data.results;
  }

  // Answer evaluation
  async evaluateAnswer(request: AIAnswerEvaluationRequest): Promise<AIAnswerEvaluationResponse> {
    // AI 서비스 미구현 - 에러 던지기
    throw new Error('AI 답변 평가 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려주세요! 🚀');
    
    // 추후 구현 시 활성화
    // const response = await api.post('/ai-review/evaluate-answer/', request);
    // return response.data;
  }


  // Fill-in-blank generation
  async generateFillBlanks(request: FillBlankRequest): Promise<FillBlankResponse> {
    // AI 서비스 미구현 - 에러 던지기
    throw new Error('빈칸 채우기 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려주세요! 🚀');
    
    // 추후 구현 시 활성화
    // const response = await api.post('/ai-review/generate-fill-blanks/', request);
    // return response.data;
  }

  // Blur regions identification
  async identifyBlurRegions(request: BlurRegionsRequest): Promise<BlurRegionsResponse> {
    // AI 서비스 미구현 - 에러 던지기
    throw new Error('블러 처리 학습 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려주세요! 🚀');
    
    // 추후 구현 시 활성화
    // const response = await api.post('/ai-review/identify-blur-regions/', request);
    // return response.data;
  }

  // AI Chat
  async chatAboutContent(request: AIChatRequest): Promise<AIChatResponse> {
    // AI 서비스 미구현 - 에러 던지기
    throw new Error('AI 채팅 기능은 현재 개발 중입니다. 곧 제공될 예정이니 조금만 기다려주세요! 🚀');
    
    // 추후 구현 시 활성화
    // const response = await api.post('/ai-review/chat/', request);
    // return response.data;
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

  getQuestionTypeLabel(type: string): string {
    switch (type) {
      case 'multiple_choice': return '객관식';
      case 'fill_blank': return '빈칸 채우기';
      case 'blur_processing': return '블러 처리';
      default: return type;
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