import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { authAPI } from '../utils/api';
import { User } from '../types';
import UserProfileForm from '../components/profile/UserProfileForm';
import SubscriptionManagement from '../components/profile/SubscriptionManagement';
import PaymentHistory from '../components/profile/PaymentHistory';
import AccountStats from '../components/profile/AccountStats';
import { useAuth } from '../contexts/AuthContext';

const ProfilePage: React.FC = () => {
  const { user: currentUser } = useAuth();

  // Fetch user profile
  const { data: user, isLoading } = useQuery<User>({
    queryKey: ['profile', currentUser?.id],
    queryFn: authAPI.getProfile,
    enabled: !!currentUser,
  });


  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-gray-200 dark:border-gray-700 border-t-indigo-600 dark:border-t-indigo-400"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">프로필을 불러올 수 없습니다</h3>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">잠시 후 다시 시도해주세요.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Gradient Header */}
      <div className="mb-8 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">프로필 관리</h1>
            <p className="text-indigo-100 text-sm mt-1">
              계정 정보를 관리하고 알림 설정을 변경할 수 있습니다
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Info Card */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 overflow-hidden">
            {/* Top accent line */}
            <div className="h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 -mx-6 -mt-6 mb-6"></div>

            <div className="text-center">
              <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold mb-4 shadow-lg">
                {user.username ? user.username[0].toUpperCase() : user.email[0].toUpperCase()}
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                {user.username || user.email.split('@')[0]}
              </h2>
              <p className="text-gray-600 dark:text-gray-400">{user.email}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                가입일: {user.created_at
                  ? new Date(user.created_at).toLocaleDateString('ko-KR', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric'
                    })
                  : '정보 없음'}
              </p>
            </div>
          </div>

          {/* Subscription Management */}
          <div className="mt-6">
            <SubscriptionManagement user={user} />
          </div>
        </div>

        {/* Profile Form and Additional Info */}
        <div className="lg:col-span-2">
          <UserProfileForm user={user} />

          {/* Payment History */}
          <div className="mt-8">
            <PaymentHistory />
          </div>

          {/* Account Statistics */}
          <div className="mt-8">
            <AccountStats />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;