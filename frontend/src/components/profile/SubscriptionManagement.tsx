import React from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCardIcon } from '@heroicons/react/24/outline';
import { subscriptionAPI } from '../../utils/api';
import { User } from '../../types';

interface SubscriptionManagementProps {
  user: User;
}

const SubscriptionManagement: React.FC<SubscriptionManagementProps> = ({ user }) => {
  const queryClient = useQueryClient();

  // Toggle auto renewal mutation
  const toggleAutoRenewalMutation = useMutation({
    mutationFn: subscriptionAPI.toggleAutoRenewal,
    onSuccess: (updatedSubscription) => {
      const isEnabled = updatedSubscription.auto_renewal;
      alert(`Success: 자동갱신이 ${isEnabled ? '활성화' : '비활성화'}되었습니다.`);
      // Update user data with new subscription info
      queryClient.setQueryData(['profile'], (oldData: User | undefined) => {
        if (oldData) {
          return { ...oldData, subscription: updatedSubscription };
        }
        return oldData;
      });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error: any) => {
      const errorMessage = error.userMessage || '자동갱신 설정 변경에 실패했습니다.';
      alert(`Error: ${errorMessage}`);
    },
  });

  const cancelSubscriptionMutation = useMutation({
    mutationFn: subscriptionAPI.cancelSubscription,
    onSuccess: (updatedSubscription) => {
      alert('Success: 구독이 성공적으로 취소되었습니다. 무료 플랜으로 변경되었습니다.');
      // Update user data with new subscription info
      queryClient.setQueryData(['profile'], (oldData: User | undefined) => {
        if (oldData) {
          return { ...oldData, subscription: updatedSubscription };
        }
        return oldData;
      });
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: (error: any) => {
      const errorMessage = error.userMessage || '구독 취소에 실패했습니다.';
      alert(`Error: ${errorMessage}`);
    },
  });

  const handleCancelSubscription = () => {
    if (window.confirm(
      '정말 구독을 취소하시겠습니까?\n\n' +
      '구독을 취소하면:\n' +
      '• 무료 플랜으로 변경됩니다\n' +
      '• 복습 간격이 3일로 제한됩니다\n\n' +
      '이 작업은 즉시 적용되며 되돌릴 수 없습니다.'
    )) {
      cancelSubscriptionMutation.mutate();
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">구독 정보</h3>
      {user.subscription ? (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">현재 플랜</span>
            <span className="font-medium text-gray-900">
              {user.subscription.tier_display}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">상태</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              user.subscription.is_active
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {user.subscription.is_active ? '활성' : '비활성'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">최대 복습 간격</span>
            <span className="font-medium text-gray-900">
              {user.subscription.max_interval_days}일
            </span>
          </div>
          {user.subscription.days_remaining && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">남은 기간</span>
              <span className="font-medium text-gray-900">
                {user.subscription.days_remaining}일
              </span>
            </div>
          )}
          {user.subscription.tier !== 'free' && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">자동갱신</span>
                <button
                  onClick={() => toggleAutoRenewalMutation.mutate()}
                  disabled={toggleAutoRenewalMutation.isPending}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    user.subscription.auto_renewal
                      ? 'bg-green-600'
                      : 'bg-gray-300'
                  } ${toggleAutoRenewalMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      user.subscription.auto_renewal ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
              {user.subscription.auto_renewal && user.subscription.next_billing_date && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">다음 결제일</span>
                  <span className="font-medium text-gray-900">
                    {new Date(user.subscription.next_billing_date).toLocaleDateString('ko-KR')}
                  </span>
                </div>
              )}
            </>
          )}
          <div className="pt-3 border-t space-y-2">
            <Link
              to="/subscription"
              className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 hover:border-blue-700 rounded-lg transition-colors"
            >
              <CreditCardIcon className="w-4 h-4 mr-2" />
              구독 관리
            </Link>
            {user.subscription.tier !== 'free' && (
              <button
                onClick={handleCancelSubscription}
                disabled={cancelSubscriptionMutation.isPending}
                className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 border border-red-600 hover:border-red-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {cancelSubscriptionMutation.isPending ? (
                  <>
                    <div className="w-4 h-4 mr-2 animate-spin rounded-full border-b-2 border-red-600"></div>
                    취소 중...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    구독 취소
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500 mb-4">구독 정보가 없습니다</p>
          <Link
            to="/subscription"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <CreditCardIcon className="w-4 h-4 mr-2" />
            구독하기
          </Link>
        </div>
      )}
    </div>
  );
};

export default SubscriptionManagement;