import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { SubscriptionTierInfo, SubscriptionTier } from '../types';
import { toast } from 'react-hot-toast';
import TierCard from '../components/subscription/TierCard';
import { subscriptionAPI } from '../utils/api';

const SubscriptionPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [billingCycle] = useState<'monthly' | 'yearly'>('monthly');

  // Fetch current subscription
  const { data: currentSubscription, isLoading: subscriptionLoading } = useQuery({
    queryKey: ['current-subscription', user?.id],
    queryFn: subscriptionAPI.getSubscription,
    enabled: !!user,
  });

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
        '20개 콘텐츠 생성',
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
        'AI 서술형 정답 지원',
        '무제한 콘텐츠 생성',
        '상세 통계 및 분석',
        '우선 이메일 지원',
        ...(billingCycle === 'yearly' ? ['연간 결제 시 20% 할인!'] : [])
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
        'AI 서술형 정답 지원',
        'AI 주간 시험 생성',
        '무제한 콘텐츠 생성',
        '상세 통계 및 분석',
        '우선 이메일 지원',
        ...(billingCycle === 'yearly' ? ['연간 결제 시 20% 할인!'] : [])
      ],
      coming_soon: false
    }
  ];



  // Mutations
  const upgradeMutation = useMutation({
    mutationFn: subscriptionAPI.upgradeSubscription,
    onSuccess: async (data) => {
      const tier = data.tier;
      const maxDays = subscriptionTiers.find(t => t.name === tier)?.max_days || 7;

      toast.success(
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

    // For FREE tier, use old password-based flow
    if (tier === 'free') {
      const confirmMessage = '무료 플랜으로 변경하시겠습니까?';

      if (window.confirm(confirmMessage)) {
        const password = window.prompt('보안을 위해 비밀번호를 입력해주세요:');

        if (!password) {
          toast.error('비밀번호를 입력해야 구독을 변경할 수 있습니다.');
          return;
        }

        upgradeMutation.mutate({
          tier,
          billing_cycle: billingCycle,
          password
        });
      }
    } else {
      // For paid tiers (BASIC/PRO), redirect to checkout page
      const cycle = billingCycle === 'monthly' ? 'MONTHLY' : 'YEARLY';
      navigate(`/payment/checkout?tier=${tier}&cycle=${cycle}`);
    }
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

  if (subscriptionLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">구독 정보를 불러오는 중...</p>
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
            구독 플랜
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
            에빙하우스 망각곡선을 활용한 스마트 복습 시스템
          </p>

        </div>

        {/* Payment History Link */}
        <div className="mb-8 text-center">
          <a
            href="/payment-history"
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            결제 내역 보기
          </a>
        </div>

        {/* Subscription Tiers Preview */}
        <div className="mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
            {subscriptionTiers.map((tier, index) => (
              <TierCard
                key={tier.name}
                tier={tier}
                currentTier={currentSubscription?.tier}
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