import React, { useState } from 'react';
import { ArrowLeft, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useSubscription } from '../hooks/useSubscription';
import { SubscriptionStatus } from '../components/SubscriptionStatus';
import { SubscriptionUpgradeModal } from '../components/SubscriptionUpgradeModal';
import { EmailVerificationBanner } from '../components/EmailVerificationBanner';
import { SubscriptionTierCard } from '../components/SubscriptionTierCard';
import { useAuth } from '../contexts/AuthContext';
import { SubscriptionTier } from '../types';

export const Subscription: React.FC = () => {
  const { user } = useAuth();
  const {
    subscription,
    subscriptionTiers,
    isLoadingSubscription,
    isLoadingTiers,
    upgradeSubscription,
    isUpgrading,
  } = useSubscription();

  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  const [selectedTier, setSelectedTier] = useState<SubscriptionTier | null>(null);

  const handleTierSelect = (tier: SubscriptionTier) => {
    if (tier === subscription?.tier) return;
    
    setSelectedTier(tier);
    upgradeSubscription({ tier });
  };

  if (isLoadingSubscription) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-48 mb-8" />
            <div className="h-32 bg-gray-200 rounded mb-8" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-96 bg-gray-200 rounded" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            to="/dashboard"
            className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <div className="flex items-center gap-3">
            <Settings className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">구독 관리</h1>
          </div>
        </div>

        {/* Email verification banner */}
        {user && !user.is_email_verified && (
          <div className="mb-8">
            <EmailVerificationBanner />
          </div>
        )}

        {/* Current subscription status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">현재 구독 상태</h2>
          
          {subscription && (
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <SubscriptionStatus className="flex-1" />
              
              {subscription.tier !== 'pro' && (
                <button
                  onClick={() => setIsUpgradeModalOpen(true)}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  업그레이드
                </button>
              )}
            </div>
          )}

          {/* Subscription details */}
          {subscription && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-1">구독 시작일</h3>
                <p className="text-lg text-gray-700">
                  {new Date(subscription.start_date).toLocaleDateString('ko-KR')}
                </p>
              </div>
              
              {subscription.end_date && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-1">구독 만료일</h3>
                  <p className="text-lg text-gray-700">
                    {new Date(subscription.end_date).toLocaleDateString('ko-KR')}
                  </p>
                </div>
              )}
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-1">상태</h3>
                <p className={`text-lg font-medium ${
                  subscription.is_expired ? 'text-red-600' : 'text-green-600'
                }`}>
                  {subscription.is_expired ? '만료됨' : '활성'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Subscription tiers */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">구독 플랜</h2>
          
          {isLoadingTiers ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="animate-pulse">
                  <div className="bg-gray-200 rounded-xl h-96" />
                </div>
              ))}
            </div>
          ) : (
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
        </div>

        {/* Benefits explanation */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            망각곡선을 활용한 과학적 학습법
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">에빙하우스 망각곡선</h3>
              <p className="text-gray-700 mb-4">
                독일의 심리학자 헤르만 에빙하우스가 발견한 망각곡선에 따르면, 
                학습한 내용은 시간이 지남에 따라 급격히 잊혀집니다.
              </p>
              <ul className="space-y-2 text-gray-700">
                <li>• 1시간 후: 56% 망각</li>
                <li>• 1일 후: 74% 망각</li>
                <li>• 1주일 후: 77% 망각</li>
                <li>• 1개월 후: 79% 망각</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">간격 반복 학습의 효과</h3>
              <p className="text-gray-700 mb-4">
                적절한 간격으로 반복 학습을 하면 장기 기억으로 전환할 수 있습니다.
                구독 플랜에 따라 더 긴 복습 주기를 활용하여 효율적으로 학습하세요.
              </p>
              <ul className="space-y-2 text-gray-700">
                <li>• <strong>무료:</strong> 단기 복습 (7일까지)</li>
                <li>• <strong>베이직:</strong> 중기 복습 (30일까지)</li>
                <li>• <strong>프리미엄:</strong> 장기 복습 (60일까지)</li>
                <li>• <strong>프로:</strong> 완전한 장기 기억 (90일까지)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Upgrade modal */}
      <SubscriptionUpgradeModal
        isOpen={isUpgradeModalOpen}
        onClose={() => setIsUpgradeModalOpen(false)}
      />
    </div>
  );
};