import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowPathIcon,
  LightBulbIcon,
  PuzzlePieceIcon,
  WrenchScrewdriverIcon,
  ChatBubbleBottomCenterTextIcon,
  ListBulletIcon,
  HandRaisedIcon,
  StarIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { apiClient } from '../utils/api';
import LoadingSpinner from './LoadingSpinner';

interface TransformedQuestion {
  transformed_question: string;
  transformed_answer: string;
  transformation_explanation: string;
  learning_benefit: string;
  difficulty_level: string;
  original_question: string;
  transformation_type: string;
}

interface QuestionTransformerProps {
  questionId: number;
  originalQuestion: string;
  onClose: () => void;
  className?: string;
}

const QuestionTransformer: React.FC<QuestionTransformerProps> = ({
  questionId,
  originalQuestion,
  onClose,
  className = ''
}) => {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState<string>('');
  const [transformedQuestion, setTransformedQuestion] = useState<TransformedQuestion | null>(null);
  const [userRating, setUserRating] = useState(0);
  const [isHelpful, setIsHelpful] = useState<boolean | null>(null);

  const transformationTypes = [
    {
      type: 'reverse',
      label: '역질문',
      description: '답을 주고 이유나 과정을 묻기',
      icon: <ArrowPathIcon className="h-5 w-5" />,
      color: 'text-blue-600 bg-blue-50 border-blue-200'
    },
    {
      type: 'practical',
      label: '실생활 적용',
      description: '실제 상황에서 활용하는 문제',
      icon: <HandRaisedIcon className="h-5 w-5" />,
      color: 'text-green-600 bg-green-50 border-green-200'
    },
    {
      type: 'comparison',
      label: '비교형',
      description: '비슷한 개념과 비교하기',
      icon: <PuzzlePieceIcon className="h-5 w-5" />,
      color: 'text-purple-600 bg-purple-50 border-purple-200'
    },
    {
      type: 'troubleshoot',
      label: '문제해결형',
      description: '문제 상황을 해결하는 방법',
      icon: <WrenchScrewdriverIcon className="h-5 w-5" />,
      color: 'text-red-600 bg-red-50 border-red-200'
    },
    {
      type: 'analogy',
      label: '비유/예시',
      description: '쉬운 비유로 이해하기',
      icon: <LightBulbIcon className="h-5 w-5" />,
      color: 'text-yellow-600 bg-yellow-50 border-yellow-200'
    },
    {
      type: 'step_by_step',
      label: '단계별 풀이',
      description: '단계를 나누어 차근차근',
      icon: <ListBulletIcon className="h-5 w-5" />,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-200'
    }
  ];

  // 문제 변형 요청
  const transformQuestionMutation = useMutation({
    mutationFn: async (transformationType: string) => {
      const response = await apiClient.post('/api/ai-review/question-transform/', {
        question_id: questionId,
        transformation_type: transformationType
      });
      return response.data;
    },
    onSuccess: (data) => {
      setTransformedQuestion(data);
      toast.success('문제가 성공적으로 변형되었습니다!');
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '문제 변형에 실패했습니다.';
      toast.error(message);
    }
  });

  // 피드백 제출
  const submitFeedbackMutation = useMutation({
    mutationFn: async ({ rating, helpful }: { rating: number; helpful: boolean }) => {
      const response = await apiClient.post('/api/ai-review/question-transform/feedback/', {
        transformation_id: transformedQuestion?.id,
        user_rating: rating,
        is_helpful: helpful
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('피드백이 저장되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['transformed-questions'] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '피드백 저장에 실패했습니다.';
      toast.error(message);
    }
  });

  const handleTransform = (type: string) => {
    setSelectedType(type);
    transformQuestionMutation.mutate(type);
  };

  const handleSubmitFeedback = () => {
    if (userRating > 0 && isHelpful !== null) {
      submitFeedbackMutation.mutate({
        rating: userRating,
        helpful: isHelpful
      });
    }
  };

  const handleTryAnother = () => {
    setTransformedQuestion(null);
    setSelectedType('');
    setUserRating(0);
    setIsHelpful(null);
  };

  return (
    <div className={`fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 ${className}`}>
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <ArrowPathIcon className="h-6 w-6 text-indigo-600 mr-2" />
              <h3 className="text-xl font-semibold text-gray-900">AI 문제 변형기</h3>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* 원본 문제 */}
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <h4 className="font-medium text-gray-900 mb-2">원본 문제</h4>
            <div className="text-gray-700">{originalQuestion}</div>
          </div>

          {!transformedQuestion ? (
            /* 변형 방식 선택 */
            <div>
              <h4 className="font-medium text-gray-900 mb-4">어떻게 변형할까요?</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {transformationTypes.map((type) => (
                  <button
                    key={type.type}
                    onClick={() => handleTransform(type.type)}
                    disabled={transformQuestionMutation.isPending}
                    className={`p-4 border-2 rounded-lg text-left hover:shadow-md transition-all disabled:opacity-50 ${type.color}`}
                  >
                    <div className="flex items-start">
                      <div className="flex-shrink-0 mr-3 mt-1">
                        {type.icon}
                      </div>
                      <div>
                        <h5 className="font-medium mb-1">{type.label}</h5>
                        <p className="text-sm opacity-80">{type.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
              
              {transformQuestionMutation.isPending && (
                <div className="mt-6 text-center">
                  <LoadingSpinner className="mx-auto mb-2" />
                  <p className="text-gray-600">AI가 문제를 변형하고 있습니다...</p>
                </div>
              )}
            </div>
          ) : (
            /* 변형된 문제 결과 */
            <div className="space-y-6">
              {/* 변형 유형 표시 */}
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {transformationTypes.find(t => t.type === selectedType)?.icon}
                  <span className="ml-2 font-medium text-gray-900">
                    {transformationTypes.find(t => t.type === selectedType)?.label}
                  </span>
                </div>
                <span className="text-sm text-gray-600">
                  난이도: {transformedQuestion.difficulty_level}
                </span>
              </div>

              {/* 변형된 문제 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-800 mb-3">변형된 문제</h4>
                <div className="text-blue-700 mb-4">{transformedQuestion.transformed_question}</div>
                <div className="text-sm text-blue-600">
                  <strong>답안:</strong> {transformedQuestion.transformed_answer}
                </div>
              </div>

              {/* 변형 설명 */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-3">변형 의도</h4>
                <div className="text-green-700">{transformedQuestion.transformation_explanation}</div>
              </div>

              {/* 학습 효과 */}
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h4 className="font-medium text-purple-800 mb-3 flex items-center">
                  <LightBulbIcon className="h-4 w-4 mr-2" />
                  학습 효과
                </h4>
                <div className="text-purple-700">{transformedQuestion.learning_benefit}</div>
              </div>

              {/* 피드백 섹션 */}
              <div className="border-t pt-6">
                <h4 className="font-medium text-gray-900 mb-4">이 변형이 도움되었나요?</h4>
                
                <div className="space-y-4">
                  {/* 별점 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      평가 (1-5점)
                    </label>
                    <div className="flex space-x-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          onClick={() => setUserRating(star)}
                          className={`p-1 rounded ${
                            star <= userRating ? 'text-yellow-500' : 'text-gray-300'
                          } hover:text-yellow-400 transition-colors`}
                        >
                          <StarIcon className="h-6 w-6" fill="currentColor" />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 도움 여부 */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      학습에 도움되었나요?
                    </label>
                    <div className="flex space-x-4">
                      <button
                        onClick={() => setIsHelpful(true)}
                        className={`px-4 py-2 rounded-lg border transition-colors ${
                          isHelpful === true
                            ? 'bg-green-600 text-white border-green-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        도움됨
                      </button>
                      <button
                        onClick={() => setIsHelpful(false)}
                        className={`px-4 py-2 rounded-lg border transition-colors ${
                          isHelpful === false
                            ? 'bg-red-600 text-white border-red-600'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        별로
                      </button>
                    </div>
                  </div>
                </div>

                {/* 버튼들 */}
                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={handleSubmitFeedback}
                    disabled={userRating === 0 || isHelpful === null || submitFeedbackMutation.isPending}
                    className="flex-1 bg-indigo-600 text-white py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors font-medium"
                  >
                    {submitFeedbackMutation.isPending ? '저장 중...' : '피드백 저장'}
                  </button>
                  <button
                    onClick={handleTryAnother}
                    className="flex-1 bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700 transition-colors font-medium"
                  >
                    다른 방식으로 변형
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default QuestionTransformer;