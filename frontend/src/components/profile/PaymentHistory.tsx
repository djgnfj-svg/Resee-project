import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { subscriptionAPI } from '../../utils/api';
import { PaymentHistory as PaymentHistoryType } from '../../types';

const PaymentHistory: React.FC = () => {
  // Fetch payment history
  const { data: paymentHistoryData, isLoading: paymentHistoryLoading } = useQuery({
    queryKey: ['payment-history'],
    queryFn: subscriptionAPI.getPaymentHistory,
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">결제 이력</h3>
      {paymentHistoryLoading ? (
        <div className="flex items-center justify-center h-24">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      ) : paymentHistoryData?.results && paymentHistoryData.results.length > 0 ? (
        <div className="space-y-3">
          {paymentHistoryData.results.map((history: PaymentHistoryType) => (
            <div key={history.id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      history.payment_type === 'upgrade' || history.payment_type === 'initial'
                        ? 'bg-green-100 text-green-800'
                        : history.payment_type === 'cancellation'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {history.payment_type_display}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {history.tier_display}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {history.description}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(history.created_at).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <div className="text-right ml-4">
                  <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {history.amount > 0 ? `₩${history.amount.toLocaleString()}` : '무료'}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">아직 결제 이력이 없습니다</p>
        </div>
      )}
    </div>
  );
};

export default PaymentHistory;