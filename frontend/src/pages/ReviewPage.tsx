import React, { useEffect } from 'react';
import { useReviewLogic } from '../hooks/useReviewLogic';
import { useReviewState } from '../hooks/useReviewState';
import ReviewHeader from '../components/review/ReviewHeader';
import ReviewCard from '../components/review/ReviewCard';
import ReviewControls from '../components/review/ReviewControls';
import ExplanationMode from '../components/review/ExplanationMode';
import UpgradeModal from '../components/review/UpgradeModal';

const ReviewPage: React.FC = () => {
  const {
    selectedCategory,
    currentReviewIndex,
    showContent,
    isFlipped,
    reviewsCompleted,
    totalSchedules,
    reviewMode,
    userExplanation,
    evaluationResult,
    isEvaluating,
    showUpgradeModal,
    showEvaluation,
    setIsFlipped,
    setShowContent,
    setUserExplanation,
    setShowUpgradeModal,
  } = useReviewState();

  const {
    reviews,
    categories,
    currentReview,
    progress,
    isLoading,
    completeReviewMutation,
    handleExplanationSubmit,
    handleExplanationReviewComplete,
    handleReviewComplete,
  } = useReviewLogic();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      switch (e.key) {
        case ' ':
          e.preventDefault();
          if (reviewMode === 'card') {
            setIsFlipped(!isFlipped);
            setShowContent(!showContent);
          }
          break;
        case '1':
          e.preventDefault();
          if (showContent && reviewMode === 'card') handleReviewComplete('forgot');
          break;
        case '2':
          e.preventDefault();
          if (showContent && reviewMode === 'card') handleReviewComplete('partial');
          break;
        case '3':
          e.preventDefault();
          if (showContent && reviewMode === 'card') handleReviewComplete('remembered');
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showContent, isFlipped, reviewMode, handleReviewComplete, setIsFlipped, setShowContent]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <ReviewHeader
        reviews={reviews}
        reviewsCompleted={reviewsCompleted}
        totalSchedules={totalSchedules}
        currentReviewIndex={currentReviewIndex}
        progress={progress}
        categories={categories}
      />

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900/25 border border-gray-200 dark:border-gray-700">
          <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">복습할 항목 없음</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {/* selectedCategory === 'all'  */}
              '오늘 복습할 콘텐츠가 없습니다.' 
              {/* : '이 카테고리에 복습할 콘텐츠가 없습니다.' */}
          </p>
        </div>
      ) : currentReview ? (
        <div className="max-w-4xl mx-auto">
          {reviewMode === 'card' ? (
            <>
              <ReviewCard
                review={currentReview}
                isFlipped={isFlipped}
                showContent={showContent}
                onFlip={() => {
                  setIsFlipped(true);
                  setShowContent(true);
                }}
                onBack={() => {
                  setIsFlipped(false);
                  setShowContent(false);
                }}
              />
              <ReviewControls
                showContent={showContent}
                onReviewComplete={handleReviewComplete}
                isPending={completeReviewMutation.isPending}
              />
            </>
          ) : (
            <ExplanationMode
              review={currentReview}
              userExplanation={userExplanation}
              setUserExplanation={setUserExplanation}
              isEvaluating={isEvaluating}
              showEvaluation={showEvaluation}
              evaluationResult={evaluationResult}
              onSubmitExplanation={handleExplanationSubmit}
              onReviewComplete={handleExplanationReviewComplete}
              isPending={completeReviewMutation.isPending}
            />
          )}
        </div>
      ) : null}

      <UpgradeModal
        show={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        onUpgrade={() => {
          setShowUpgradeModal(false);
          window.location.href = '/subscription';
        }}
      />
    </div>
  );
};

export default ReviewPage;