import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authAPI } from '../../utils/api';

interface NotificationSettings {
  email_notifications_enabled: boolean;
  daily_reminder_enabled: boolean;
  daily_reminder_time: string;
  evening_reminder_enabled: boolean;
  evening_reminder_time: string;
  weekly_summary_enabled: boolean;
  weekly_summary_day: number;
  weekly_summary_time: string;
}

const NotificationTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedHour, setSelectedHour] = useState(9);
  const [selectedMinute, setSelectedMinute] = useState(0);

  // Fetch current notification preferences
  const { data: notificationPreferences, isLoading: preferencesLoading } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: async () => {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/accounts/notification-preferences/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch notification preferences');
      }

      return response.json();
    },
  });

  const notificationForm = useForm<NotificationSettings>({
    defaultValues: {
      email_notifications_enabled: true,
      daily_reminder_enabled: true,
      daily_reminder_time: '09:00',
      evening_reminder_enabled: false,
      evening_reminder_time: '20:00',
      weekly_summary_enabled: true,
      weekly_summary_day: 1,
      weekly_summary_time: '09:00',
    },
  });

  // Update form values when preferences are loaded
  useEffect(() => {
    if (notificationPreferences) {
      // Reset form with loaded preferences
      notificationForm.reset(notificationPreferences);

      // Parse and set the time from daily_reminder_time
      if (notificationPreferences.daily_reminder_time) {
        const [hours, minutes] = notificationPreferences.daily_reminder_time.split(':');
        setSelectedHour(parseInt(hours, 10));
        setSelectedMinute(parseInt(minutes, 10));
      }
    }
  }, [notificationPreferences, notificationForm]);

  // 시간을 문자열로 포맷
  const formatTime = (hour: number, minute: number) => {
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
  };

  // 시간 옵션 생성 (0-23)
  const hourOptions = Array.from({ length: 24 }, (_, i) => i);

  // 분 옵션 생성 (0-59)
  const minuteOptions = Array.from({ length: 60 }, (_, i) => i);


  // Notification settings update mutation
  const notificationMutation = useMutation({
    mutationFn: async (data: NotificationSettings) => {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/accounts/notification-preferences/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '알림 설정 저장에 실패했습니다.');
      }

      return response.json();
    },
    onSuccess: () => {
      alert('알림 설정이 성공적으로 저장되었습니다.');
      // Invalidate and refetch notification preferences
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
    },
    onError: (error: any) => {
      alert(`Error: ${error.message}`);
    },
  });

  const onNotificationSubmit = (data: NotificationSettings) => {
    // Update the daily_reminder_time with selected time
    const updatedData = {
      ...data,
      daily_reminder_time: formatTime(selectedHour, selectedMinute),
    };
    notificationMutation.mutate(updatedData);
  };

  // Show loading state while fetching preferences
  if (preferencesLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">알림 설정</h3>
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500 dark:text-gray-400">설정을 불러오는 중...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-6">알림 설정</h3>
        <form onSubmit={notificationForm.handleSubmit(onNotificationSubmit)} className="space-y-6">
          <div className="space-y-6">
            {/* 복습 알림 받기 */}
            <div className="flex items-start space-x-3">
              <div className="flex items-center h-5 mt-0.5">
                <input
                  id="daily_reminder_enabled"
                  type="checkbox"
                  {...notificationForm.register('daily_reminder_enabled')}
                  className="focus:ring-blue-500 focus:ring-2 h-4 w-4 text-blue-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                />
              </div>
              <div className="min-w-0 flex-1">
                <label htmlFor="daily_reminder_enabled" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  복습 알림 받기
                </label>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  복습할 콘텐츠가 있을 때 알림을 받습니다.
                </p>
              </div>
            </div>

            {/* 이메일 알림 받기 */}
            <div className="flex items-start space-x-3">
              <div className="flex items-center h-5 mt-0.5">
                <input
                  id="email_notifications_enabled"
                  type="checkbox"
                  {...notificationForm.register('email_notifications_enabled')}
                  className="focus:ring-blue-500 focus:ring-2 h-4 w-4 text-blue-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                />
              </div>
              <div className="min-w-0 flex-1">
                <label htmlFor="email_notifications_enabled" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  이메일 알림 받기
                </label>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  중요한 업데이트를 이메일로 받습니다.
                </p>
              </div>
            </div>

            {/* 일일 알림 시간 */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                일일 알림 시간
              </label>
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  {/* 시간 선택 */}
                  <select
                    value={selectedHour}
                    onChange={(e) => {
                      const hour = parseInt(e.target.value);
                      setSelectedHour(hour);
                      notificationForm.setValue('daily_reminder_time', formatTime(hour, selectedMinute));
                    }}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm shadow-sm"
                    style={{ width: '70px' }}
                  >
                    {hourOptions.map(hour => (
                      <option key={hour} value={hour}>
                        {hour.toString().padStart(2, '0')}
                      </option>
                    ))}
                  </select>

                  <span className="text-gray-500 dark:text-gray-400 font-medium">:</span>

                  {/* 분 선택 */}
                  <select
                    value={selectedMinute}
                    onChange={(e) => {
                      const minute = parseInt(e.target.value);
                      setSelectedMinute(minute);
                      notificationForm.setValue('daily_reminder_time', formatTime(selectedHour, minute));
                    }}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm shadow-sm"
                    style={{ width: '70px' }}
                  >
                    {minuteOptions.map(minute => (
                      <option key={minute} value={minute}>
                        {minute.toString().padStart(2, '0')}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    매일 이 시간에 복습 알림을 받습니다.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="submit"
              disabled={notificationMutation.isPending}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {notificationMutation.isPending ? '저장 중...' : '설정 저장'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NotificationTab;