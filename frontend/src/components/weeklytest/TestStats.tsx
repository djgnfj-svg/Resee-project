import React from 'react';
import { BookOpenIcon, ClockIcon, PlayIcon } from '@heroicons/react/24/outline';

interface WeeklyTest {
  id: number;
  week_start_date: string;
  week_end_date: string;
  total_questions: number;
  time_limit_minutes: number;
  difficulty_distribution: Record<string, number>;
  content_coverage: number[];
  completion_rate: number;
  status: 'draft' | 'ready' | 'in_progress' | 'completed' | 'expired';
}

interface TestStatsProps {
  currentTest: WeeklyTest;
  onStartTest: (testId: number) => void;
  isStarting: boolean;
}

const TestStats: React.FC<TestStatsProps> = ({ currentTest, onStartTest, isStarting }) => {
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
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-8 border-l-4 border-indigo-500 dark:border-indigo-400">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <BookOpenIcon className="h-6 w-6 text-indigo-600 dark:text-indigo-400 mr-2" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {formatDate(currentTest.week_start_date)} - {formatDate(currentTest.week_end_date)} 주간 시험
          </h2>
          {getStatusBadge(currentTest.status)}
        </div>
        {currentTest.status === 'ready' && (
          <button
            onClick={() => onStartTest(currentTest.id)}
            disabled={isStarting}
            className="bg-green-600 dark:bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-colors font-medium flex items-center disabled:opacity-50"
          >
            <PlayIcon className="h-4 w-4 mr-2" />
            {isStarting ? '시작 중...' : '시험 시작'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{currentTest.total_questions}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">총 문제 수</div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
            <ClockIcon className="h-5 w-5 mr-1" />
            {currentTest.time_limit_minutes === 0 ? '무제한' : `${currentTest.time_limit_minutes}분`}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">제한 시간</div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{currentTest.content_coverage.length}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">출제 콘텐츠</div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
          <div className="text-2xl font-bold text-indigo-600 dark:text-indigo-400">
            {currentTest.completion_rate.toFixed(0)}%
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">진행률</div>
        </div>
      </div>

      {/* 난이도 분포 */}
      <div className="mt-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">난이도 분포</h3>
        <div className="flex space-x-4">
          {Object.entries(currentTest.difficulty_distribution as Record<string, number>).map(([level, count]) => (
            <div key={level} className="flex items-center">
              <div className={`w-3 h-3 rounded mr-2 ${
                level === 'easy' ? 'bg-green-400' :
                level === 'medium' ? 'bg-yellow-400' : 'bg-red-400'
              }`} />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {level === 'easy' ? '쉬움' : level === 'medium' ? '보통' : '어려움'}: {count}문항
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TestStats;