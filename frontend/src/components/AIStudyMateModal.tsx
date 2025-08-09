import React, { useState, useEffect, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  PaperAirplaneIcon,
  LightBulbIcon,
  ExclamationCircleIcon,
  AcademicCapIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import apiClient from '../utils/apiClient';
import LoadingSpinner from './LoadingSpinner';

interface StudyMateSession {
  id: number;
  session_type: 'guided_learning' | 'hint_system' | 'error_analysis' | 'concept_explanation';
  interaction_count: number;
  hints_provided: string[];
  user_level: 'beginner' | 'intermediate' | 'advanced';
  adapted_explanations: string[];
  learning_progress: Record<string, any>;
  session_duration_minutes: number;
  effectiveness_score: number | null;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  hint?: boolean;
}

interface AIStudyMateModalProps {
  isOpen: boolean;
  onClose: () => void;
  contentId: number;
  contentTitle: string;
}

const AIStudyMateModal: React.FC<AIStudyMateModalProps> = ({
  isOpen,
  onClose,
  contentId,
  contentTitle
}) => {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [sessionType, setSessionType] = useState<'guided_learning' | 'hint_system' | 'error_analysis' | 'concept_explanation'>('guided_learning');
  const [userLevel, setUserLevel] = useState<'beginner' | 'intermediate' | 'advanced'>('intermediate');
  const [currentSession, setCurrentSession] = useState<StudyMateSession | null>(null);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 세션 시작
  const startSessionMutation = useMutation({
    mutationFn: async ({ strugglePoint }: { strugglePoint: string }) => {
      const response = await apiClient.post('/api/ai-review/study-mate/', {
        content_id: contentId,
        struggle_point: strugglePoint,
        user_level: userLevel,
        session_type: sessionType
      });
      return response.data;
    },
    onSuccess: (data) => {
      setCurrentSession(data.session);
      setIsSessionActive(true);
      // AI 첫 인사 메시지 추가
      setMessages([{
        role: 'assistant',
        content: data.welcome_message || '안녕하세요! AI 스터디 메이트입니다. 어떤 부분이 어려우신가요?',
        timestamp: new Date()
      }]);
      toast.success('AI 스터디 메이트 세션이 시작되었습니다!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '세션 시작에 실패했습니다.';
      toast.error(message);
    }
  });

  // 메시지 전송
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await apiClient.post('/api/ai-review/study-mate/chat/', {
        session_id: currentSession?.id,
        message: message
      });
      return response.data;
    },
    onSuccess: (data) => {
      // AI 응답 추가
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        hint: data.is_hint
      }]);
      
      // 세션 정보 업데이트
      if (data.session_update) {
        setCurrentSession(data.session_update);
      }
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '메시지 전송에 실패했습니다.';
      toast.error(message);
    }
  });

  // 세션 종료
  const endSessionMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/ai-review/study-mate/end/', {
        session_id: currentSession?.id
      });
      return response.data;
    },
    onSuccess: () => {
      setIsSessionActive(false);
      setCurrentSession(null);
      queryClient.invalidateQueries({ queryKey: ['content', contentId] });
      toast.success('세션이 종료되었습니다.');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '세션 종료에 실패했습니다.';
      toast.error(message);
    }
  });

  // 스크롤 자동 이동
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 모달 닫기 시 정리
  useEffect(() => {
    if (!isOpen) {
      setMessages([]);
      setInputMessage('');
      setIsSessionActive(false);
      setCurrentSession(null);
    }
  }, [isOpen]);

  const handleSendMessage = () => {
    if (!inputMessage.trim() || sendMessageMutation.isPending) return;

    if (!isSessionActive) {
      // 세션 시작
      startSessionMutation.mutate({ strugglePoint: inputMessage });
    } else {
      // 메시지 전송
      setMessages(prev => [...prev, {
        role: 'user',
        content: inputMessage,
        timestamp: new Date()
      }]);
      
      sendMessageMutation.mutate(inputMessage);
    }

    setInputMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getSessionTypeLabel = (type: string) => {
    const labels = {
      'guided_learning': '가이드 학습',
      'hint_system': '힌트 시스템',
      'error_analysis': '오답 분석',
      'concept_explanation': '개념 설명'
    };
    return labels[type as keyof typeof labels] || type;
  };

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case 'guided_learning': return <AcademicCapIcon className="h-4 w-4" />;
      case 'hint_system': return <LightBulbIcon className="h-4 w-4" />;
      case 'error_analysis': return <ExclamationCircleIcon className="h-4 w-4" />;
      case 'concept_explanation': return <ChatBubbleLeftRightIcon className="h-4 w-4" />;
      default: return <ChatBubbleLeftRightIcon className="h-4 w-4" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-4xl h-[80vh] flex flex-col">
        {/* 헤더 */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 flex items-center">
                <ChatBubbleLeftRightIcon className="h-6 w-6 text-indigo-600 mr-2" />
                AI 스터디 메이트
              </h3>
              <p className="text-sm text-gray-600 mt-1">{contentTitle}</p>
            </div>
            <div className="flex items-center space-x-4">
              {/* 세션 정보 */}
              {isSessionActive && currentSession && (
                <div className="text-sm text-gray-600 flex items-center space-x-4">
                  <div className="flex items-center">
                    {getSessionTypeIcon(currentSession.session_type)}
                    <span className="ml-1">{getSessionTypeLabel(currentSession.session_type)}</span>
                  </div>
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {currentSession.session_duration_minutes}분
                  </div>
                </div>
              )}
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* 설정 (세션 시작 전에만 표시) */}
          {!isSessionActive && (
            <div className="mt-4 flex space-x-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  세션 유형
                </label>
                <select
                  value={sessionType}
                  onChange={(e) => setSessionType(e.target.value as any)}
                  className="border border-gray-300 rounded px-3 py-1 text-sm"
                >
                  <option value="guided_learning">가이드 학습</option>
                  <option value="hint_system">힌트 시스템</option>
                  <option value="error_analysis">오답 분석</option>
                  <option value="concept_explanation">개념 설명</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  수준
                </label>
                <select
                  value={userLevel}
                  onChange={(e) => setUserLevel(e.target.value as any)}
                  className="border border-gray-300 rounded px-3 py-1 text-sm"
                >
                  <option value="beginner">초급</option>
                  <option value="intermediate">중급</option>
                  <option value="advanced">고급</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* 채팅 영역 */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 && !isSessionActive ? (
            <div className="text-center text-gray-500 mt-8">
              <ChatBubbleLeftRightIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p>어떤 부분이 어려우신지 말씀해주세요.</p>
              <p className="text-sm">AI가 맞춤형 도움을 제공할게요!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-indigo-600 text-white'
                        : message.hint
                        ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    {message.hint && (
                      <div className="flex items-center text-yellow-600 text-xs mb-1">
                        <LightBulbIcon className="h-3 w-3 mr-1" />
                        힌트
                      </div>
                    )}
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className={`text-xs mt-1 ${
                      message.role === 'user' ? 'text-indigo-200' : 'text-gray-500'
                    }`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              {(startSessionMutation.isPending || sendMessageMutation.isPending) && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-lg flex items-center">
                    <LoadingSpinner className="w-4 h-4 mr-2" />
                    <span className="text-sm">AI가 생각중...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 입력 영역 */}
        <div className="p-6 border-t border-gray-200">
          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isSessionActive ? "메시지를 입력하세요..." : "어떤 부분이 어려운지 설명해주세요..."}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none focus:ring-indigo-500 focus:border-indigo-500"
                rows={2}
              />
            </div>
            <div className="flex flex-col space-y-2">
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || startSessionMutation.isPending || sendMessageMutation.isPending}
                className="bg-indigo-600 text-white p-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
              {isSessionActive && (
                <button
                  onClick={() => endSessionMutation.mutate()}
                  disabled={endSessionMutation.isPending}
                  className="bg-gray-600 text-white p-2 rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors text-xs"
                >
                  종료
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIStudyMateModal;