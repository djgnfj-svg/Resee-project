import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
// import toast from 'react-hot-toast';
import { authAPI, analyticsAPI } from '../utils/api';
import { User, DashboardData } from '../types';

interface ProfileFormData {
  email: string;
  first_name: string;
  last_name: string;
  timezone: string;
  notification_enabled: boolean;
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

  // Form setup
  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<ProfileFormData>({
    defaultValues: user ? {
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      timezone: user.timezone,
      notification_enabled: user.notification_enabled,
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

  const onSubmit = (data: ProfileFormData) => {
    updateProfileMutation.mutate(data);
  };

  const handleCancel = () => {
    if (user) {
      reset({
        email: user.email,
        first_name: user.first_name,
        last_name: user.last_name,
        timezone: user.timezone,
        notification_enabled: user.notification_enabled,
      });
    }
    setIsEditing(false);
  };

  const timezones = [
    { value: 'Asia/Seoul', label: '한국 (KST)' },
    { value: 'America/New_York', label: '뉴욕 (EST)' },
    { value: 'America/Los_Angeles', label: '로스앤젤레스 (PST)' },
    { value: 'Europe/London', label: '런던 (GMT)' },
    { value: 'Europe/Paris', label: '파리 (CET)' },
    { value: 'Asia/Tokyo', label: '도쿄 (JST)' },
    { value: 'Australia/Sydney', label: '시드니 (AEDT)' },
  ];

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
                {user.first_name ? user.first_name[0].toUpperCase() : user.email[0].toUpperCase()}
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                {user.first_name && user.last_name 
                  ? `${user.first_name} ${user.last_name}`
                  : user.email.split('@')[0]
                }
              </h2>
              <p className="text-gray-600">{user.email}</p>
              <p className="text-sm text-gray-500 mt-2">
                가입일: {new Date(user.date_joined).toLocaleDateString()}
              </p>
            </div>
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

              {/* Name */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-2">
                    이름
                  </label>
                  <input
                    type="text"
                    id="first_name"
                    {...register('first_name')}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                  />
                </div>
                <div>
                  <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-2">
                    성
                  </label>
                  <input
                    type="text"
                    id="last_name"
                    {...register('last_name')}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                  />
                </div>
              </div>

              {/* Timezone */}
              <div>
                <label htmlFor="timezone" className="block text-sm font-medium text-gray-700 mb-2">
                  시간대
                </label>
                <select
                  id="timezone"
                  {...register('timezone', { required: '시간대를 선택해주세요' })}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
                >
                  {timezones.map((tz) => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
                {errors.timezone && (
                  <p className="mt-1 text-sm text-red-600">{errors.timezone.message}</p>
                )}
              </div>

              {/* Notification Settings */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('notification_enabled')}
                    disabled={!isEditing}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    복습 알림 받기
                  </span>
                </label>
                <p className="mt-1 text-xs text-gray-500">
                  매일 오전 9시에 복습할 콘텐츠가 있을 때 알림을 받습니다.
                </p>
              </div>
            </form>
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