import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { authAPI } from '../../utils/api';

interface NotificationSettings {
  notification_enabled: boolean;
  daily_reminder_time: string;
  email_notifications: boolean;
}

const NotificationTab: React.FC = () => {
  const notificationForm = useForm<NotificationSettings>({
    defaultValues: {
      notification_enabled: false,
      daily_reminder_time: '09:00',
      email_notifications: false,
    },
  });

  const updateProfileMutation = useMutation({
    mutationFn: authAPI.updateProfile,
    onSuccess: () => {
      alert('Success: 설정이 성공적으로 저장되었습니다!');
    },
    onError: () => {
      alert('Error: 설정 저장에 실패했습니다.');
    },
  });

  const onNotificationSubmit = (data: NotificationSettings) => {
    // Notification settings are not supported in current User model
    alert('알림 설정은 현재 지원되지 않습니다.');
  };

  return (
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
  );
};

export default NotificationTab;