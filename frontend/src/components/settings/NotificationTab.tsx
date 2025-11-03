import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

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
  const [dailyHour, setDailyHour] = useState(9);
  const [eveningHour, setEveningHour] = useState(20);
  const [weeklyHour, setWeeklyHour] = useState(9);

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
      daily_reminder_time: '09:00:00',
      evening_reminder_enabled: false,
      evening_reminder_time: '20:00:00',
      weekly_summary_enabled: true,
      weekly_summary_day: 1,
      weekly_summary_time: '09:00:00',
    },
  });

  // Update form values when preferences are loaded
  useEffect(() => {
    if (notificationPreferences) {
      // Reset form with loaded preferences
      notificationForm.reset(notificationPreferences);

      // Parse and set the hours from time fields
      if (notificationPreferences.daily_reminder_time) {
        const [hours] = notificationPreferences.daily_reminder_time.split(':');
        setDailyHour(parseInt(hours, 10));
      }
      if (notificationPreferences.evening_reminder_time) {
        const [hours] = notificationPreferences.evening_reminder_time.split(':');
        setEveningHour(parseInt(hours, 10));
      }
      if (notificationPreferences.weekly_summary_time) {
        const [hours] = notificationPreferences.weekly_summary_time.split(':');
        setWeeklyHour(parseInt(hours, 10));
      }
    }
  }, [notificationPreferences, notificationForm]);

  // 시간을 문자열로 포맷 (시간 단위만, 분/초는 00으로 고정)
  const formatTime = (hour: number) => {
    return `${hour.toString().padStart(2, '0')}:00:00`;
  };

  // 시간대별 추천 시간 옵션
  const getTimeLabel = (hour: number) => {
    if (hour >= 6 && hour <= 11) return `${hour}시 (오전)`;
    if (hour >= 12 && hour <= 17) return `${hour}시 (오후)`;
    if (hour >= 18 && hour <= 23) return `${hour}시 (저녁)`;
    return `${hour}시 (새벽)`;
  };

  // 시간 옵션 생성 (0-23)
  const hourOptions = Array.from({ length: 24 }, (_, i) => i);


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
    // Update all time fields with selected hours
    const updatedData = {
      ...data,
      daily_reminder_time: formatTime(dailyHour),
      evening_reminder_time: formatTime(eveningHour),
      weekly_summary_time: formatTime(weeklyHour),
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
        <form onSubmit={notificationForm.handleSubmit(onNotificationSubmit)} className="space-y-8">
          {/* 전체 이메일 알림 설정 */}
          <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-lg">
            <div className="flex items-start space-x-3">
              <div className="flex items-center h-5 mt-0.5">
                <input
                  id="email_notifications_enabled"
                  type="checkbox"
                  {...notificationForm.register('email_notifications_enabled')}
                  className="focus:ring-indigo-500 focus:ring-2 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                />
              </div>
              <div className="min-w-0 flex-1">
                <label htmlFor="email_notifications_enabled" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  이메일 알림 활성화
                </label>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  모든 이메일 알림을 받으려면 이 옵션을 활성화하세요.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {/* 일일 복습 알림 */}
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex items-center h-5 mt-0.5">
                  <input
                    id="daily_reminder_enabled"
                    type="checkbox"
                    {...notificationForm.register('daily_reminder_enabled')}
                    className="focus:ring-indigo-500 focus:ring-2 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <label htmlFor="daily_reminder_enabled" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    일일 복습 알림
                  </label>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    매일 지정한 시간에 오늘 복습할 콘텐츠가 있으면 알림을 받습니다.
                  </p>
                </div>
              </div>

              <div className="ml-7 space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  알림 시간
                </label>
                <select
                  value={dailyHour}
                  onChange={(e) => {
                    const hour = parseInt(e.target.value);
                    setDailyHour(hour);
                    notificationForm.setValue('daily_reminder_time', formatTime(hour));
                  }}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm shadow-sm min-w-32"
                >
                  {hourOptions.map(hour => (
                    <option key={hour} value={hour}>
                      {getTimeLabel(hour)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* 저녁 리마인더 */}
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex items-center h-5 mt-0.5">
                  <input
                    id="evening_reminder_enabled"
                    type="checkbox"
                    {...notificationForm.register('evening_reminder_enabled')}
                    className="focus:ring-indigo-500 focus:ring-2 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <label htmlFor="evening_reminder_enabled" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    저녁 리마인더
                  </label>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    아직 완료하지 못한 오늘의 복습이 있을 때 저녁에 한 번 더 알림을 받습니다.
                  </p>
                </div>
              </div>

              <div className="ml-7 space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  리마인더 시간
                </label>
                <select
                  value={eveningHour}
                  onChange={(e) => {
                    const hour = parseInt(e.target.value);
                    setEveningHour(hour);
                    notificationForm.setValue('evening_reminder_time', formatTime(hour));
                  }}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm shadow-sm min-w-32"
                >
                  {hourOptions.map(hour => (
                    <option key={hour} value={hour}>
                      {getTimeLabel(hour)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* 주간 요약 */}
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex items-center h-5 mt-0.5">
                  <input
                    id="weekly_summary_enabled"
                    type="checkbox"
                    {...notificationForm.register('weekly_summary_enabled')}
                    className="focus:ring-indigo-500 focus:ring-2 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
                  />
                </div>
                <div className="min-w-0 flex-1">
                  <label htmlFor="weekly_summary_enabled" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    주간 학습 요약
                  </label>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    매주 월요일에 지난주 학습 성과와 이번주 예정 복습에 대한 요약을 받습니다.
                  </p>
                </div>
              </div>

              <div className="ml-7 space-y-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  요약 발송 시간
                </label>
                <select
                  value={weeklyHour}
                  onChange={(e) => {
                    const hour = parseInt(e.target.value);
                    setWeeklyHour(hour);
                    notificationForm.setValue('weekly_summary_time', formatTime(hour));
                  }}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm shadow-sm min-w-32"
                >
                  {hourOptions.map(hour => (
                    <option key={hour} value={hour}>
                      {getTimeLabel(hour)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              type="submit"
              disabled={notificationMutation.isPending}
              className="inline-flex items-center gap-2 px-6 py-3 border border-transparent text-sm font-semibold rounded-xl shadow-md text-white bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {notificationMutation.isPending ? (
                <>
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  저장 중...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  설정 저장
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NotificationTab;