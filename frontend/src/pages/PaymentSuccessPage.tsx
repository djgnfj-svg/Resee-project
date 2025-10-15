import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-hot-toast';
import api from '../utils/api';

const PaymentSuccessPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isProcessing, setIsProcessing] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const paymentKey = searchParams.get('paymentKey');
  const orderId = searchParams.get('orderId');
  const amount = searchParams.get('amount');

  useEffect(() => {
    if (!paymentKey || !orderId || !amount) {
      setError('결제 정보가 올바르지 않습니다.');
      setIsProcessing(false);
      return;
    }

    confirmPayment();
  }, [paymentKey, orderId, amount]);

  const confirmPayment = async () => {
    try {
      setIsProcessing(true);

      // Confirm payment with backend
      const response = await api.post('/accounts/payment/confirm/', {
        payment_key: paymentKey,
        order_id: orderId,
        amount: parseInt(amount || '0')
      });

      if (response.data.success) {
        setSuccess(true);
        toast.success('결제가 완료되었습니다!');

        // Refresh user data
        await refreshUser();

        // Redirect to subscription page after 3 seconds
        setTimeout(() => {
          navigate('/subscription');
        }, 3000);
      } else {
        setError(response.data.error || '결제 확인에 실패했습니다.');
      }
    } catch (err: any) {
      console.error('Payment confirmation error:', err);
      setError(err.response?.data?.error || '결제 확인 중 오류가 발생했습니다.');
      toast.error(err.response?.data?.error || '결제 확인에 실패했습니다.');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          {isProcessing ? (
            <>
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                결제를 확인하는 중...
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                잠시만 기다려주세요.
              </p>
            </>
          ) : success ? (
            <>
              <div className="text-green-500 mb-6">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                결제 완료!
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                구독이 성공적으로 활성화되었습니다.
              </p>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  3초 후 구독 페이지로 이동합니다...
                </p>
              </div>
              <button
                onClick={() => navigate('/subscription')}
                className="w-full bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors"
              >
                구독 페이지로 이동
              </button>
            </>
          ) : (
            <>
              <div className="text-red-500 mb-6">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                결제 확인 실패
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {error || '결제 확인 중 오류가 발생했습니다.'}
              </p>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/subscription')}
                  className="w-full bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  구독 페이지로 돌아가기
                </button>
                <button
                  onClick={() => navigate('/payment-history')}
                  className="w-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold py-3 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  결제 내역 확인
                </button>
              </div>
            </>
          )}
        </div>

        {/* Order Info */}
        {orderId && (
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              주문번호: {orderId}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentSuccessPage;
