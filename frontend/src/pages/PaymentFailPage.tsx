import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const PaymentFailPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const code = searchParams.get('code');
  const message = searchParams.get('message');
  const orderId = searchParams.get('orderId');

  const getErrorMessage = () => {
    if (message) {
      return decodeURIComponent(message);
    }

    // Common error codes
    const errorMessages: Record<string, string> = {
      'PAY_PROCESS_CANCELED': '사용자가 결제를 취소했습니다.',
      'PAY_PROCESS_ABORTED': '결제가 중단되었습니다.',
      'REJECT_CARD_COMPANY': '카드사에서 승인을 거부했습니다.',
      'COMMON_ERROR': '결제 처리 중 오류가 발생했습니다.'
    };

    return errorMessages[code || ''] || '결제에 실패했습니다.';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
          {/* Error Icon */}
          <div className="text-red-500 mb-6">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            결제 실패
          </h2>

          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {getErrorMessage()}
          </p>

          {/* Error Details */}
          {(code || orderId) && (
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 mb-6 text-left">
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                오류 상세 정보
              </h3>
              <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                {code && (
                  <p>
                    <span className="font-medium">오류 코드:</span> {code}
                  </p>
                )}
                {orderId && (
                  <p>
                    <span className="font-medium">주문번호:</span> {orderId}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="space-y-3">
            <button
              onClick={() => navigate('/subscription')}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 shadow-md"
            >
              다시 시도하기
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold py-3 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              대시보드로 돌아가기
            </button>
          </div>

          {/* Help Text */}
          <div className="mt-6 text-sm text-gray-500 dark:text-gray-400">
            <p>문제가 계속되면 고객센터로 문의해주세요.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentFailPage;
