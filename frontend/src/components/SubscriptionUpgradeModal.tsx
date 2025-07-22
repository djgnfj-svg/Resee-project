import React, { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { useSubscription } from '../hooks/useSubscription';
import { SubscriptionTierCard } from './SubscriptionTierCard';
import { EmailVerificationBanner } from './EmailVerificationBanner';
import { useAuth } from '../contexts/AuthContext';
import { SubscriptionTier, SubscriptionUpgradeError } from '../types';

interface SubscriptionUpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SubscriptionUpgradeModal: React.FC<SubscriptionUpgradeModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { user } = useAuth();
  const {
    subscription,
    subscriptionTiers,
    isLoadingTiers,
    upgradeSubscription,
    isUpgrading,
    upgradeError,
    upgradeSuccess,
  } = useSubscription();

  const [selectedTier, setSelectedTier] = useState<SubscriptionTier | null>(null);

  if (!isOpen) return null;

  const handleTierSelect = (tier: SubscriptionTier) => {
    if (tier === subscription?.tier) return;

    setSelectedTier(tier);
    upgradeSubscription({ tier });
  };

  const getUpgradeErrorMessage = (error: any): string => {
    if (!error) return '';

    const errorData = error.response?.data as SubscriptionUpgradeError | undefined;
    
    if (errorData?.error) {
      return errorData.error;
    }
    
    if (errorData?.email_verified === false) {
      return '이메일 인증이 필요합니다. 먼저 이메일을 인증해주세요.';
    }
    
    if (errorData?.tier && Array.isArray(errorData.tier)) {
      return errorData.tier[0];
    }

    return error.userMessage || '구독 업그레이드 중 오류가 발생했습니다.';
  };

  // Close modal on successful upgrade
  React.useEffect(() => {
    if (upgradeSuccess) {
      const timer = setTimeout(() => {
        onClose();
        setSelectedTier(null);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [upgradeSuccess, onClose]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
        
        <div className="relative bg-white rounded-xl shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">구독 플랜 선택</h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6">
            <>
              {/* Email verification banner */}
              {user && !user.is_email_verified && (
                <EmailVerificationBanner />
              )}

              {/* Error message */}
              {upgradeError && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-700">
                    {getUpgradeErrorMessage(upgradeError)}
                  </div>
                </div>
              </div>
            )}

            {/* Success message */}
            {upgradeSuccess && (
              <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 bg-green-600 rounded-full flex items-center justify-center">
                    <X className="w-3 h-3 text-white" />
                  </div>
                  <div className="text-sm text-green-700 font-medium">
                    구독이 성공적으로 업그레이드되었습니다!
                  </div>
                </div>
              </div>
            )}

            {/* Loading state */}
            {isLoadingTiers ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="animate-pulse">
                    <div className="bg-gray-200 rounded-xl h-96" />
                  </div>
                ))}
              </div>
            ) : (
              /* Subscription tiers */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {subscriptionTiers?.map((tier) => (
                  <SubscriptionTierCard
                    key={tier.name}
                    tier={tier}
                    currentTier={subscription?.tier}
                    isLoading={isUpgrading && selectedTier === tier.name}
                    onSelect={handleTierSelect}
                  />
                ))}
              </div>
            )}

            {/* Additional information */}
            <div className="mt-8 bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                구독 플랜 비교
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">복습 주기</h4>
                  <ul className="space-y-1">
                    <li>• <strong>무료:</strong> 최대 7일까지</li>
                    <li>• <strong>베이직:</strong> 최대 30일까지</li>
                    <li>• <strong>프리미엄:</strong> 최대 60일까지</li>
                    <li>• <strong>프로:</strong> 최대 90일까지</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">학습 효과</h4>
                  <ul className="space-y-1">
                    <li>• 더 긴 복습 주기로 장기 기억 강화</li>
                    <li>• 망각곡선을 활용한 효율적 학습</li>
                    <li>• 개인별 맞춤 복습 스케줄</li>
                    <li>• 과학적으로 검증된 학습법</li>
                  </ul>
                </div>
              </div>
            </div>
            </>
          </div>
        </div>
      </div>
    </div>
  );
};