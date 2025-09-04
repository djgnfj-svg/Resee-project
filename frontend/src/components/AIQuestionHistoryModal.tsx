import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { XMarkIcon, ClockIcon, CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../utils/api';
import LoadingSpinner from './LoadingSpinner';
import { AIQuestion } from '../types/ai-review';

interface AIQuestionHistoryModalProps {
  onClose: () => void;
}

interface QuestionSession {
  id: string;
  content_title: string;
  created_at: string;
  questions: AIQuestion[];
  user_answers: Record<number, string>;
  score?: number;
  total_questions: number;
  correct_answers: number;
}

const AIQuestionHistoryModal: React.FC<AIQuestionHistoryModalProps> = ({ onClose }) => {
  const [selectedSession, setSelectedSession] = useState<QuestionSession | null>(null);

  // Mock data for now - replace with actual API call
  const { data: sessions, isLoading } = useQuery<QuestionSession[]>({
    queryKey: ['ai-question-history'],
    queryFn: async () => {
      // Mock response - replace with actual API call
      return [
        {
          id: '1',
          content_title: 'React Hooks 기초',
          created_at: '2024-01-15T10:30:00Z',
          questions: [],
          user_answers: {},
          total_questions: 5,
          correct_answers: 4,
          score: 80
        },
        {
          id: '2',
          content_title: 'JavaScript 비동기 처리',
          created_at: '2024-01-14T15:20:00Z',
          questions: [],
          user_answers: {},
          total_questions: 3,
          correct_answers: 2,
          score: 67
        }
      ];
    }
  });

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-blue-600 bg-blue-100';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-8">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-indigo-600 p-6 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 mr-3" />
              <div>
                <h2 className="text-2xl font-bold">AI 질문 기록</h2>
                <p className="text-purple-100 mt-1">이전에 생성한 질문들을 확인할 수 있습니다</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {!sessions || sessions.length === 0 ? (
            <div className="text-center py-12">
              <ClockIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                아직 질문 기록이 없습니다
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                AI 질문을 생성하면 이곳에 기록이 표시됩니다.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                  onClick={() => setSelectedSession(session)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {session.content_title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {formatDate(session.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <div className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                          <CheckCircleIcon className="h-4 w-4 mr-1 text-green-500" />
                          {session.correct_answers}/{session.total_questions}
                        </div>
                        {session.score !== undefined && (
                          <span className={`inline-block px-2 py-1 text-xs font-semibold rounded-full ${getScoreColor(session.score)}`}>
                            {session.score}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Session Detail Modal */}
        {selectedSession && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-60 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
              <div className="bg-indigo-600 p-4 text-white">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">{selectedSession.content_title}</h3>
                  <button
                    onClick={() => setSelectedSession(null)}
                    className="p-1 hover:bg-white/20 rounded"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <div className="mb-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">총 문제</p>
                      <p className="text-lg font-semibold">{selectedSession.total_questions}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">정답</p>
                      <p className="text-lg font-semibold text-green-600">{selectedSession.correct_answers}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">점수</p>
                      <p className="text-lg font-semibold">{selectedSession.score || 0}%</p>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                  상세한 질문 내용은 추후 업데이트 예정입니다.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIQuestionHistoryModal;