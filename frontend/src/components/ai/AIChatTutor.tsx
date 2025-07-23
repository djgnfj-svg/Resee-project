/**
 * AI Chat Tutor Component
 * Interactive AI tutoring for learning content
 */
import React, { useState, useRef, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { AIChatRequest, ChatMessage } from '../../types/ai-review';
import { Content } from '../../types';

interface AIChatTutorProps {
  content: Content;
}

export const AIChatTutor: React.FC<AIChatTutorProps> = ({ content }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage = currentMessage.trim();
    const messageId = Date.now().toString();
    
    // Add user message and loading response
    const newMessage: ChatMessage = {
      id: messageId,
      message: userMessage,
      response: '',
      timestamp: new Date(),
      isLoading: true
    };

    setMessages(prev => [...prev, newMessage]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const request: AIChatRequest = {
        content_id: content.id,
        message: userMessage
      };

      const response = await aiReviewAPI.chatAboutContent(request);
      
      // Update message with AI response
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, response: response.response, isLoading: false }
            : msg
        )
      );

      toast.success('AI 튜터가 답변했습니다! 🤖');
    } catch (error: any) {
      console.error('AI chat failed:', error);
      const errorMessage = error.response?.data?.error || 'AI 채팅에 실패했습니다';
      
      // Update message with error
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, response: `오류: ${errorMessage}`, isLoading: false }
            : msg
        )
      );
      
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    toast.success('채팅 기록이 삭제되었습니다');
  };

  const suggestedQuestions = [
    "이 내용의 핵심 개념이 무엇인가요?",
    "좀 더 자세히 설명해주세요",
    "실제 예시를 들어 설명해주세요",
    "이것과 관련된 다른 개념은 무엇인가요?",
    "이해하기 쉽게 요약해주세요"
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg text-white">
            🤖
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">AI 튜터</h3>
            <p className="text-sm text-gray-600">"{content.title}"에 대해 질문하세요</p>
          </div>
        </div>
        
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200 transition-colors"
          >
            채팅 삭제
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">💬</div>
            <p className="text-gray-600 mb-4">AI 튜터에게 학습 내용에 대해 질문해보세요!</p>
            
            {/* Suggested Questions */}
            <div className="text-left">
              <p className="text-sm font-medium text-gray-700 mb-2">💡 추천 질문:</p>
              <div className="space-y-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentMessage(question)}
                    className="block w-full text-left p-2 text-sm bg-blue-50 hover:bg-blue-100 rounded-lg text-blue-700 transition-colors"
                  >
                    "{question}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className="space-y-3">
              {/* User Message */}
              <div className="flex justify-end">
                <div className="max-w-[80%] bg-blue-500 text-white rounded-lg px-4 py-2">
                  <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
                  <p className="text-xs text-blue-100 mt-1">
                    {msg.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>

              {/* AI Response */}
              <div className="flex justify-start">
                <div className="max-w-[80%] bg-gray-100 rounded-lg px-4 py-2">
                  {msg.isLoading ? (
                    <div className="flex items-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-purple-600 border-t-transparent"></div>
                      <span className="text-sm text-gray-600">AI가 답변을 생성하고 있습니다...</span>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-gray-800 whitespace-pre-wrap">{msg.response}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        AI 튜터 • {msg.timestamp.toLocaleTimeString()}
                      </p>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 pt-4">
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="AI 튜터에게 질문하세요... (Enter: 전송, Shift+Enter: 줄바꿈)"
            disabled={isLoading}
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            rows={2}
          />
          <button
            onClick={handleSendMessage}
            disabled={!currentMessage.trim() || isLoading}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              !currentMessage.trim() || isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center gap-1">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                전송
              </div>
            ) : (
              '전송'
            )}
          </button>
        </div>
        
        <p className="text-xs text-gray-500 mt-2">
          💡 AI 튜터는 현재 학습 내용을 바탕으로 답변합니다. 구체적으로 질문할수록 더 정확한 답변을 받을 수 있습니다.
        </p>
      </div>
    </div>
  );
};