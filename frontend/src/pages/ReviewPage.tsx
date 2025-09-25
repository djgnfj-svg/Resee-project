import React, { useState, useCallback } from 'react';
import { useReviewLogic } from '../hooks/useReviewLogic';
import { useReviewState } from '../hooks/useReviewState';
import ReviewHeader from '../components/review/ReviewHeader';
import ReviewCard from '../components/review/ReviewCard';
import ReviewControls from '../components/review/ReviewControls';
import UpgradeModal from '../components/review/UpgradeModal';
import Toast from '../components/common/Toast';

const ReviewPage: React.FC = () => {
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
    reviewsCompleted,
    totalSchedules,
    showUpgradeModal,
    setIsFlipped,
    setShowContent,
    setShowUpgradeModal,
  } = useReviewState();

  const {
    currentReview,
    progress,
    isLoading,
    completeReviewMutation,
    handleReviewComplete,
  } = useReviewLogic(showToast);


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
            onBack={() => setShowContent(false)}
            onFlip={() => {
              setIsFlipped(prev => !prev);
              setShowContent(true);
            }}
          />

          <ReviewControls
            showContent={showContent}
            onReviewComplete={handleReviewComplete}
            isPending={completeReviewMutation.isPending}
          />
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