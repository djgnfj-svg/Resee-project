import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { subscriptionAPI } from '../utils/api';
import { useAuth } from '../contexts/AuthContext';
import { PaymentHistory } from '../types';

const PaymentHistoryPage: React.FC = () => {
  const { user } = useAuth();

  const { data: paymentData, isLoading } = useQuery({
    queryKey: ['payment-history'],
    queryFn: subscriptionAPI.getPaymentHistory,
    enabled: !!user,
  });

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            로그인이 필요합니다
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            결제 내역을 확인하려면 로그인해주세요.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">결제 내역을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  const histories: PaymentHistory[] = paymentData?.results || [];

  const getPaymentTypeColor = (type: string) => {
    switch (type) {
      case 'initial':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'upgrade':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20';
      case 'downgrade':
        return 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20';
      case 'cancellation':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      case 'refund':
        return 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            결제 내역
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            구독 변경 및 결제 이력을 확인하세요
          </p>
        </div>

        {/* Payment History List */}
        {histories.length === 0 ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
            <p className="text-gray-600 dark:text-gray-400">
              결제 내역이 없습니다.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {histories.map((history) => (
              <div
                key={history.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${getPaymentTypeColor(
                          history.payment_type
                        )}`}
                      >
                        {history.payment_type_display}
                      </span>
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(history.created_at).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    <p className="text-gray-900 dark:text-gray-100 font-medium mb-1">
                      {history.description}
                    </p>

                    {history.notes && (
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {history.notes}
                      </p>
                    )}

                    {history.from_tier && history.to_tier && (
                      <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        {history.from_tier} → {history.to_tier}
                      </div>
                    )}
                  </div>

                  <div className="text-right ml-4">
                    <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                      {history.amount > 0 ? `₩${history.amount.toLocaleString()}` : '-'}
                    </div>
                    {history.refund_amount && history.refund_amount > 0 && (
                      <div className="text-sm text-purple-600 dark:text-purple-400 mt-1">
                        환불: ₩{history.refund_amount.toLocaleString()}
                      </div>
                    )}
                    {history.billing_cycle && (
                      <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {history.billing_cycle_display}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Back to Subscription Button */}
        <div className="mt-8">
          <a
            href="/subscription"
            className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
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
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            구독 관리로 돌아가기
          </a>
        </div>
      </div>
    </div>
  );
};

export default PaymentHistoryPage;
