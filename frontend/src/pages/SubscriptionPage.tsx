import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useMutation, useQuery } from '@tanstack/react-query';
import { authAPI } from '../utils/api';
import { SubscriptionTierInfo, SubscriptionUpgradeData } from '../types';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const SubscriptionPage: React.FC = () => {
  const { user } = useAuth();

  // Subscription tiers data
  const subscriptionTiers: SubscriptionTierInfo[] = [
    {
      name: 'free',
      display_name: '무료',
      max_days: 7,
      price: 0,
      features: [
        '최대 7일 복습 간격',
        '기본 통계',
        '무제한 콘텐츠 생성',
        '이메일 지원'
      ]
    },
    {
      name: 'basic',
      display_name: '베이직',
      max_days: 14,
      price: 5900,
      features: [
        '최대 14일 복습 간격',
        '상세 통계 및 분석',
        '무제한 콘텐츠 생성',
        'AI 질문 생성 (월 50개)',
        '우선 이메일 지원'
      ]
    },
    {
      name: 'premium',
      display_name: '프리미엄',
      max_days: 30,
      price: 9900,
      features: [
        '최대 30일 복습 간격',
        '고급 통계 및 인사이트',
        '무제한 콘텐츠 생성',
        'AI 질문 생성 (월 200개)',
        '카테고리 관리',
        '데이터 내보내기',
        '24시간 이메일 지원'
      ]
    },
    {
      name: 'pro',
      display_name: '프로',
      max_days: 90,
      price: 19900,
      features: [
        '최대 90일 복습 간격',
        '전문가급 분석 도구',
        '무제한 콘텐츠 생성',
        'AI 질문 생성 (무제한)',
        '고급 카테고리 관리',
        '데이터 내보내기',
        'API 액세스',
        '전담 고객 지원'
      ]
    }
  ];

  // Import subscription API
  const subscriptionAPI = {
    upgradeSubscription: async (data: SubscriptionUpgradeData) => {
      const response = await fetch('/api/accounts/subscription/upgrade/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed to upgrade subscription');
      return response.json();
    }
  };

  // Subscription upgrade mutation
  const upgradeMutation = useMutation({
    mutationFn: (data: SubscriptionUpgradeData) => subscriptionAPI.upgradeSubscription(data),
    onSuccess: () => {
      toast.success('구독이 성공적으로 업그레이드되었습니다!');
      window.location.reload(); // Refresh to update user data
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.error || '구독 업그레이드에 실패했습니다.';
      toast.error(errorMessage);
    }
  });

  const handleUpgrade = (tier: string) => {
    if (!user?.is_email_verified) {
      toast.error('구독을 업그레이드하려면 먼저 이메일 인증을 완료해주세요.');
      return;
    }
    
    upgradeMutation.mutate({ tier: tier as any });
  };

  const getCurrentTierIndex = () => {
    const currentTier = user?.subscription?.tier || 'free';
    return subscriptionTiers.findIndex(tier => tier.name === currentTier);
  };

  const currentTierIndex = getCurrentTierIndex();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            구독 플랜
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            효과적인 학습을 위한 최적의 플랜을 선택하세요. 언제든지 업그레이드하거나 취소할 수 있습니다.
          </p>
        </div>

        {/* Current Subscription Status */}
        {user?.subscription && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                  현재 구독: {user.subscription.tier_display}
                </h3>
                <p className="text-blue-700 dark:text-blue-300">
                  {user.subscription.is_active ? '활성' : '비활성'} • 
                  최대 {user.subscription.max_interval_days}일 복습 간격
                </p>
              </div>
              {user.subscription.days_remaining && (
                <div className="text-right">
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    {user.subscription.days_remaining}일 남음
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Subscription Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {subscriptionTiers.map((tier, index) => {
            const isCurrent = currentTierIndex === index;
            const isUpgrade = index > currentTierIndex;
            const isDowngrade = index < currentTierIndex;

            return (
              <div
                key={tier.name}
                className={`relative rounded-2xl border-2 p-8 shadow-lg transition-all duration-200 ${
                  isCurrent
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-600'
                } ${tier.name === 'premium' ? 'scale-105' : ''}`}
              >
                {tier.name === 'premium' && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                      인기
                    </span>
                  </div>
                )}

                {isCurrent && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-green-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                      현재 플랜
                    </span>
                  </div>
                )}

                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    {tier.display_name}
                  </h3>
                  <div className="mb-4">
                    <span className="text-4xl font-bold text-gray-900 dark:text-white">
                      ₩{tier.price.toLocaleString()}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400 ml-2">
                      /월
                    </span>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400">
                    최대 {tier.max_days}일 복습 간격
                  </p>
                </div>

                <ul className="space-y-4 mb-8">
                  {tier.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <CheckIcon className="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300">
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleUpgrade(tier.name)}
                  disabled={isCurrent || isDowngrade || upgradeMutation.isPending}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-colors duration-200 ${
                    isCurrent
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                      : isDowngrade
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                      : tier.name === 'premium'
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
                      : 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
                  } ${upgradeMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {upgradeMutation.isPending ? (
                    '처리 중...'
                  ) : isCurrent ? (
                    '현재 플랜'
                  ) : isDowngrade ? (
                    '다운그레이드 불가'
                  ) : tier.price === 0 ? (
                    '무료로 시작'
                  ) : (
                    `${tier.display_name}으로 업그레이드`
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="mt-16 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white text-center mb-8">
            자주 묻는 질문
          </h2>
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                언제든지 구독을 취소할 수 있나요?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                네, 언제든지 구독을 취소할 수 있습니다. 취소 후에도 현재 결제 기간이 끝날 때까지는 모든 기능을 이용할 수 있습니다.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                복습 간격이란 무엇인가요?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                복습 간격은 학습한 내용을 다시 복습하기까지의 최대 시간입니다. 더 긴 간격은 장기 기억 형성에 더 효과적입니다.
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-md">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                플랜을 변경하면 데이터는 어떻게 되나요?
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                모든 학습 데이터와 콘텐츠는 플랜 변경과 관계없이 안전하게 보관됩니다. 업그레이드 시 즉시 새로운 기능을 이용할 수 있습니다.
              </p>
            </div>
          </div>
        </div>

        {/* Contact Section */}
        <div className="mt-16 text-center">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-8">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              더 궁금한 점이 있으신가요?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              언제든지 문의해 주세요. 최선을 다해 도와드리겠습니다.
            </p>
            <a
              href="mailto:support@resee.com"
              className="inline-flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200"
            >
              문의하기
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;