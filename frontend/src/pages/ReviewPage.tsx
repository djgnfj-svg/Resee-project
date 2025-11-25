import React, { useState, useCallback, useEffect } from 'react';
import { useReviewLogic } from '../hooks/useReviewLogic';
import { useReviewState } from '../hooks/useReviewState';
import ReviewHeader from '../components/review/ReviewHeader';
import ReviewCard from '../components/review/ReviewCard';
import ReviewControls from '../components/review/ReviewControls';
import UpgradeModal from '../components/review/UpgradeModal';
import Toast from '../components/common/Toast';

const ReviewPage: React.FC = () => {
  useEffect(() => {
    document.title = '복습 - Resee';
  }, []);

  // Descriptive mode: 제목 보고 내용 작성
  const [descriptiveAnswer, setDescriptiveAnswer] = useState<string>('');
  // Multiple choice mode: 내용 보고 제목 선택
  const [selectedChoice, setSelectedChoice] = useState<string>('');
  // AI evaluation result
  const [aiEvaluation, setAiEvaluation] = useState<{
    score: number;
    feedback: string;
    auto_result?: string;
    is_correct?: boolean;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Toast state
  const [toast, setToast] = useState<{
    message: string;
    type: 'success' | 'info' | 'warning' | 'error';
    isVisible: boolean;
  }>({
    message: '',
    type: 'success',
    isVisible: false,
  });

  const showToast = useCallback((message: string, type: 'success' | 'info' | 'warning' | 'error') => {
    setToast({
      message,
      type,
      isVisible: true,
    });
  }, []);

  const hideToast = useCallback(() => {
    setToast(prev => ({
      ...prev,
      isVisible: false,
    }));
  }, []);

  const {
    showContent,
    isFlipped,
    showUpgradeModal,
    setIsFlipped,
    setShowContent,
    setShowUpgradeModal,
    resetReviewState,
  } = useReviewState();

  const {
    currentReview,
    isLoading,
    completeReviewMutation,
    handleReviewComplete,
    setReviewsCompleted,
    remainingReviews,
    removeCurrentCard,
    moveCurrentCardToEnd,
  } = useReviewLogic(showToast, resetReviewState);

  // Track submitted answers for display
  const [submittedAnswer, setSubmittedAnswer] = useState<string>('');

  // 1. Descriptive Mode: 제목 보고 내용 작성 → AI 평가
  const handleSubmitDescriptive = useCallback(async () => {
    if (!currentReview || descriptiveAnswer.length < 10) return;

    setIsSubmitting(true);
    setSubmittedAnswer(descriptiveAnswer);

    try {
      const response = await handleReviewComplete(null as any, descriptiveAnswer, '') as any;

      if (response && response.ai_evaluation) {
        setAiEvaluation(response.ai_evaluation);
        const resultText = response.ai_evaluation.auto_result === 'remembered' ? '기억함' : '모름';
        showToast(`AI 평가: ${Math.round(response.ai_evaluation.score)}점 - ${resultText}`,
                  response.ai_evaluation.auto_result === 'remembered' ? 'success' : 'warning');
      }

      setIsFlipped(true);
      setShowContent(true);
    } catch (error) {
      showToast('평가에 실패했습니다. 다시 시도해주세요.', 'error');
      setSubmittedAnswer('');
    } finally {
      setIsSubmitting(false);
    }
  }, [currentReview, descriptiveAnswer, handleReviewComplete, showToast, setIsFlipped, setShowContent]);

  // 2. Multiple Choice Mode: 내용 보고 제목 선택
  const handleSubmitMultipleChoice = useCallback(async () => {
    if (!currentReview || !selectedChoice) return;

    setIsSubmitting(true);

    try {
      const response = await handleReviewComplete(null as any, '', selectedChoice) as any;

      // Use Backend's authoritative ai_evaluation
      if (response && response.ai_evaluation) {
        setAiEvaluation(response.ai_evaluation);
        const isCorrect = response.ai_evaluation.score === 100;
        showToast(response.ai_evaluation.feedback, isCorrect ? 'success' : 'error');
      }

      setIsFlipped(true);
      setShowContent(true);
    } catch (error) {
      showToast('제출에 실패했습니다. 다시 시도해주세요.', 'error');
    } finally {
      setIsSubmitting(false);
    }
  }, [currentReview, selectedChoice, handleReviewComplete, showToast, setIsFlipped, setShowContent]);


  // 다음으로 넘어가기 (AI 평가 후)
  const handleNextAfterEvaluation = useCallback(() => {
    if (aiEvaluation?.auto_result === 'remembered' || aiEvaluation?.is_correct) {
      setReviewsCompleted(prev => prev + 1);
      removeCurrentCard();
      showToast('잘 기억하고 있어요!', 'success');
    } else {
      moveCurrentCardToEnd();
      showToast('괜찮아요, 나중에 다시 시도해보세요!', 'info');
    }

    // 상태 초기화
    setAiEvaluation(null);
    setDescriptiveAnswer('');
    setSelectedChoice('');
    setSubmittedAnswer('');
  }, [aiEvaluation, removeCurrentCard, moveCurrentCardToEnd, showToast, setReviewsCompleted]);

  // 객관식/서술형 아닌 모드 - 복습 완료 핸들러
  const handleReviewCompleteWithAI = useCallback(async (result: 'remembered' | 'partial' | 'forgot') => {
    // 기억 확인 모드에서는 AI 필드를 전달하지 않음
    await handleReviewComplete(result, '', '');
  }, [handleReviewComplete]);


  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-gray-200 dark:border-gray-700 border-t-indigo-600 dark:border-t-indigo-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">오늘의 복습을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (!currentReview) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">🎉</div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            복습 완료!
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            오늘 예정된 모든 복습을 완료했습니다!
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <ReviewHeader
        remainingReviews={remainingReviews}
      />

      <div className="space-y-6">
          <ReviewCard
            review={currentReview}
            showContent={showContent}
            isFlipped={isFlipped}
            onFlip={() => {
              setIsFlipped(prev => !prev);
              setShowContent(true);
            }}
            // Descriptive mode
            descriptiveAnswer={descriptiveAnswer}
            onDescriptiveAnswerChange={setDescriptiveAnswer}
            onSubmitDescriptive={handleSubmitDescriptive}
            // Multiple choice mode
            selectedChoice={selectedChoice}
            onSelectChoice={setSelectedChoice}
            onSubmitMultipleChoice={handleSubmitMultipleChoice}
            // Common
            isSubmitting={isSubmitting}
            submittedAnswer={submittedAnswer}
            aiEvaluation={aiEvaluation}
          />

          {/* ReviewControls 표시 */}
          {currentReview.content.review_mode === 'objective' ? (
            // Objective mode: 사용자 선택 (remembered/partial/forgot)
            <ReviewControls
              showContent={showContent}
              onReviewComplete={handleReviewCompleteWithAI}
              isPending={completeReviewMutation.isPending}
            />
          ) : (
            // AI mode (descriptive, multiple_choice): AI 평가 완료 후 "다음으로" 버튼
            aiEvaluation && (
              <ReviewControls
                showContent={showContent}
                onReviewComplete={handleReviewCompleteWithAI}
                isPending={false}
                isAIMode={true}
                onNext={handleNextAfterEvaluation}
              />
            )
          )}
        </div>

        <UpgradeModal
          show={showUpgradeModal}
          onClose={() => setShowUpgradeModal(false)}
          onUpgrade={() => window.location.href = '/subscription'}
        />

      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
    </>
  );
};

export default ReviewPage;