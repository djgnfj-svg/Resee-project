import React from 'react';
import { WeeklyTest } from '../../utils/api/weeklyTest';

interface TestListItemProps {
  test: WeeklyTest;
  isLoading: boolean;
  onStart: (testId: number) => void;
  onViewResults: (testId: number) => void;
}

const TestListItem: React.FC<TestListItemProps> = ({
  test,
  isLoading,
  onStart,
  onViewResults,
}) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 dark:bg-green-800 text-green-800 dark:text-green-200';
      case 'in_progress':
        return 'bg-yellow-100 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200';
      case 'preparing':
        return 'bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '완료';
      case 'in_progress': return '진행중';
      case 'preparing': return '준비중';
      default: return '대기중';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {test.title}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {test.start_date} ~ {test.end_date}
          </p>

          <div className="flex items-center space-x-4 text-sm">
            <span className={`px-3 py-1 rounded-full font-medium ${getStatusColor(test.status)}`}>
              {getStatusText(test.status)}
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
              onClick={() => onStart(test.id)}
              disabled={isLoading}
              className="bg-blue-600 dark:bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 transition-colors"
            >
              시험 시작
            </button>
          )}

          {test.status === 'in_progress' && (
            <button
              onClick={() => onStart(test.id)}
              disabled={isLoading}
              className="bg-yellow-600 dark:bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 dark:hover:bg-yellow-600 disabled:opacity-50 transition-colors"
            >
              시험 계속
            </button>
          )}

          {test.status === 'completed' && (
            <button
              onClick={() => onViewResults(test.id)}
              className="bg-gray-600 dark:bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
            >
              결과 보기
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TestListItem;
