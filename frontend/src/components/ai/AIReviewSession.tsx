/**
 * AI Review Session Component
 * Main component that orchestrates different AI review types
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import { AIQuestionGenerator } from './AIQuestionGenerator';
import { FillBlankQuestion } from './FillBlankQuestion';
import { BlurProcessingViewer } from './BlurProcessingViewer';
import type { 
  AIQuestion
} from '../../types/ai-review';
import { Content } from '../../types';
import { useAuth } from '../../contexts/AuthContext';

interface AIReviewSessionProps {
  content: Content;
  mode?: 'generate' | 'all';
  onSessionComplete?: () => void;
}

type ReviewMode = 'generator' | 'fill_blank' | 'blur_processing';

export const AIReviewSession: React.FC<AIReviewSessionProps> = ({
  content,
  mode = 'all',
  onSessionComplete
}) => {
  const { user } = useAuth();
  const [currentMode, setCurrentMode] = useState<ReviewMode>('generator');
  const [existingQuestions, setExistingQuestions] = useState<AIQuestion[]>([]);
  const [loading, setLoading] = useState(false);

  // Check if user can access AI features
  const canUseAI = user?.subscription?.is_active && user.is_email_verified;
  const subscriptionTier = user?.subscription?.tier || 'free';

  // Load existing questions for this content
  useEffect(() => {
    const loadExistingQuestions = async () => {
      try {
        setLoading(true);
        const questions = await aiReviewAPI.getContentQuestions(content.id);
        setExistingQuestions(questions);
        
        // Questions loaded for display
      } catch (error) {
        console.error('Failed to load existing questions:', error);
      } finally {
        setLoading(false);
      }
    };

    loadExistingQuestions();
  }, [content.id]);

  const handleQuestionsGenerated = (questions: AIQuestion[]) => {
    setExistingQuestions(prev => [...prev, ...questions]);
    toast.success('새로운 AI 질문들이 준비되었습니다! 🚀');
  };

  const getModeIcon = (mode: ReviewMode) => {
    switch (mode) {
      case 'generator': return '🤖';
      case 'fill_blank': return '🧩';
      case 'blur_processing': return '🎯';
      default: return '📚';
    }
  };

  const getModeTitle = (mode: ReviewMode) => {
    switch (mode) {
      case 'generator': return 'AI 질문 생성기';
      case 'fill_blank': return '빈칸 채우기';
      case 'blur_processing': return '블러 처리 학습';
      default: return 'AI 학습';
    }
  };

  const renderModeSelector = () => {
    const modes: ReviewMode[] = ['generator', 'fill_blank', 'blur_processing']; // Removed multiple_choice and short_answer since they need evaluation
    
    // Define which modes are available per tier - simplified to generation only
    const getAvailableModes = (tier: string) => {
      switch (tier) {
        case 'basic': return ['generator'];
        case 'premium': return ['generator', 'fill_blank'];
        case 'pro': return ['generator', 'fill_blank', 'blur_processing'];
        default: return ['generator']; // Free tier
      }
    };
    
    const availableModes = getAvailableModes(subscriptionTier);
    
    return (
      <div className="mb-6 bg-white rounded-lg shadow-md p-4">
        <h3 className="text-lg font-semibold mb-3 text-gray-900">
          AI 학습 도구 선택
          <span className="ml-2 text-sm font-normal text-gray-600">
            ({subscriptionTier.toUpperCase()} 플랜)
          </span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {modes.map((mode) => {
            const isAvailable = canUseAI && availableModes.includes(mode);
            const isActive = currentMode === mode;
            
            return (
              <div key={mode} className="relative">
                <button
                  onClick={() => isAvailable && setCurrentMode(mode)}
                  disabled={!isAvailable}
                  className={`w-full p-4 rounded-lg border-2 transition-all text-center ${
                    isActive && isAvailable
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : isAvailable
                      ? 'border-gray-200 hover:border-gray-300 text-gray-600'
                      : 'border-gray-100 bg-gray-50 text-gray-400 cursor-not-allowed opacity-60'
                  }`}
                >
                  <div className="text-3xl mb-2">{getModeIcon(mode)}</div>
                  <div className="text-sm font-medium">{getModeTitle(mode)}</div>
                </button>
                {!isAvailable && canUseAI && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 rounded-lg text-white text-xs font-medium">
                    구독 업그레이드 필요
                  </div>
                )}
                {!canUseAI && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75 rounded-lg text-white text-xs font-medium">
                    구독 필요
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-blue-800 text-sm">
            💡 <strong>안내:</strong> AI 질문 생성 기능만 제공됩니다. 생성된 문제를 보고 학습하세요!
          </p>
        </div>
      </div>
    );
  };

  const renderCurrentMode = () => {
    switch (currentMode) {
      case 'generator':
        return (
          <div>
            <AIQuestionGenerator
              content={content}
              onQuestionsGenerated={handleQuestionsGenerated}
            />
            
            {/* Display generated questions in read-only format */}
            {existingQuestions.length > 0 && (
              <div className="mt-8 bg-white rounded-lg shadow-md p-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">🔍 생성된 질문들</h4>
                <div className="space-y-4">
                  {existingQuestions.map((question, index) => (
                    <div key={question.id} className="p-4 bg-gray-50 rounded-lg border-l-4 border-blue-500">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">
                          {question.question_type_display}
                        </span>
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                          문제 #{index + 1}
                        </span>
                      </div>
                      
                      <h5 className="font-medium text-gray-900 mb-2">{question.question_text}</h5>
                      
                      {question.options && (
                        <div className="mb-2">
                          <p className="text-sm text-gray-600 mb-1">선택지:</p>
                          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                            {question.options.map((option: string, idx: number) => (
                              <li key={idx}>{option}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      <details className="mt-2">
                        <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-800">정답 보기</summary>
                        <div className="mt-2 p-2 bg-green-50 rounded text-sm text-green-800">
                          <strong>정답:</strong> {question.correct_answer}
                          {question.explanation && (
                            <div className="mt-1">
                              <strong>해설:</strong> {question.explanation}
                            </div>
                          )}
                        </div>
                      </details>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'fill_blank':
        return <FillBlankQuestion content={content} numBlanks={5} />;

      case 'blur_processing':
        return <BlurProcessingViewer content={content} />;

      default:
        return <div>알 수 없는 모드입니다.</div>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mr-3"></div>
        <span className="text-gray-600">AI 학습 시스템을 준비하고 있습니다...</span>
      </div>
    );
  }

  // Show subscription upgrade prompt for free users
  if (!canUseAI) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl p-8 border border-purple-200">
          <div className="text-center">
            <div className="p-4 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
              <span className="text-3xl">🤖</span>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              AI 스마트 학습 기능
            </h2>
            
            <p className="text-gray-600 mb-6 leading-relaxed">
              AI 기반 맞춤형 학습 기능을 사용하려면 구독이 필요합니다.
              {!user?.is_email_verified && " 또한 이메일 인증도 완료해야 합니다."}
            </p>

            <div className="space-y-4">
              {!user?.is_email_verified && (
                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-yellow-800 text-sm">
                    ⚠️ 먼저 이메일 인증을 완료해주세요
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="p-4 bg-white rounded-lg border">
                  <h3 className="font-semibold text-blue-600 mb-2">베이직</h3>
                  <p className="text-gray-600">• 객관식 • 주관식</p>
                  <p className="text-gray-600">• 월 10개 질문</p>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <h3 className="font-semibold text-purple-600 mb-2">프리미엄</h3>
                  <p className="text-gray-600">• 객관식 • 주관식 • 빈칸 채우기</p>
                  <p className="text-gray-600">• 월 50개 질문</p>
                </div>
                <div className="p-4 bg-white rounded-lg border">
                  <h3 className="font-semibold text-green-600 mb-2">프로</h3>
                  <p className="text-gray-600">• 모든 AI 기능</p>
                  <p className="text-gray-600">• 월 200개 질문</p>
                </div>
              </div>

              <button 
                onClick={() => window.location.href = '/subscription'}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all"
              >
                구독 업그레이드하기
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg text-white">
            🤖
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AI 스마트 학습</h1>
          <span className="px-3 py-1 bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 text-sm rounded-full font-medium">
            AI 기반 개인 맞춤형 학습
          </span>
        </div>
        <p className="text-gray-600">
          "{content.title}" - AI가 분석한 맞춤형 학습 콘텐츠로 효율적인 학습을 경험하세요
        </p>
      </div>

      {/* Mode Selector */}
      {renderModeSelector()}

      {/* Current Mode Content */}
      {renderCurrentMode()}

      {/* Quick Stats */}
      {existingQuestions.length > 0 && (
        <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">📊 생성된 질문 현황</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
            <div className="p-3 bg-white rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{existingQuestions.length}</div>
              <div className="text-xs text-gray-600">총 생성된 질문</div>
            </div>
            <div className="p-3 bg-white rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {existingQuestions.filter(q => q.options).length}
              </div>
              <div className="text-xs text-gray-600">객관식 질문</div>
            </div>
            <div className="p-3 bg-white rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {existingQuestions.filter(q => !q.options).length}
              </div>
              <div className="text-xs text-gray-600">주관식 질문</div>
            </div>
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
        <h4 className="font-medium text-yellow-900 mb-2">💡 AI 학습 도구 사용법</h4>
        <ul className="text-yellow-800 text-sm space-y-1">
          <li>• <strong>질문 생성기:</strong> 원하는 유형과 난이도로 맞춤형 문제 생성</li>
          <li>• <strong>빈칸 채우기:</strong> 핵심 용어 학습에 효과적인 대화형 도구</li>
          <li>• <strong>블러 처리:</strong> 게임처럼 재미있게 개념 학습</li>
          <li>• <strong>자가 학습:</strong> 생성된 문제와 정답을 보며 스스로 학습하세요</li>
        </ul>
      </div>
    </div>
  );
};