import React from 'react';
import { Link } from 'react-router-dom';
// import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CreditCardIcon } from '@heroicons/react/24/outline';
// import { subscriptionAPI } from '../../utils/api';
import { User } from '../../types';

interface SubscriptionManagementProps {
  user: User;
}

const SubscriptionManagement: React.FC<SubscriptionManagementProps> = ({ user }) => {
  // Commented out until subscription management UI is implemented
  // const queryClient = useQueryClient();

  // // Toggle auto renewal mutation
  // const toggleAutoRenewalMutation = useMutation({
  //   mutationFn: ({ password, autoRenewal }: { password: string; autoRenewal: boolean }) =>
  //     subscriptionAPI.toggleAutoRenewal(password, autoRenewal),
  //   onSuccess: (updatedSubscription) => {
  //     const isEnabled = updatedSubscription.auto_renewal;
  //     alert(`Success: 자동갱신이 ${isEnabled ? '활성화' : '비활성화'}되었습니다.`);
  //     // Update user data with new subscription info
  //     queryClient.setQueryData(['profile'], (oldData: User | undefined) => {
  //       if (oldData) {
  //         return { ...oldData, subscription: updatedSubscription };
  //       }
  //       return oldData;
  //     });
  //     queryClient.invalidateQueries({ queryKey: ['profile'] });
  //   },
  //   onError: (error: any) => {
  //     const errorMessage = error.userMessage || '자동갱신 설정 변경에 실패했습니다.';
  //     alert(`Error: ${errorMessage}`);
  //   },
  // });

  // const cancelSubscriptionMutation = useMutation({
  //   mutationFn: (password: string) => subscriptionAPI.cancelSubscription(password),
  //   onSuccess: (updatedSubscription) => {
  //     alert('Success: 구독이 성공적으로 취소되었습니다. 무료 플랜으로 변경되었습니다.');
  //     // Update user data with new subscription info
  //     queryClient.setQueryData(['profile'], (oldData: User | undefined) => {
  //       if (oldData) {
  //         return { ...oldData, subscription: updatedSubscription };
  //       }
  //       return oldData;
  //     });
  //     queryClient.invalidateQueries({ queryKey: ['profile'] });
  //   },
  //   onError: (error: any) => {
  //     const errorMessage = error.userMessage || '구독 취소에 실패했습니다.';
  //     alert(`Error: ${errorMessage}`);
  //   },
  // });

  // Commented out until subscription management UI is implemented
  // const handleToggleAutoRenewal = () => {
  //   const password = window.prompt('비밀번호를 입력해주세요:');
  //   if (!password) return;

  //   const newAutoRenewal = !user.subscription?.auto_renewal;
  //   toggleAutoRenewalMutation.mutate({ password, autoRenewal: newAutoRenewal });
  // };

  // const handleCancelSubscription = () => {
  //   if (window.confirm(
  //     '정말 구독을 취소하시겠습니까?\n\n' +
  //     '구독을 취소하면:\n' +
  //     '• 무료 플랜으로 변경됩니다\n' +
  //     '• 복습 간격이 3일로 제한됩니다\n\n' +
  //     '이 작업은 즉시 적용되며 되돌릴 수 없습니다.'
  //   )) {
  //     const password = window.prompt('비밀번호를 입력해주세요:');
  //     if (!password) return;

  //     cancelSubscriptionMutation.mutate(password);
  //   }
  // };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">구독 정보</h3>
      {user.subscription ? (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">현재 플랜</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {user.subscription.tier_display}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">상태</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              user.subscription.is_active
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {user.subscription.is_active ? '활성' : '비활성'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">최대 복습 간격</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {user.subscription.max_interval_days}일
            </span>
          </div>
          {user.subscription.days_remaining && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">남은 기간</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {user.subscription.days_remaining}일
              </span>
            </div>
          )}
          <div className="pt-3 border-t space-y-2">
            <Link
              to="/subscription"
              className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 border border-indigo-600 hover:border-indigo-700 rounded-lg transition-colors"
            >
              <CreditCardIcon className="w-4 h-4 mr-2" />
              구독 플랜 보기
            </Link>
            {user.subscription.tier !== 'free' && (
              <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-3">
                <p className="text-xs text-amber-800 dark:text-amber-200 text-center">
                  유료 플랜은 12월에 오픈 예정입니다
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500 dark:text-gray-400 mb-4">구독 정보가 없습니다</p>
          <Link
            to="/subscription"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
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