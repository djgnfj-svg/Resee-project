import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authAPI } from '../utils/api';

export interface NotificationSettings {
  email_notifications_enabled: boolean;
  daily_reminder_enabled: boolean;
  daily_reminder_time: string;
  evening_reminder_enabled: boolean;
  evening_reminder_time: string;
  weekly_summary_enabled: boolean;
  weekly_summary_day: number;
  weekly_summary_time: string;
}

// 시간을 문자열로 포맷 (시간 단위만, 분/초는 00으로 고정)
export const formatTime = (hour: number): string => {
  return `${hour.toString().padStart(2, '0')}:00:00`;
};

// 시간대별 추천 시간 옵션
export const getTimeLabel = (hour: number): string => {
  if (hour >= 6 && hour <= 11) return `${hour}시 (오전)`;
  if (hour >= 12 && hour <= 17) return `${hour}시 (오후)`;
  if (hour >= 18 && hour <= 23) return `${hour}시 (저녁)`;
  return `${hour}시 (새벽)`;
};

// 시간 옵션 생성 (0-23)
export const hourOptions = Array.from({ length: 24 }, (_, i) => i);

export const useNotificationSettings = () => {
  const queryClient = useQueryClient();
  const [dailyHour, setDailyHour] = useState(9);
  const [eveningHour, setEveningHour] = useState(20);
  const [weeklyHour, setWeeklyHour] = useState(9);

  // Fetch current notification preferences
  const { data: notificationPreferences, isLoading: preferencesLoading } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: () => authAPI.getNotificationPreferences(),
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

  // Notification settings update mutation
  const notificationMutation = useMutation({
    mutationFn: (data: NotificationSettings) => authAPI.updateNotificationPreferences(data),
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

  return {
    notificationForm,
    notificationMutation,
    preferencesLoading,
    dailyHour,
    setDailyHour,
    eveningHour,
    setEveningHour,
    weeklyHour,
    setWeeklyHour,
    onNotificationSubmit,
  };
};
