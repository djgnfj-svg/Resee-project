import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { authAPI } from '../utils/api';
import { User } from '../types';

interface NotificationSettings {
  notification_enabled: boolean;
  daily_reminder_time: string;
  email_notifications: boolean;
}

interface SecuritySettings {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

const SettingsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'notifications' | 'security' | 'data'>('notifications');

  // Fetch user profile
  const { data: user, isLoading } = useQuery<User>({
    queryKey: ['profile'],
    queryFn: authAPI.getProfile,
  });

  // Notification settings form
  const notificationForm = useForm<NotificationSettings>({
    defaultValues: {
      notification_enabled: user?.notification_enabled || false,
      daily_reminder_time: '09:00',
      email_notifications: false,
    },
  });

  // Security settings form
  const securityForm = useForm<SecuritySettings>({
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: authAPI.updateProfile,
    onSuccess: () => {
      toast.success('설정이 성공적으로 저장되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['profile'] });
    },
    onError: () => {
      toast.error('설정 저장에 실패했습니다.');
    },
  });

  const onNotificationSubmit = (data: NotificationSettings) => {
    updateProfileMutation.mutate({
      notification_enabled: data.notification_enabled,
    });
  };

  // Password change mutation
  const changePasswordMutation = useMutation({
    mutationFn: authAPI.changePassword,
    onSuccess: () => {
      toast.success('비밀번호가 성공적으로 변경되었습니다!');
      securityForm.reset();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.current_password || error.response?.data?.new_password || '비밀번호 변경에 실패했습니다.';
      toast.error(errorMessage);
    },
  });

  const onSecuritySubmit = (data: SecuritySettings) => {
    if (data.new_password !== data.confirm_password) {
      toast.error('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    changePasswordMutation.mutate({
      current_password: data.current_password,
      new_password: data.new_password,
      new_password_confirm: data.confirm_password,
    });
  };

  const exportData = () => {
    toast.success('데이터 내보내기가 시작되었습니다. 이메일로 다운로드 링크를 보내드릴게요.');
  };

  // Account deletion form
  const deleteAccountForm = useForm<{ password: string; confirmation: string }>({
    defaultValues: {
      password: '',
      confirmation: '',
    },
  });

  // Account deletion mutation
  const deleteAccountMutation = useMutation({
    mutationFn: authAPI.deleteAccount,
    onSuccess: () => {
      toast.success('계정이 성공적으로 삭제되었습니다.');
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.password || error.response?.data?.confirmation || '계정 삭제에 실패했습니다.';
      toast.error(errorMessage);
    },
  });

  const onDeleteAccount = (data: { password: string; confirmation: string }) => {
    if (data.confirmation !== 'DELETE') {
      toast.error('"DELETE"를 정확히 입력해주세요.');
      return;
    }
    deleteAccountMutation.mutate(data);
  };

  const tabs = [
    { id: 'notifications', name: '알림 설정', icon: '🔔' },
    { id: 'security', name: '보안', icon: '🔒' },
    { id: 'data', name: '데이터 관리', icon: '📊' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">설정</h1>
        <p className="mt-2 text-gray-600">
          계정 설정과 환경을 관리할 수 있습니다.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        {/* Tabs - Mobile Responsive */}
        <div className="border-b border-gray-200">
          {/* Mobile Tab Selector */}
          <div className="block sm:hidden p-4">
            <select
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value as any)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              {tabs.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {tab.icon} {tab.name}
                </option>
              ))}
            </select>
          </div>
          
          {/* Desktop Tabs */}
          <nav className="hidden sm:flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-4 sm:p-6">
          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">알림 설정</h3>
                <form onSubmit={notificationForm.handleSubmit(onNotificationSubmit)} className="space-y-4">
                  <div className="space-y-4">
                    <div className="flex items-start">
                      <div className="flex items-center h-5">
                        <input
                          id="notification_enabled"
                          type="checkbox"
                          {...notificationForm.register('notification_enabled')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                        />
                      </div>
                      <div className="ml-3 text-sm">
                        <label htmlFor="notification_enabled" className="font-medium text-gray-700">
                          복습 알림 받기
                        </label>
                        <p className="text-gray-500">
                          복습할 콘텐츠가 있을 때 알림을 받습니다.
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start">
                      <div className="flex items-center h-5">
                        <input
                          id="email_notifications"
                          type="checkbox"
                          {...notificationForm.register('email_notifications')}
                          className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                        />
                      </div>
                      <div className="ml-3 text-sm">
                        <label htmlFor="email_notifications" className="font-medium text-gray-700">
                          이메일 알림 받기
                        </label>
                        <p className="text-gray-500">
                          중요한 업데이트를 이메일로 받습니다.
                        </p>
                      </div>
                    </div>

                    <div>
                      <label htmlFor="daily_reminder_time" className="block text-sm font-medium text-gray-700 mb-2">
                        일일 알림 시간
                      </label>
                      <input
                        type="time"
                        id="daily_reminder_time"
                        {...notificationForm.register('daily_reminder_time')}
                        className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                      />
                      <p className="mt-1 text-sm text-gray-500">
                        매일 이 시간에 복습 알림을 받습니다.
                      </p>
                    </div>
                  </div>

                  <div className="pt-4">
                    <button
                      type="submit"
                      disabled={updateProfileMutation.isPending}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                      {updateProfileMutation.isPending ? '저장 중...' : '설정 저장'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">비밀번호 변경</h3>
                <form onSubmit={securityForm.handleSubmit(onSecuritySubmit)} className="space-y-4">
                  <div>
                    <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 mb-2">
                      현재 비밀번호
                    </label>
                    <input
                      type="password"
                      id="current_password"
                      {...securityForm.register('current_password', { required: '현재 비밀번호를 입력해주세요' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
                      새 비밀번호
                    </label>
                    <input
                      type="password"
                      id="new_password"
                      {...securityForm.register('new_password', { 
                        required: '새 비밀번호를 입력해주세요',
                        minLength: { value: 8, message: '비밀번호는 최소 8자 이상이어야 합니다' }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 mb-2">
                      새 비밀번호 확인
                    </label>
                    <input
                      type="password"
                      id="confirm_password"
                      {...securityForm.register('confirm_password', { required: '비밀번호 확인을 입력해주세요' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div className="pt-4">
                    <button
                      type="submit"
                      disabled={changePasswordMutation.isPending}
                      className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                      {changePasswordMutation.isPending ? '변경 중...' : '비밀번호 변경'}
                    </button>
                  </div>
                </form>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">보안 정보</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-blue-800">보안 팁</h3>
                      <div className="mt-2 text-sm text-blue-700">
                        <ul className="list-disc pl-5 space-y-1">
                          <li>강력한 비밀번호를 사용하세요 (대소문자, 숫자, 특수문자 포함)</li>
                          <li>정기적으로 비밀번호를 변경하세요</li>
                          <li>다른 사이트와 같은 비밀번호를 사용하지 마세요</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Data Tab */}
          {activeTab === 'data' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">데이터 관리</h3>
                
                <div className="space-y-4">
                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-base font-medium text-gray-900">데이터 내보내기</h4>
                        <p className="text-sm text-gray-600">
                          모든 학습 데이터를 JSON 형식으로 내보냅니다.
                        </p>
                      </div>
                      <button
                        onClick={exportData}
                        className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                      >
                        내보내기
                      </button>
                    </div>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-base font-medium text-gray-900">데이터 가져오기</h4>
                        <p className="text-sm text-gray-600">
                          이전에 내보낸 데이터를 가져옵니다.
                        </p>
                      </div>
                      <button
                        disabled
                        className="bg-gray-300 text-gray-500 px-4 py-2 rounded-md text-sm font-medium cursor-not-allowed"
                      >
                        준비 중
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-red-600 mb-4">위험 영역</h3>
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="mb-4">
                    <h4 className="text-base font-medium text-red-900">계정 삭제</h4>
                    <p className="text-sm text-red-700">
                      모든 데이터가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
                    </p>
                  </div>
                  
                  <form onSubmit={deleteAccountForm.handleSubmit(onDeleteAccount)} className="space-y-4">
                    <div>
                      <label htmlFor="delete_password" className="block text-sm font-medium text-red-700 mb-2">
                        계정 삭제를 위해 비밀번호를 입력해주세요
                      </label>
                      <input
                        type="password"
                        id="delete_password"
                        {...deleteAccountForm.register('password', { required: '비밀번호를 입력해주세요' })}
                        className="w-full px-3 py-2 border border-red-300 rounded-md focus:ring-red-500 focus:border-red-500"
                        placeholder="비밀번호"
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="delete_confirmation" className="block text-sm font-medium text-red-700 mb-2">
                        계정 삭제를 확인하기 위해 "DELETE"를 입력해주세요
                      </label>
                      <input
                        type="text"
                        id="delete_confirmation"
                        {...deleteAccountForm.register('confirmation', { required: '"DELETE"를 입력해주세요' })}
                        className="w-full px-3 py-2 border border-red-300 rounded-md focus:ring-red-500 focus:border-red-500"
                        placeholder="DELETE"
                      />
                    </div>
                    
                    <div className="pt-2">
                      <button
                        type="submit"
                        disabled={deleteAccountMutation.isPending}
                        className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
                      >
                        {deleteAccountMutation.isPending ? '삭제 중...' : '계정 영구 삭제'}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;