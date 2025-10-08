import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { weeklyTestAPI, WeeklyTest } from '../utils/api/weeklyTest';
import { contentAPI } from '../utils/api/content';
import { Category } from '../types';

/**
 * 백틱으로 감싸진 텍스트를 코드 스타일로 렌더링
 */
const renderTextWithCode = (text: string) => {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  const regex = /`([^`]+)`/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // 백틱 앞의 일반 텍스트
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    // 백틱 안의 코드
    parts.push(
      <code
        key={match.index}
        className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 text-blue-600 dark:text-blue-300 rounded text-sm font-mono"
      >
        {match[1]}
      </code>
    );

    lastIndex = match.index + match[0].length;
  }

  // 남은 텍스트
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
};

const WeeklyTestPage: React.FC = () => {
  const navigate = useNavigate();
  const [tests, setTests] = useState<WeeklyTest[]>([]);
  const [currentTest, setCurrentTest] = useState<WeeklyTest | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [error, setError] = useState<string>('');

  // 카테고리 선택 관련 상태
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
      setTests([]); // 에러 시 빈 배열로 설정
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
      const testData = { category_ids: selectedCategoryIds };

      await weeklyTestAPI.createWeeklyTest(testData);
      await loadTests();
      setShowCategorySelector(false);
      setSelectedCategoryIds([]);
      setError('');
    } catch (error: any) {
      console.error('Failed to create test:', error);
      setError(error.response?.data?.detail || '시험 생성에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryToggle = (categoryId: number) => {
    setSelectedCategoryIds(prev =>
      prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId]
    );
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

    // BUG-SECTION5-001 FIX: 모든 문제에 답했는지 검증
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
      setError(''); // 에러 메시지 초기화
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

  // 시험 결과 화면
  if (testResults) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                시험 완료!
              </h1>
              <div className="text-6xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                {Math.round(testResults.test.score_percentage || 0)}점
              </div>
              <p className="text-gray-600 dark:text-gray-400">
                {testResults.test.correct_answers}개 / {testResults.test.total_questions}개 정답
              </p>
            </div>

            <div className="space-y-6">
              {/* BUG-SECTION5-002 FIX: 모든 문제 표시 (답변 여부와 관계없이) */}
              {testResults.test.questions?.map((question: any, index: number) => {
                // 해당 문제에 대한 답변 찾기
                const answer = testResults.answers?.find(
                  (a: any) => a.question.id === question.id
                );

                return (
                  <div
                    key={question.id}
                    className={`p-6 rounded-lg border ${
                      !answer
                        ? 'bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-600'
                        : answer.is_correct
                        ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700'
                        : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                        문제 {index + 1}: {question.content_title}
                      </h3>
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${
                          !answer
                            ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                            : answer.is_correct
                            ? 'bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200'
                            : 'bg-red-100 dark:bg-red-800 text-red-800 dark:text-red-200'
                        }`}
                      >
                        {!answer ? '미답변' : answer.is_correct ? '정답' : '오답'}
                      </span>
                    </div>

                    <p className="text-gray-700 dark:text-gray-300 mb-4 whitespace-pre-wrap">
                      {renderTextWithCode(question.question_text)}
                    </p>

                    {answer ? (
                      <>
                        <div className="grid md:grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                              내 답변:
                            </p>
                            <p className="text-gray-900 dark:text-gray-100">
                              {answer.user_answer}
                            </p>
                          </div>

                          {!answer.is_correct && (
                            <div>
                              <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                                정답:
                              </p>
                              <p className="text-gray-900 dark:text-gray-100">
                                {question.correct_answer}
                              </p>
                            </div>
                          )}
                        </div>

                        {question.explanation && (
                          <div className="mt-4 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                              해설:
                            </p>
                            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {renderTextWithCode(question.explanation)}
                            </p>
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        <p className="text-gray-600 dark:text-gray-400">
                          이 문제는 답변하지 않았습니다.
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                          정답: {question.correct_answer}
                        </p>
                        {question.explanation && (
                          <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                            <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
                              해설:
                            </p>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {renderTextWithCode(question.explanation)}
                            </p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="mt-8 text-center">
              <button
                onClick={resetView}
                className="bg-blue-600 dark:bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
              >
                시험 목록으로 돌아가기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 시험 진행 화면
  if (currentTest && currentTest.questions && currentTest.questions.length > 0) {
    const currentQuestion = currentTest.questions[currentQuestionIndex];
    const isLastQuestion = currentQuestionIndex === currentTest.questions.length - 1;

    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-3xl mx-auto px-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-8">
            {/* 진행 상황 */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {currentTest.title}
                </h1>
                <div className="text-right">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {currentQuestionIndex + 1} / {currentTest.questions.length}
                  </div>
                  <div className="text-xs mt-1">
                    <span className="text-blue-600 dark:text-blue-400 font-medium">
                      답변: {Object.keys(answers).length}/{currentTest.questions.length}
                    </span>
                    {Object.keys(answers).length < currentTest.questions.length && (
                      <span className="ml-2 text-red-500">
                        (미답변 {currentTest.questions.length - Object.keys(answers).length}개)
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${((currentQuestionIndex + 1) / currentTest.questions.length) * 100}%`
                  }}
                />
              </div>
            </div>

            {/* 에러 메시지 표시 */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
                <p className="text-red-800 dark:text-red-200">{error}</p>
              </div>
            )}

            {/* 문제 */}
            <div className="mb-8">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  문제 {currentQuestionIndex + 1}
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {renderTextWithCode(currentQuestion.question_text)}
                </p>

                {currentQuestion.content && (
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                      관련 콘텐츠: {currentQuestion.content.title}
                    </p>
                  </div>
                )}
              </div>

              {/* 답변 입력 */}
              <div className="space-y-4">
                {currentQuestion.question_type === 'true_false' ? (
                  <div className="flex space-x-4">
                    {['O', 'X'].map((option) => (
                      <button
                        key={option}
                        onClick={() => {
                          const answer = option;
                          setAnswers(prev => ({ ...prev, [currentQuestion.id]: answer }));
                          submitAnswer(currentQuestion.id, answer);
                        }}
                        className={`flex-1 py-3 px-6 rounded-lg border-2 transition-all ${
                          answers[currentQuestion.id] === option
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-500'
                        }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {currentQuestion.choices?.map((choice, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          setAnswers(prev => ({ ...prev, [currentQuestion.id]: choice }));
                          submitAnswer(currentQuestion.id, choice);
                        }}
                        className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                          answers[currentQuestion.id] === choice
                            ? 'bg-blue-600 border-blue-600 text-white'
                            : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-500'
                        }`}
                      >
                        {index + 1}. {choice}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 네비게이션 */}
            <div className="flex justify-between">
              <button
                onClick={prevQuestion}
                disabled={currentQuestionIndex === 0}
                className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                이전 문제
              </button>

              {isLastQuestion ? (
                <button
                  onClick={completeTest}
                  disabled={isLoading}
                  className="px-6 py-3 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50 transition-colors"
                >
                  {isLoading ? '완료 중...' : '시험 완료'}
                </button>
              ) : (
                <button
                  onClick={nextQuestion}
                  className="px-6 py-3 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
                >
                  다음 문제
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 시험 목록 화면
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
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

        {/* 새 시험 생성 */}
        <div className="mb-8">
          <button
            onClick={openCategorySelector}
            disabled={isLoading}
            className="bg-blue-600 dark:bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
          >
            {isLoading ? '생성 중...' : '새 주간 시험 생성'}
          </button>
        </div>

        {/* 카테고리 선택 모달 */}
        {showCategorySelector && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                카테고리 선택
              </h3>

              <div className="space-y-3 mb-6 max-h-60 overflow-y-auto">
                {categories.map((category) => (
                  <label key={category.id} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedCategoryIds.includes(category.id)}
                      onChange={() => handleCategoryToggle(category.id)}
                      className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-gray-700 dark:text-gray-300">
                      {category.name}
                    </span>
                  </label>
                ))}
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg">
                  <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
                </div>
              )}

              <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                {selectedCategoryIds.length === 0
                  ? "카테고리를 선택하세요. 선택된 카테고리에서 200자 이상 콘텐츠 10개가 필요합니다."
                  : `선택된 카테고리에서 200자 이상 콘텐츠 10개가 필요합니다.`
                }
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => setShowCategorySelector(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={createNewTest}
                  disabled={isLoading || selectedCategoryIds.length === 0}
                  className="flex-1 px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
                >
                  {isLoading ? '생성 중...' : '시험 생성'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 시험 목록 */}
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
            tests && tests.map((test) => (
              <div
                key={test.id}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                      {test.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      {test.start_date} ~ {test.end_date}
                    </p>

                    <div className="flex items-center space-x-4 text-sm">
                      <span
                        className={`px-3 py-1 rounded-full font-medium ${
                          test.status === 'completed'
                            ? 'bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200'
                            : test.status === 'in_progress'
                            ? 'bg-yellow-100 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
                            : test.status === 'preparing'
                            ? 'bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200'
                            : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
                        }`}
                      >
                        {test.status === 'completed' ? '완료' :
                         test.status === 'in_progress' ? '진행중' :
                         test.status === 'preparing' ? '준비중' : '대기중'}
                      </span>

                      <span className="text-gray-600 dark:text-gray-400">
                        {test.total_questions}문제
                      </span>

                      {test.score_percentage !== null && test.score_percentage !== undefined && (
                        <span className="text-gray-600 dark:text-gray-400">
                          점수: {Math.round(test.score_percentage)}점
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    {test.status === 'preparing' && (
                      <div className="bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 px-4 py-2 rounded-lg text-center">
                        문제 생성 중...
                      </div>
                    )}

                    {test.status === 'pending' && (
                      <button
                        onClick={() => startTest(test.id)}
                        disabled={isLoading}
                        className="bg-blue-600 dark:bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
                      >
                        시험 시작
                      </button>
                    )}

                    {test.status === 'in_progress' && (
                      <button
                        onClick={() => startTest(test.id)}
                        disabled={isLoading}
                        className="bg-yellow-600 dark:bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 dark:hover:bg-yellow-600 disabled:opacity-50 transition-colors"
                      >
                        시험 계속
                      </button>
                    )}

                    {test.status === 'completed' && (
                      <button
                        onClick={async () => {
                          const results = await weeklyTestAPI.getTestResults(test.id);
                          setTestResults(results);
                        }}
                        className="bg-gray-600 dark:bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
                      >
                        결과 보기
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Back to Dashboard */}
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