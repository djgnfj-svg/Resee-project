import { useState, useEffect } from 'react';
import { weeklyTestAPI, WeeklyTest } from '../utils/api/exams';
import { logger } from '../utils/logger';

export const useExamList = () => {
  const [tests, setTests] = useState<WeeklyTest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const loadTests = async () => {
    try {
      setIsLoading(true);
      const testList = await weeklyTestAPI.getExams();
      setTests(Array.isArray(testList) ? testList : []);
    } catch (error) {
      logger.error('Failed to load tests:', error);
      setError('시험 목록을 불러오는데 실패했습니다.');
      setTests([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTests();
  }, []);

  return {
    tests,
    isLoading,
    error,
    setError,
    loadTests,
  };
};
