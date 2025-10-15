import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { loadPaymentWidget } from '@tosspayments/payment-widget-sdk';
import { toast } from 'react-hot-toast';
import api from '../utils/api';

const CheckoutPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const tier = searchParams.get('tier') || 'basic';
  const billingCycle = searchParams.get('cycle') || 'MONTHLY';

  useEffect(() => {
    if (!user) {
      toast.error('로그인이 필요합니다.');
      navigate('/login');
      return;
    }

    if (!user.is_email_verified) {
      toast.error('이메일 인증이 필요합니다.');
      navigate('/subscription');
      return;
    }

    initializePayment();
  }, [user, tier, billingCycle]);

  const initializePayment = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Create payment checkout
      const response = await api.post('/accounts/payment/checkout/', {
        tier: tier.toUpperCase(),
        billing_cycle: billingCycle
      });

      const { order_id, amount, client_key, payment_key } = response.data;

      // Load Toss Payment Widget
      const paymentWidget = await loadPaymentWidget(client_key, user?.email || '');

      // Render payment methods
      await paymentWidget.renderPaymentMethods('#payment-method', {
        value: amount,
        currency: 'KRW'
      });

      // Render agreement checkbox
      await paymentWidget.renderAgreement('#agreement');

      // Setup payment button
      const button = document.getElementById('payment-button');
      if (button) {
        button.addEventListener('click', async () => {
          try {
            // Request payment
            await paymentWidget.requestPayment({
              orderId: order_id,
              orderName: `Resee ${tier.toUpperCase()} 구독`,
              customerName: user?.email?.split('@')[0] || 'Customer',
              customerEmail: user?.email || '',
              successUrl: `${window.location.origin}/payment/success`,
              failUrl: `${window.location.origin}/payment/fail`
            });
          } catch (err: any) {
            console.error('Payment request error:', err);
            toast.error(err.message || '결제 요청에 실패했습니다.');
          }
        });
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error('Payment initialization error:', err);
      setError(err.response?.data?.error || '결제 초기화에 실패했습니다.');
      setIsLoading(false);
      toast.error(err.response?.data?.error || '결제 초기화에 실패했습니다.');
    }
  };

  const getPricing = () => {
    const pricing: Record<string, Record<string, number>> = {
      basic: { MONTHLY: 5000, YEARLY: 50000 },
      pro: { MONTHLY: 20000, YEARLY: 200000 }
    };
    return pricing[tier.toLowerCase()]?.[billingCycle] || 0;
  };

  const getTierName = () => {
    const names: Record<string, string> = {
      basic: '베이직',
      pro: '프로'
    };
    return names[tier.toLowerCase()] || tier;
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/subscription')}
            className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 mb-4 flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            구독 플랜으로 돌아가기
          </button>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            결제하기
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {getTierName()} 플랜 ({billingCycle === 'MONTHLY' ? '월간' : '연간'})
          </p>
        </div>

        {/* Order Summary */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            주문 정보
          </h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">플랜</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {getTierName()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">결제 주기</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {billingCycle === 'MONTHLY' ? '월간' : '연간'}
              </span>
            </div>
            <div className="border-t border-gray-200 dark:border-gray-700 pt-3 flex justify-between">
              <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                총 결제 금액
              </span>
              <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {getPricing().toLocaleString()}원
              </span>
            </div>
          </div>
        </div>

        {/* Payment Widget */}
        {isLoading ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">결제 페이지를 준비하는 중...</p>
          </div>
        ) : error ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              결제 초기화 실패
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
            <button
              onClick={() => navigate('/subscription')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              구독 플랜으로 돌아가기
            </button>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            {/* Payment Methods */}
            <div id="payment-method" className="mb-6"></div>

            {/* Agreement */}
            <div id="agreement" className="mb-6"></div>

            {/* Payment Button */}
            <button
              id="payment-button"
              className="w-full bg-blue-600 text-white font-semibold py-4 px-6 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {getPricing().toLocaleString()}원 결제하기
            </button>

            {/* Notice */}
            <div className="mt-6 text-sm text-gray-500 dark:text-gray-400 space-y-2">
              <p>• 결제는 Toss Payments를 통해 안전하게 처리됩니다.</p>
              <p>• 구독은 자동 갱신되며, 언제든지 취소할 수 있습니다.</p>
              <p>• 결제 관련 문의는 고객센터로 연락주세요.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckoutPage;
