import { useState, useEffect, useCallback } from 'react';
import { weeklyTestAPI } from '../utils/api/exams';
import { contentAPI } from '../utils/api/content';
import { Content } from '../types';
import { logger } from '../utils/logger';
import { parseApiError } from '../utils/errorParser';

export const useExamCreation = (onTestCreated: () => void) => {
  const [showContentSelector, setShowContentSelector] = useState(false);
  const [contents, setContents] = useState<Content[]>([]);
  const [selectedContentIds, setSelectedContentIds] = useState<number[]>([]);
  const [creatingTestMessage, setCreatingTestMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    loadContents();
  }, []);

  const loadContents = async () => {
    try {
      const response = await contentAPI.getContents();
      setContents(response.results || []);
    } catch (error) {
      logger.error('Failed to load contents:', error);
    }
  };

  const openContentSelector = useCallback(() => {
    setShowContentSelector(true);
    setSelectedContentIds([]);
    setError('');
  }, []);

  const handleContentToggle = useCallback((contentId: number) => {
    setSelectedContentIds(prev => {
      if (prev.includes(contentId)) {
        return prev.filter(id => id !== contentId);
      } else {
        if (prev.length >= 10) {
          setError('최대 10개까지만 선택할 수 있습니다.');
          return prev;
        }
        setError('');
        return [...prev, contentId];
      }
    });
  }, []);

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
        logger.error('Polling error:', error);
        // 에러 발생 시 계속 시도
      }
    }

    // 타임아웃 - 에러는 발생시키지 않고 그냥 진행
    logger.warn('Test creation polling timeout');
  };

  const createNewTest = useCallback(async () => {
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
      onTestCreated();

      // 2초 후 메시지 제거
      setTimeout(() => setCreatingTestMessage(null), 2000);
    } catch (error) {
      logger.error('Failed to create test:', error);
      const errorMessage = parseApiError(error, '시험 생성에 실패했습니다.');
      setError(errorMessage);
      setCreatingTestMessage(null);
    } finally {
      setIsLoading(false);
    }
  }, [selectedContentIds, onTestCreated]);

  return {
    showContentSelector,
    contents,
    selectedContentIds,
    creatingTestMessage,
    isLoading,
    error,
    setError,
    openContentSelector,
    handleContentToggle,
    createNewTest,
    closeContentSelector: () => setShowContentSelector(false),
  };
};
