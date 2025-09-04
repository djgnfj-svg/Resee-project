import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
// import toast from 'react-hot-toast';
import { authAPI, analyticsAPI, subscriptionAPI } from '../utils/api';
import { User, DashboardData, PaymentHistory } from '../types';
import { CreditCardIcon } from '@heroicons/react/24/outline';

interface ProfileFormData {
  email: string;
  username?: string;
}

const ProfilePage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);

  // Fetch user profile
  const { data: user, isLoading } = useQuery<User>({
    queryKey: ['profile'],
    queryFn: authAPI.getProfile,
  });

  // Fetch dashboard statistics
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: analyticsAPI.getDashboard,
  });

  // Fetch payment history
  const { data: paymentHistoryData, isLoading: paymentHistoryLoading } = useQuery({
    queryKey: ['payment-history'],
    queryFn: subscriptionAPI.getPaymentHistory,
  });

  // Form setup
  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<ProfileFormData>({
    defaultValues: user ? {
      email: user.email,
      username: user.username || '',
    } : undefined,
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: authAPI.updateProfile,
    onSuccess: (updatedUser) => {
      alert('Success: 프로필이 성공적으로 업데이트되었습니다!');
      queryClient.setQueryData(['profile'], updatedUser);
      setIsEditing(false);
    },
    onError: () => {
      alert('Error: 프로필 업데이트에 실패했습니다.');
    },
  });

  // Cancel subscription mutation
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

  const onSubmit = (data: ProfileFormData) => {
    updateProfileMutation.mutate(data);
  };

  const handleCancel = () => {
    if (user) {
      reset({
        email: user.email,
        username: user.username || '',
      });
    }
    setIsEditing(false);
  };

  const handleCancelSubscription = () => {
    if (window.confirm(
      '정말 구독을 취소하시겠습니까?\n\n' +
      '구독을 취소하면:\n' +
      '• 무료 플랜으로 변경됩니다\n' +
      '• 복습 간격이 3일로 제한됩니다\n' +
      '• AI 기능 사용이 제한됩니다\n\n' +
      '이 작업은 즉시 적용되며 되돌릴 수 없습니다.'
    )) {
      cancelSubscriptionMutation.mutate();
    }
  };


  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900">프로필을 불러올 수 없습니다</h3>
        <p className="mt-2 text-sm text-gray-600">잠시 후 다시 시도해주세요.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">프로필 관리</h1>
        <p className="mt-2 text-gray-600">
          계정 정보를 관리하고 알림 설정을 변경할 수 있습니다.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Info Card */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-center">
              <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold mb-4">
                {user.username ? user.username[0].toUpperCase() : user.email[0].toUpperCase()}
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                {user.username || user.email.split('@')[0]}
              </h2>
              <p className="text-gray-600">{user.email}</p>
              <p className="text-sm text-gray-500 mt-2">
                가입일: {new Date(user.created_at).toLocaleDateString('ko-KR')}
              </p>
            </div>
          </div>

          {/* Subscription Card */}
          <div className="bg-white rounded-xl shadow-lg p-6 mt-6">
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
        </div>

        {/* Profile Form */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">개인 정보</h3>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 border border-blue-600 hover:border-blue-700 rounded-lg transition-colors"
                >
                  편집
                </button>
              ) : (
                <div className="flex space-x-2">
                  <button
                    onClick={handleCancel}
                    disabled={updateProfileMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-700 border border-gray-300 hover:border-gray-400 rounded-lg transition-colors disabled:opacity-50"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleSubmit(onSubmit)}
                    disabled={!isDirty || updateProfileMutation.isPending}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {updateProfileMutation.isPending ? '저장 중...' : '저장'}
                  </button>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                  이메일
                </label>
                <input
                  type="email"
                  id="email"
                  {...register('email', { 
                    required: '이메일은 필수입니다',
                    pattern: {
                      value: /^\S+@\S+$/i,
                      message: '유효한 이메일 주소를 입력해주세요'
                    }
                  })}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                />
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                )}
              </div>

              {/* Username */}
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                  사용자명 (선택사항)
                </label>
                <input
                  type="text"
                  id="username"
                  {...register('username', {
                    maxLength: {
                      value: 150,
                      message: '사용자명은 150자 이하여야 합니다'
                    },
                    pattern: {
                      value: /^[a-zA-Z0-9_-]+$/,
                      message: '사용자명은 영문, 숫자, -, _만 사용 가능합니다'
                    }
                  })}
                  disabled={!isEditing}
                  placeholder="사용자명을 입력하세요"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                />
                {errors.username && (
                  <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  사용자명은 프로필에 표시되며, 언제든지 변경할 수 있습니다.
                </p>
              </div>

            </form>
          </div>

          {/* Payment History */}
          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">결제 이력</h3>
            {paymentHistoryLoading ? (
              <div className="flex items-center justify-center h-24">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : paymentHistoryData?.results && paymentHistoryData.results.length > 0 ? (
              <div className="space-y-3">
                {paymentHistoryData.results.map((history: PaymentHistory) => (
                  <div key={history.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
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
                          <span className="text-sm font-medium text-gray-900">
                            {history.tier_display}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {history.description}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
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
                        <p className="text-lg font-semibold text-gray-900">
                          {history.amount > 0 ? `₩${history.amount.toLocaleString()}` : '무료'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="mt-2 text-sm text-gray-600">아직 결제 이력이 없습니다</p>
              </div>
            )}
          </div>

          {/* Account Statistics */}
          <div className="mt-8 bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">계정 통계</h3>
            {statsLoading ? (
              <div className="flex items-center justify-center h-24">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {stats?.total_content || 0}
                  </div>
                  <div className="text-sm text-gray-600">총 콘텐츠</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {stats?.total_reviews_30_days || 0}
                  </div>
                  <div className="text-sm text-gray-600">총 복습 (30일)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {stats?.success_rate ? `${Math.round(stats.success_rate)}%` : '0%'}
                  </div>
                  <div className="text-sm text-gray-600">성공률</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {stats?.streak_days || 0}
                  </div>
                  <div className="text-sm text-gray-600">연속 일수</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;