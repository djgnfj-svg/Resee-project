import React, { useState, useCallback } from 'react';
import { useReviewLogic } from '../hooks/useReviewLogic';
import { useReviewState } from '../hooks/useReviewState';
import ReviewHeader from '../components/review/ReviewHeader';
import ReviewCard from '../components/review/ReviewCard';
import ReviewControls from '../components/review/ReviewControls';
import UpgradeModal from '../components/review/UpgradeModal';
import Toast from '../components/common/Toast';

const ReviewPage: React.FC = () => {
  // v0.5: AI 평가용 서술형 답변 상태
  const [descriptiveAnswer, setDescriptiveAnswer] = useState<string>('');
  const [aiEvaluation, setAiEvaluation] = useState<{
    score: number;
    feedback: string;
    auto_result?: string;
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
    progress,
    isLoading,
    completeReviewMutation,
    handleReviewComplete,
    reviewsCompleted,
    totalSchedules,
    removeCurrentCard,
    moveCurrentCardToEnd,
  } = useReviewLogic(showToast, resetReviewState);

  // v0.5: 주관식 모드 - 제출 핸들러
  const [submittedAnswer, setSubmittedAnswer] = useState<string>('');

  const handleSubmitSubjective = useCallback(async () => {
    if (!currentReview || descriptiveAnswer.length < 10) return;

    setIsSubmitting(true);
    setSubmittedAnswer(descriptiveAnswer); // 제출한 답변 저장

    try {
      // 주관식은 result를 보내지 않음 (AI가 자동 판단)
      const response = await handleReviewComplete(null as any, descriptiveAnswer) as any;

      // AI 평가 결과 표시
      if (response && response.ai_evaluation) {
        setAiEvaluation(response.ai_evaluation);
        const resultText = response.ai_evaluation.auto_result === 'remembered' ? '기억함' : '모름';
        showToast(`AI 평가: ${Math.round(response.ai_evaluation.score)}점 - ${resultText}`,
                  response.ai_evaluation.auto_result === 'remembered' ? 'success' : 'warning');
      }

      // 카드 뒤집기
      setIsFlipped(true);
      setShowContent(true);
    } catch (error) {
      showToast('평가에 실패했습니다. 다시 시도해주세요.', 'error');
      setSubmittedAnswer(''); // 에러 시 초기화
    } finally {
      setIsSubmitting(false);
    }
  }, [currentReview, descriptiveAnswer, handleReviewComplete, showToast, setIsFlipped, setShowContent]);

  // 서술형 평가 - 다음으로 넘어가기
  const handleNextSubjective = useCallback(() => {
    // AI 평가 결과에 따라 카드 이동/제거
    if (aiEvaluation?.auto_result === 'remembered') {
      removeCurrentCard();  // 기억함 → 카드 제거
      showToast('잘 기억하고 있어요!', 'success');
    } else {
      moveCurrentCardToEnd();  // 모름 → 카드 맨 뒤로
      showToast('괜찮아요, 나중에 다시 시도해보세요!', 'info');
    }

    // 상태 초기화
    setAiEvaluation(null);
    setDescriptiveAnswer('');
    setSubmittedAnswer('');
  }, [aiEvaluation, removeCurrentCard, moveCurrentCardToEnd, showToast]);

  // v0.4: 객관식 모드 - 복습 완료 핸들러
  const handleReviewCompleteWithAI = useCallback(async (result: 'remembered' | 'partial' | 'forgot') => {
    // 기억 확인 모드에서는 descriptiveAnswer를 전달하지 않음
    await handleReviewComplete(result, '');
  }, [handleReviewComplete]);


  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
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
          <div className="space-y-2 text-sm text-gray-500 dark:text-gray-400">
            <p>완료된 복습: {reviewsCompleted}개</p>
            {totalSchedules > 0 && (
              <p>전체 예정: {totalSchedules}개</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <ReviewHeader
          reviewsCompleted={reviewsCompleted}
          totalSchedules={totalSchedules}
          progress={progress}
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
            descriptiveAnswer={descriptiveAnswer}
            onDescriptiveAnswerChange={setDescriptiveAnswer}
            onSubmitSubjective={handleSubmitSubjective}
            isSubmitting={isSubmitting}
            submittedAnswer={submittedAnswer}
            aiEvaluation={aiEvaluation}
          />

          {/* ReviewControls 표시 */}
          {currentReview.content.review_mode === 'objective' ? (
            <ReviewControls
              showContent={showContent}
              onReviewComplete={handleReviewCompleteWithAI}
              isPending={completeReviewMutation.isPending}
            />
          ) : (
            // 서술형 평가: AI 평가 완료 후 "다음으로" 버튼 표시
            aiEvaluation && (
              <ReviewControls
                showContent={showContent}
                onReviewComplete={handleReviewCompleteWithAI}
                isPending={false}
                isSubjectiveMode={true}
                onNext={handleNextSubjective}
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
      </div>
    </div>
  );
};

export default ReviewPage;