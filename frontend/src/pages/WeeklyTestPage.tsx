import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { weeklyTestAPI, WeeklyTest } from '../utils/api/weeklyTest';
import { contentAPI } from '../utils/api/content';
import { Category } from '../types';
import TestResultsView from '../components/weeklytest/TestResultsView';
import TestQuestionView from '../components/weeklytest/TestQuestionView';
import CategorySelectorModal from '../components/weeklytest/CategorySelectorModal';
import TestListItem from '../components/weeklytest/TestListItem';

const WeeklyTestPage: React.FC = () => {
  const navigate = useNavigate();
  const [tests, setTests] = useState<WeeklyTest[]>([]);
  const [currentTest, setCurrentTest] = useState<WeeklyTest | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [showCategorySelector, setShowCategorySelector] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([]);

  useEffect(() => {
    loadTests();
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await contentAPI.getCategories();
      setCategories(response.results || []);
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const loadTests = async () => {
    try {
      setIsLoading(true);
      const testList = await weeklyTestAPI.getWeeklyTests();
      setTests(Array.isArray(testList) ? testList : []);
    } catch (error) {
      console.error('Failed to load tests:', error);
      setError('시험 목록을 불러오는데 실패했습니다.');
      setTests([]);
    } finally {
      setIsLoading(false);
    }
  };

  const openCategorySelector = () => {
    setShowCategorySelector(true);
    setSelectedCategoryIds([]);
    setError('');
  };

  const createNewTest = async () => {
    if (selectedCategoryIds.length === 0) {
      setError('카테고리를 선택해주세요.');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      const testData = { category_ids: selectedCategoryIds };
      await weeklyTestAPI.createWeeklyTest(testData);
      await loadTests();
      setShowCategorySelector(false);
      setSelectedCategoryIds([]);
    } catch (error: any) {
      console.error('Failed to create test:', error);

      // 다양한 에러 형식 처리
      let errorMessage = '시험 생성에 실패했습니다.';

      if (error.response?.data) {
        const data = error.response.data;
        // ValidationError는 non_field_errors, detail, 또는 특정 필드로 올 수 있음
        if (data.non_field_errors && Array.isArray(data.non_field_errors)) {
          errorMessage = data.non_field_errors[0];
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.category_ids && Array.isArray(data.category_ids)) {
          errorMessage = data.category_ids[0];
        } else if (typeof data === 'string') {
          errorMessage = data;
        }
      }

      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryToggle = (categoryId: number) => {
    // 단일 선택만 허용
    setSelectedCategoryIds([categoryId]);
  };

  const startTest = async (testId: number) => {
    try {
      setIsLoading(true);
      const response = await weeklyTestAPI.startTest(testId);
      setCurrentTest(response.test);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setError('');
    } catch (error: any) {
      console.error('Failed to start test:', error);
      setError(error.response?.data?.detail || '시험 시작에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async (questionId: number, answer: string) => {
    try {
      await weeklyTestAPI.submitAnswer({
        question_id: questionId,
        user_answer: answer
      });
      setAnswers(prev => ({ ...prev, [questionId]: answer }));
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const nextQuestion = () => {
    if (currentTest && currentQuestionIndex < currentTest.questions!.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const prevQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const completeTest = async () => {
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
      await loadTests();
    } catch (error: any) {
      console.error('Failed to complete test:', error);
      setError(error.response?.data?.detail || '시험 완료에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetView = () => {
    setCurrentTest(null);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setTestResults(null);
    setError('');
  };

  const viewTestResults = async (testId: number) => {
    const results = await weeklyTestAPI.getTestResults(testId);
    setTestResults(results);
  };

  if (testResults) {
    return <TestResultsView testResults={testResults} onReset={resetView} />;
  }

  if (currentTest && currentTest.questions && currentTest.questions.length > 0) {
    return (
      <TestQuestionView
        test={currentTest}
        currentQuestionIndex={currentQuestionIndex}
        answers={answers}
        error={error}
        isLoading={isLoading}
        onAnswerSelect={submitAnswer}
        onPrevious={prevQuestion}
        onNext={nextQuestion}
        onComplete={completeTest}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            주간 시험
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            지난 일주일 동안 학습한 내용을 종합적으로 테스트해보세요.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        <div className="mb-8">
          <button
            onClick={openCategorySelector}
            disabled={isLoading}
            className="bg-blue-600 dark:bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {isLoading ? '생성 중...' : '새 주간 시험 생성'}
          </button>
        </div>

        <CategorySelectorModal
          show={showCategorySelector}
          categories={categories}
          selectedCategoryIds={selectedCategoryIds}
          error={error}
          isLoading={isLoading}
          onToggleCategory={handleCategoryToggle}
          onCreate={createNewTest}
          onClose={() => setShowCategorySelector(false)}
        />

        <div className="space-y-4">
          {isLoading && (!tests || tests.length === 0) ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600 dark:text-gray-400">로딩 중...</p>
            </div>
          ) : (!tests || tests.length === 0) ? (
            <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                아직 주간 시험이 없습니다.
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                새 주간 시험을 생성하여 학습 내용을 점검해보세요.
              </p>
            </div>
          ) : (
            tests.map((test) => (
              <TestListItem
                key={test.id}
                test={test}
                isLoading={isLoading}
                onStart={startTest}
                onViewResults={viewTestResults}
              />
            ))
          )}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium transition-colors"
          >
            ← 대시보드로 돌아가기
          </button>
        </div>
      </div>
    </div>
  );
};

export default WeeklyTestPage;
