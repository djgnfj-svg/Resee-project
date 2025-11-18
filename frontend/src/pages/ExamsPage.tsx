import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { weeklyTestAPI, WeeklyTest } from '../utils/api/exams';
import { contentAPI } from '../utils/api/content';
import { Content } from '../types';
import TestResultsView from '../components/weeklytest/TestResultsView';
import TestQuestionView from '../components/weeklytest/TestQuestionView';
import ContentSelectorModal from '../components/weeklytest/ContentSelectorModal';
import TestListItem from '../components/weeklytest/TestListItem';

const ExamsPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [tests, setTests] = useState<WeeklyTest[]>([]);
  const [currentTest, setCurrentTest] = useState<WeeklyTest | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [showContentSelector, setShowContentSelector] = useState(false);
  const [contents, setContents] = useState<Content[]>([]);
  const [selectedContentIds, setSelectedContentIds] = useState<number[]>([]);
  const [creatingTestMessage, setCreatingTestMessage] = useState<string | null>(null);

  useEffect(() => {
    loadTests();
    loadContents();

    // URL에 시험 ID가 있으면 해당 시험 로드
    if (id) {
      startTest(parseInt(id));
    }
  }, [id]);

  const loadContents = async () => {
    try {
      const response = await contentAPI.getContents();
      setContents(response.results || []);
    } catch (error) {
      console.error('Failed to load contents:', error);
    }
  };

  const loadTests = async () => {
    try {
      setIsLoading(true);
      const testList = await weeklyTestAPI.getExams();
      setTests(Array.isArray(testList) ? testList : []);
    } catch (error) {
      console.error('Failed to load tests:', error);
      setError('시험 목록을 불러오는데 실패했습니다.');
      setTests([]);
    } finally {
      setIsLoading(false);
    }
  };

  const openContentSelector = () => {
    setShowContentSelector(true);
    setSelectedContentIds([]);
    setError('');
  };

  const createNewTest = async () => {
    if (selectedContentIds.length < 7 || selectedContentIds.length > 10) {
      setError('AI 검증된 콘텐츠를 7~10개 선택해주세요.');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      setCreatingTestMessage('시험을 생성하고 있습니다...');

      const testData = { content_ids: selectedContentIds };

      // 시험 생성 (preparing 상태로 생성됨)
      const createdTest = await weeklyTestAPI.createExam(testData);

      setShowContentSelector(false);
      setSelectedContentIds([]);

      // 문제 생성 완료까지 폴링
      setCreatingTestMessage('AI가 문제를 생성하고 있습니다... (최대 1분 소요)');
      await pollTestStatus(createdTest.id);

      // 완료 후 목록 새로고침
      setCreatingTestMessage('시험 생성이 완료되었습니다!');
      await loadTests();

      // 2초 후 메시지 제거
      setTimeout(() => setCreatingTestMessage(null), 2000);
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
        } else if (data.content_ids && Array.isArray(data.content_ids)) {
          errorMessage = data.content_ids[0];
        } else if (typeof data === 'string') {
          errorMessage = data;
        }
      }

      setError(errorMessage);
      setCreatingTestMessage(null);
    } finally {
      setIsLoading(false);
    }
  };

  const pollTestStatus = async (testId: number) => {
    const maxAttempts = 60; // 최대 60초 대기
    const pollInterval = 1000; // 1초마다 확인

    for (let i = 0; i < maxAttempts; i++) {
      try {
        const test = await weeklyTestAPI.getExam(testId);

        // preparing 상태가 아니면 완료
        if (test.status !== 'preparing') {
          return;
        }

        // 1초 대기
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      } catch (error) {
        console.error('Polling error:', error);
        // 에러 발생 시 계속 시도
      }
    }

    // 타임아웃 - 에러는 발생시키지 않고 그냥 진행
    console.warn('Test creation polling timeout');
  };

  const handleContentToggle = (contentId: number) => {
    setSelectedContentIds(prev => {
      if (prev.includes(contentId)) {
        return prev.filter(id => id !== contentId);
      } else {
        // 최대 10개까지만 선택 가능
        if (prev.length >= 10) {
          setError('최대 10개까지만 선택할 수 있습니다.');
          return prev;
        }
        setError('');
        return [...prev, contentId];
      }
    });
  };

  const startTest = async (testId: number) => {
    try {
      setIsLoading(true);
      const response = await weeklyTestAPI.startTest(testId);
      setCurrentTest(response.test);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setError('');
      // URL을 /exams/:id로 변경
      if (!id) {
        navigate(`/exams/${testId}`);
      }
    } catch (error: any) {
      console.error('Failed to start test:', error);
      setError(error.response?.data?.detail || '시험 시작에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const submitAnswer = async (questionId: number, answer: string) => {
    if (!currentTest) return;

    try {
      await weeklyTestAPI.submitAnswer(currentTest.id, {
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
    navigate('/exams');
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
    <div className="min-h-screen">
      <div>
        {/* Gradient Header */}
        <div className="mb-8 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 shadow-lg">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center space-y-4 sm:space-y-0">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">📝 주간 시험</h1>
              <p className="text-indigo-100">지난 일주일 동안 학습한 내용을 종합적으로 테스트해보세요</p>
            </div>
            <button
              onClick={openContentSelector}
              disabled={isLoading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white text-indigo-600 px-6 py-3 text-sm font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-150 w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              {isLoading ? '생성 중...' : '새 시험 생성'}
            </button>
          </div>
        </div>

        {creatingTestMessage && (
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p className="text-blue-800 dark:text-blue-200">{creatingTestMessage}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded-lg shadow-sm">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          </div>
        )}

        <ContentSelectorModal
          show={showContentSelector}
          contents={contents}
          selectedContentIds={selectedContentIds}
          error={error}
          isLoading={isLoading}
          onToggleContent={handleContentToggle}
          onCreate={createNewTest}
          onClose={() => setShowContentSelector(false)}
        />

        <div className="space-y-4">
          {isLoading && (!tests || tests.length === 0) ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-2 border-gray-200 dark:border-gray-700 border-t-indigo-600 dark:border-t-indigo-400 mx-auto mb-4"></div>
                <p className="text-gray-600 dark:text-gray-400">시험 목록을 불러오는 중...</p>
              </div>
            </div>
          ) : (!tests || tests.length === 0) ? (
            <div className="bg-white dark:bg-gray-800 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 p-12">
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-full mb-4">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                  아직 주간 시험이 없습니다
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                  새 주간 시험을 생성하여 학습 내용을 점검해보세요
                </p>
                <button
                  onClick={openContentSelector}
                  disabled={isLoading}
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:from-indigo-600 hover:to-purple-700 transition-all duration-300 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  첫 시험 만들기
                </button>
              </div>
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
      </div>
    </div>
  );
};

export default ExamsPage;
