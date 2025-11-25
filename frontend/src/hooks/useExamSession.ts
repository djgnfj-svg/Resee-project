import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { weeklyTestAPI, WeeklyTest } from '../utils/api/exams';
import { logger } from '../utils/logger';
import { parseApiError } from '../utils/errorParser';

export const useExamSession = (initialTestId?: string, onTestComplete?: () => void) => {
  const navigate = useNavigate();
  const [currentTest, setCurrentTest] = useState<WeeklyTest | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [testResults, setTestResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const startTest = useCallback(async (testId: number) => {
    try {
      setIsLoading(true);
      const response = await weeklyTestAPI.startTest(testId);
      setCurrentTest(response.test);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setError('');

      // URL을 /exams/:id로 변경
      if (!initialTestId) {
        navigate(`/exams/${testId}`);
      }
    } catch (error) {
      logger.error('Failed to start test:', error);
      const errorMessage = parseApiError(error, '시험 시작에 실패했습니다.');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [navigate, initialTestId]);

  useEffect(() => {
    // URL에 시험 ID가 있으면 해당 시험 로드
    if (initialTestId) {
      startTest(parseInt(initialTestId));
    }
  }, [initialTestId, startTest]);

  const submitAnswer = useCallback(async (questionId: number, answer: string) => {
    if (!currentTest) return;

    try {
      await weeklyTestAPI.submitAnswer(currentTest.id, {
        question_id: questionId,
        user_answer: answer
      });
      setAnswers(prev => ({ ...prev, [questionId]: answer }));
    } catch (error) {
      logger.error('Failed to submit answer:', error);
    }
  }, [currentTest]);

  const nextQuestion = useCallback(() => {
    if (currentTest && currentQuestionIndex < currentTest.questions!.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  }, [currentTest, currentQuestionIndex]);

  const prevQuestion = useCallback(() => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  }, [currentQuestionIndex]);

  const completeTest = useCallback(async () => {
    if (!currentTest) return;

    const totalQuestions = currentTest.questions?.length || 0;
    const answeredCount = Object.keys(answers).length;

    if (answeredCount < totalQuestions) {
      const unansweredCount = totalQuestions - answeredCount;
      setError(
        `${unansweredCount}개의 문제를 아직 답하지 않았습니다. ` +
        `모든 문제에 답해주세요. (${answeredCount}/${totalQuestions} 완료)`
      );
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      await weeklyTestAPI.completeTest(currentTest.id);
      const detailedResults = await weeklyTestAPI.getTestResults(currentTest.id);
      setTestResults(detailedResults);

      if (onTestComplete) {
        onTestComplete();
      }
    } catch (error) {
      logger.error('Failed to complete test:', error);
      const errorMessage = parseApiError(error, '시험 완료에 실패했습니다.');
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [currentTest, answers, onTestComplete]);

  const resetView = useCallback(() => {
    setCurrentTest(null);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setTestResults(null);
    setError('');
    navigate('/exams');
  }, [navigate]);

  const viewTestResults = useCallback(async (testId: number) => {
    const results = await weeklyTestAPI.getTestResults(testId);
    setTestResults(results);
  }, []);

  return {
    currentTest,
    currentQuestionIndex,
    answers,
    testResults,
    isLoading,
    error,
    setError,
    startTest,
    submitAnswer,
    nextQuestion,
    prevQuestion,
    completeTest,
    resetView,
    viewTestResults,
  };
};
