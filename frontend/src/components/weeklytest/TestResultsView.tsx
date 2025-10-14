import React from 'react';
import { renderTextWithCode } from '../../utils/textFormatters';

interface TestResultsViewProps {
  testResults: any;
  onReset: () => void;
}

const TestResultsView: React.FC<TestResultsViewProps> = ({ testResults, onReset }) => {
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
            {testResults.test.questions?.map((question: any, index: number) => {
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
              onClick={onReset}
              className="bg-blue-600 dark:bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
            >
              시험 목록으로 돌아가기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestResultsView;
