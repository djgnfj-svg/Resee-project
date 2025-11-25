import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import TestResultsView from '../components/weeklytest/TestResultsView';
import TestQuestionView from '../components/weeklytest/TestQuestionView';
import ContentSelectorModal from '../components/weeklytest/ContentSelectorModal';
import TestListItem from '../components/weeklytest/TestListItem';
import { useExamList } from '../hooks/useExamList';
import { useExamCreation } from '../hooks/useExamCreation';
import { useExamSession } from '../hooks/useExamSession';

const ExamsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  useEffect(() => {
    document.title = '주간시험 - Resee';
  }, []);

  // 시험 목록 관리
  const { tests, isLoading: listLoading, error: listError, loadTests } = useExamList();

  // 시험 생성 관리
  const {
    showContentSelector,
    contents,
    selectedContentIds,
    creatingTestMessage,
    isLoading: creationLoading,
    error: creationError,
    openContentSelector,
    handleContentToggle,
    createNewTest,
    closeContentSelector,
  } = useExamCreation(loadTests);

  // 시험 응시 관리
  const {
    currentTest,
    currentQuestionIndex,
    answers,
    testResults,
    isLoading: sessionLoading,
    error: sessionError,
    startTest,
    submitAnswer,
    nextQuestion,
    prevQuestion,
    completeTest,
    resetView,
    viewTestResults,
  } = useExamSession(id, loadTests);

  // 통합 상태
  const isLoading = listLoading || creationLoading || sessionLoading;
  const error = listError || creationError || sessionError;

  // 결과 보기
  if (testResults) {
    return <TestResultsView testResults={testResults} onReset={resetView} />;
  }

  // 시험 진행 중
  if (currentTest && currentTest.questions && currentTest.questions.length > 0) {
    return (
      <TestQuestionView
        test={currentTest}
        currentQuestionIndex={currentQuestionIndex}
        answers={answers}
        error={sessionError}
        isLoading={sessionLoading}
        onAnswerSelect={submitAnswer}
        onPrevious={prevQuestion}
        onNext={nextQuestion}
        onComplete={completeTest}
      />
    );
  }

  // 시험 목록 화면
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

        {/* 시험 생성 상태 메시지 */}
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

        {/* 에러 메시지 */}
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

        {/* 콘텐츠 선택 모달 */}
        <ContentSelectorModal
          show={showContentSelector}
          contents={contents}
          selectedContentIds={selectedContentIds}
          error={creationError}
          isLoading={creationLoading}
          onToggleContent={handleContentToggle}
          onCreate={createNewTest}
          onClose={closeContentSelector}
        />

        {/* 시험 목록 */}
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
                isLoading={sessionLoading}
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
