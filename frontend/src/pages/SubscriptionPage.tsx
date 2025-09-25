import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { SubscriptionTierInfo, SubscriptionUpgradeData, SubscriptionTier } from '../types';
import { toast } from 'react-hot-toast';
import TierCard from '../components/subscription/TierCard';
import EmailSignup from '../components/subscription/EmailSignup';

const SubscriptionPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const queryClient = useQueryClient();
  const [billingCycle] = useState<'monthly' | 'yearly'>('monthly');

  // Get pricing based on billing cycle
  const getPrice = (monthlyPrice: number) => {
    if (billingCycle === 'yearly') {
      return Math.floor(monthlyPrice * 12 * 0.8); // 20% discount for yearly
    }
    return monthlyPrice;
  };

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
      display_name: '베이직',
      max_days: 90,
      price: getPrice(9900),
      features: [
        '최대 90일 복습 간격',
        '상세 통계 및 분석',
        '무제한 콘텐츠 생성',
        '우선 이메일 지원',
        ...(billingCycle === 'yearly' ? ['🎉 연간 결제 시 20% 할인!'] : [])
      ],
      coming_soon: false
    },
    {
      name: 'pro',
      display_name: '프로',
      max_days: 180,
      price: getPrice(19900),
      features: [
        '최대 180일 복습 간격',
        '완전한 장기 기억 시스템',
        '무제한 콘텐츠 생성',
        '고급 카테고리 관리',
        '데이터 내보내기',
        '전담 고객 지원',
        ...(billingCycle === 'yearly' ? ['🎉 연간 결제 시 20% 할인!'] : [])
      ],
      coming_soon: false
    }
  ];


  // Subscription API
  const subscriptionAPI = {
    upgradeSubscription: async (data: SubscriptionUpgradeData) => {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.REACT_APP_API_URL}/accounts/subscription/upgrade/`, {
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

  // Mutations
  const upgradeMutation = useMutation({
    mutationFn: subscriptionAPI.upgradeSubscription,
    onSuccess: async (data) => {
      const tier = data.subscription?.tier;
      const maxDays = subscriptionTiers.find(t => t.name === tier)?.max_days || 7;
      
      toast.success(
        data.message || 
        `구독이 성공적으로 변경되었습니다! 이제 최대 ${maxDays}일까지의 복습을 확인할 수 있습니다.`
      );
      
      await refreshUser();
      queryClient.invalidateQueries({ queryKey: ['current-subscription'] });
      queryClient.invalidateQueries({ queryKey: ['user'] });
      queryClient.invalidateQueries({ queryKey: ['todayReviews'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (error: any) => {
      toast.error(error.message || '구독 변경에 실패했습니다.');
    }
  });

  const handleTierUpgrade = (tier: SubscriptionTier, billingCycle: 'monthly' | 'yearly') => {
    if (!user?.is_email_verified) {
      toast.error('구독을 변경하려면 먼저 이메일 인증을 완료해주세요.');
      return;
    }

    upgradeMutation.mutate({
      tier,
      billing_cycle: billingCycle
    });
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            로그인이 필요합니다
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            구독 정보를 확인하려면 로그인해주세요.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            💎 구독 플랜
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            에빙하우스 망각곡선을 활용한 스마트 복습 시스템
          </p>

          {/* Coming Soon Notice with Email Signup */}
          <div className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 border border-indigo-200 dark:border-indigo-700 rounded-xl p-8 mb-8 max-w-2xl mx-auto">
            <div className="text-center mb-6">
              <p className="text-indigo-800 dark:text-indigo-300 font-bold text-xl mb-2">
                🚀 곧 출시됩니다!
              </p>
              <p className="text-indigo-700 dark:text-indigo-400 text-sm mb-4">
                더 나은 서비스를 위해 유료 구독은 사용자 200명 달성 후 오픈 예정입니다.
              </p>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                📧 출시 알림 받기
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                오픈 소식을 가장 먼저 받아보세요!
              </p>
            </div>
            <EmailSignup />
          </div>
        </div>

        {/* Subscription Tiers Preview */}
        <div className="mb-8">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 text-center mb-8">
            📋 예정된 구독 플랜
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            {subscriptionTiers.map((tier, index) => (
              <TierCard
                key={tier.name}
                tier={tier}
                currentTier={user.subscription?.tier}
                billingCycle={billingCycle}
                isPopular={tier.name === 'basic'}
                onUpgrade={handleTierUpgrade}
                upgrading={upgradeMutation.isPending}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default SubscriptionPage;