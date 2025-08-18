import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api, { authAPI } from '../utils/api';
import { SubscriptionTierInfo, SubscriptionUpgradeData } from '../types';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const SubscriptionPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const queryClient = useQueryClient();

  // 현재 구독 정보 조회
  const { data: currentSubscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ['current-subscription'],
    queryFn: () => api.get('/accounts/subscription/').then(res => res.data),
    enabled: !!user?.is_email_verified,
  });

  // Subscription tiers data
  const subscriptionTiers: SubscriptionTierInfo[] = [
    {
      name: 'free',
      display_name: '무료',
      max_days: 3,
      price: 0,
      features: [
        '최대 3일 복습 간격',
        '기본 통계',
        '무제한 콘텐츠 생성',
        '이메일 지원'
      ]
    },
    {
      name: 'basic',
      display_name: '베이직 (테스트 모드)',
      max_days: 90,
      price: 9900,
      features: [
        '최대 90일 복습 간격',
        '상세 통계 및 분석',
        '무제한 콘텐츠 생성',
        'AI 질문 생성 (일 30개)',
        'AI 서술형 평가',
        'AI 채팅',
        '우선 이메일 지원',
        '💳 테스트 모드로 결제 가능!'
      ],
      coming_soon: false
    },
    {
      name: 'pro',
      display_name: '프로 (테스트 모드)',
      max_days: 180,
      price: 19900,
      features: [
        '최대 180일 복습 간격 (에빙하우스 최적화)',
        '완전한 장기 기억 시스템',
        '무제한 콘텐츠 생성',
        'AI 질문 생성 (일 200개)',
        '모든 AI 기능 (빈칸채우기, 블러처리)',
        'AI 서술형 평가',
        'AI 채팅',
        '고급 카테고리 관리',
        '데이터 내보내기',
        'API 액세스',
        '전담 고객 지원',
        '💳 테스트 모드로 결제 가능!'
      ],
      coming_soon: false
    }
  ];

  // Import subscription API
  const subscriptionAPI = {
    upgradeSubscription: async (data: SubscriptionUpgradeData) => {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8000/api/accounts/subscription/upgrade/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      
      const responseData = await response.json();
      
      if (!response.ok) {
        throw new Error(responseData.error || 'Failed to upgrade subscription');
      }
      
      return responseData;
    }
  };

  // Subscription upgrade mutation
  const upgradeMutation = useMutation({
    mutationFn: (data: SubscriptionUpgradeData) => subscriptionAPI.upgradeSubscription(data),
    onSuccess: async (data) => {
      const tier = data.subscription?.tier;
      const maxDays = subscriptionTiers.find(t => t.name === tier)?.max_days || 7;
      
      toast.success(
        data.message || 
        `구독이 성공적으로 변경되었습니다! 이제 최대 ${maxDays}일까지의 밀진 복습을 확인할 수 있습니다.`
      );
      
      // Refresh user data in AuthContext to update subscription info
      await refreshUser();
      
      // Invalidate all relevant queries to refresh data immediately
      queryClient.invalidateQueries({ queryKey: ['current-subscription'] });
      queryClient.invalidateQueries({ queryKey: ['user'] });
      queryClient.invalidateQueries({ queryKey: ['contents'] });
      queryClient.invalidateQueries({ queryKey: ['todayReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['learning-calendar'] });
    },
    onError: (error: any) => {
      const errorMessage = error.message || '구독 변경에 실패했습니다.';
      toast.error(errorMessage);
    }
  });

  const handleTierChange = (tier: string) => {
    if (!user?.is_email_verified) {
      toast.error('구독을 변경하려면 먼저 이메일 인증을 완료해주세요.');
      return;
    }
    
    const currentTierIndex = getCurrentTierIndex();
    const newTierIndex = subscriptionTiers.findIndex(t => t.name === tier);
    const isDowngrade = newTierIndex < currentTierIndex;
    
    if (isDowngrade) {
      const currentMaxDays = subscriptionTiers[currentTierIndex].max_days;
      const newMaxDays = subscriptionTiers[newTierIndex].max_days;
      
      const confirmed = window.confirm(
        `정말로 ${subscriptionTiers[newTierIndex].display_name}으로 다운그레이드하시겠습니까?\n\n` +
        `다운그레이드 시 다음과 같은 제한이 적용됩니다:\n` +
        `• 복습 범위: ${currentMaxDays}일 → ${newMaxDays}일로 축소\n` +
        `• ${newMaxDays}일보다 오래된 밀린 복습은 숨겨집니다\n` +
        `• AI 기능 및 질문 생성 제한\n` +
        `• 일부 고급 기능 사용 불가\n\n` +
        `기존 데이터는 유지되지만 새로운 제한사항이 즉시 적용됩니다.`
      );
      
      if (!confirmed) {
        return;
      }
    }
    
    upgradeMutation.mutate({ tier: tier as any });
  };

  const getCurrentTierIndex = () => {
    const currentTier = currentSubscription?.tier || user?.subscription?.tier || 'free';
    return subscriptionTiers.findIndex(tier => tier.name === currentTier);
  };

  const currentTierIndex = getCurrentTierIndex();
  
  // 현재 표시할 구독 정보 (API에서 가져온 데이터 우선)
  const displaySubscription = currentSubscription || user?.subscription;

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
        {subscriptionLoading ? (
          <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-8">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-1/4 mb-2"></div>
              <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
            </div>
          </div>
        ) : displaySubscription && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                  현재 구독: {displaySubscription.tier_display}
                </h3>
                <p className="text-blue-700 dark:text-blue-300">
                  {displaySubscription.is_active ? '활성' : '비활성'} • 
                  최대 {displaySubscription.max_interval_days}일 복습 간격
                </p>
              </div>
              {displaySubscription.days_remaining && (
                <div className="text-right">
                  <p className="text-sm text-blue-600 dark:text-blue-400">
                    {displaySubscription.days_remaining}일 남음
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Subscription Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
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
                } ${tier.name === 'pro' ? 'scale-105' : ''}`}
              >
                {tier.name === 'pro' && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-yellow-500 to-orange-600 text-white px-4 py-1 rounded-full text-sm font-medium">
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
                    {tier.coming_soon ? (
                      <span className="text-4xl font-bold text-orange-600 dark:text-orange-400">
                        {tier.price}
                      </span>
                    ) : (
                      <>
                        <span className="text-4xl font-bold text-gray-900 dark:text-white">
                          ₩{tier.price.toLocaleString()}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 ml-2">
                          /월
                        </span>
                      </>
                    )}
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
                  onClick={() => tier.coming_soon ? null : handleTierChange(tier.name)}
                  disabled={isCurrent || upgradeMutation.isPending || tier.coming_soon}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-colors duration-200 ${
                    isCurrent
                      ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                      : tier.coming_soon
                      ? 'bg-orange-100 dark:bg-orange-900/20 text-orange-600 dark:text-orange-400 cursor-not-allowed border-2 border-orange-300 dark:border-orange-700'
                      : tier.name === 'pro'
                      ? 'bg-gradient-to-r from-yellow-500 to-orange-600 text-white hover:from-yellow-600 hover:to-orange-700'
                      : isDowngrade
                      ? 'bg-orange-600 text-white hover:bg-orange-700 dark:bg-orange-500 dark:hover:bg-orange-600'
                      : 'bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600'
                  } ${upgradeMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {tier.coming_soon ? (
                    '준비 중...'
                  ) : upgradeMutation.isPending ? (
                    '처리 중...'
                  ) : isCurrent ? (
                    '현재 플랜'
                  ) : isDowngrade ? (
                    `${tier.display_name}으로 다운그레이드`
                  ) : tier.price === 0 ? (
                    '무료로 변경'
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
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 shadow-md">
              <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
                💳 테스트 모드 활성화!
              </h3>
              <p className="text-green-800 dark:text-green-200">
                포트폴리오 시연을 위해 테스트 모드가 활성화되었습니다. 
                실제 결제 없이 결제 프로세스를 체험해볼 수 있습니다. 
                테스트 카드 번호 <strong>4242 4242 4242 4242</strong>를 사용하여 결제를 시도해보세요!
              </p>
            </div>
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