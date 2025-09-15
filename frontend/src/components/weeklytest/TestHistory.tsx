import React from 'react';
import { ChartBarIcon, AcademicCapIcon } from '@heroicons/react/24/outline';

interface WeeklyTest {
  id: number;
  week_start_date: string;
  week_end_date: string;
  total_questions: number;
  completed_questions: number;
  score: number | null;
  accuracy_rate: number;
  time_spent_minutes: number;
  improvement_from_last_week: number | null;
  status: 'draft' | 'ready' | 'in_progress' | 'completed' | 'expired';
}

interface TestHistoryProps {
  completedTests: WeeklyTest[];
}

const TestHistory: React.FC<TestHistoryProps> = ({ completedTests }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status: WeeklyTest['status']) => {
    const badges = {
      draft: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
      ready: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200',
      completed: 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200',
      expired: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200'
    };

    const labels = {
      draft: '준비중',
      ready: '시작가능',
      in_progress: '진행중',
      completed: '완료',
      expired: '만료'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badges[status]}`}>
        {labels[status]}
      </span>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <div className="flex items-center mb-6">
        <ChartBarIcon className="h-6 w-6 text-gray-600 dark:text-gray-400 mr-2" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">시험 기록</h2>
      </div>

      {completedTests.length === 0 ? (
        <div className="text-center py-12">
          <AcademicCapIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">완료된 시험이 없습니다</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            첫 번째 주간 시험을 만들어보세요!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {completedTests.map((test: WeeklyTest) => (
            <div key={test.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium text-gray-900 dark:text-gray-100">
                  {formatDate(test.week_start_date)} - {formatDate(test.week_end_date)}
                </div>
                <div className="flex items-center space-x-4">
                  <span className={`text-lg font-bold ${
                    test.score && test.score >= 80 ? 'text-green-600 dark:text-green-400' :
                    test.score && test.score >= 60 ? 'text-yellow-600 dark:text-yellow-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    {test.score?.toFixed(0)}점
                  </span>
                  {getStatusBadge(test.status)}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400">
                <div>
                  정답률: <span className="font-medium">{test.accuracy_rate.toFixed(0)}%</span>
                </div>
                <div>
                  소요시간: <span className="font-medium">{test.time_spent_minutes}분</span>
                </div>
                <div>
                  문제수: <span className="font-medium">{test.completed_questions}/{test.total_questions}</span>
                </div>
              </div>

              {test.improvement_from_last_week !== null && (
                <div className="mt-2 text-sm">
                  <span className={`font-medium ${
                    test.improvement_from_last_week > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}>
                    지난 주 대비 {test.improvement_from_last_week > 0 ? '+' : ''}{test.improvement_from_last_week.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TestHistory;