import api from './index';

export interface WeeklyTest {
  id: number;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  status: 'pending' | 'preparing' | 'in_progress' | 'completed';
  total_questions: number;
  correct_answers: number;
  score_percentage?: number;
  started_at?: string;
  completed_at?: string;
  time_spent?: string;
  created_at: string;
  updated_at: string;
  questions?: WeeklyTestQuestion[];
  user_answers?: WeeklyTestAnswer[];
}

export interface WeeklyTestQuestion {
  id: number;
  question_type: 'multiple_choice' | 'true_false';
  question_text: string;
  choices?: string[];
  correct_answer: string;
  explanation: string;
  order: number;
  points: number;
  content: {
    id: number;
    title: string;
    content: string;
    category?: {
      id: number;
      name: string;
    };
  };
  created_at: string;
}

export interface WeeklyTestAnswer {
  id: number;
  question: WeeklyTestQuestion;
  user_answer: string;
  is_correct: boolean;
  points_earned: number;
  ai_score?: number;
  ai_feedback?: string;
  answered_at: string;
}

export interface CreateWeeklyTestData {
  title?: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  content_ids?: number[];  // 7-10개의 AI 검증된 콘텐츠 ID (수동 선택)
  category_id?: number;    // 카테고리 ID (자동 선택)
}

export interface SubmitAnswerData {
  question_id: number;
  user_answer: string;
}

export interface TestResultData {
  test: WeeklyTest;
  answers: Array<{
    question: {
      id: number;
      question_text: string;
      question_type: string;
      correct_answer: string;
      explanation: string;
      content_title: string;
    };
    user_answer: string;
    is_correct: boolean;
    points_earned: number;
    ai_score?: number;
    ai_feedback?: string;
  }>;
}

// Backward compatibility: keep type names
export type Exam = WeeklyTest;
export type ExamQuestion = WeeklyTestQuestion;
export type ExamAnswer = WeeklyTestAnswer;
export type CreateExamData = CreateWeeklyTestData;

export const examsAPI = {
  // 시험 목록 조회
  getExams: async (): Promise<Exam[]> => {
    const response = await api.get('/exams/');
    return response.data.results || [];
  },

  // 시험 생성
  createExam: async (data: CreateExamData = {}): Promise<Exam> => {
    const response = await api.post('/exams/', data);
    return response.data;
  },

  // 시험 상세 조회
  getExam: async (id: number): Promise<Exam> => {
    const response = await api.get(`/exams/${id}/`);
    return response.data;
  },

  // 시험 시작 (RESTful)
  startTest: async (testId: number): Promise<{ message: string; test: Exam }> => {
    const response = await api.post('/exams/test-sessions/', { test_id: testId });
    return response.data;
  },

  // 답변 제출 (RESTful)
  submitAnswer: async (sessionId: number, data: SubmitAnswerData): Promise<{
    message: string;
    answer_id: number;
    is_correct: boolean;
    points_earned: number;
  }> => {
    const response = await api.post(`/exams/test-sessions/${sessionId}/answers/`, data);
    return response.data;
  },

  // 시험 완료 (RESTful)
  completeTest: async (sessionId: number): Promise<{
    message: string;
    score_percentage: number;
    correct_answers: number;
    total_questions: number;
    time_spent?: string;
  }> => {
    const response = await api.patch(`/exams/test-sessions/${sessionId}/`);
    return response.data;
  },

  // 시험 결과 조회 (RESTful)
  getTestResults: async (sessionId: number): Promise<TestResultData> => {
    const response = await api.get(`/exams/test-sessions/${sessionId}/results/`);
    return response.data;
  },

  // 시험 삭제
  deleteExam: async (id: number): Promise<void> => {
    await api.delete(`/exams/${id}/`);
  }
};

// Backward compatibility
export const weeklyTestAPI = examsAPI;