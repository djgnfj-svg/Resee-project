import React from 'react';
import { useNotificationSettings } from '../../hooks/useNotificationSettings';
import NotificationToggle from './NotificationToggle';
import TimeSelector from './TimeSelector';

const NotificationTab: React.FC = () => {
  const {
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
  } = useNotificationSettings();

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
          <NotificationToggle
            id="email_notifications_enabled"
            label="이메일 알림 활성화"
            description="모든 이메일 알림을 받으려면 이 옵션을 활성화하세요."
            register={notificationForm.register}
            fieldName="email_notifications_enabled"
            highlighted
          />

          <div className="space-y-6">
            {/* 일일 복습 알림 */}
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg space-y-4">
              <NotificationToggle
                id="daily_reminder_enabled"
                label="일일 복습 알림"
                description="매일 지정한 시간에 오늘 복습할 콘텐츠가 있으면 알림을 받습니다."
                register={notificationForm.register}
                fieldName="daily_reminder_enabled"
              />
              <TimeSelector
                label="알림 시간"
                hour={dailyHour}
                onChange={setDailyHour}
                setValue={notificationForm.setValue}
                fieldName="daily_reminder_time"
              />
            </div>

            {/* 저녁 리마인더 */}
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg space-y-4">
              <NotificationToggle
                id="evening_reminder_enabled"
                label="저녁 리마인더"
                description="아직 완료하지 못한 오늘의 복습이 있을 때 저녁에 한 번 더 알림을 받습니다."
                register={notificationForm.register}
                fieldName="evening_reminder_enabled"
              />
              <TimeSelector
                label="리마인더 시간"
                hour={eveningHour}
                onChange={setEveningHour}
                setValue={notificationForm.setValue}
                fieldName="evening_reminder_time"
              />
            </div>

            {/* 주간 요약 */}
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg space-y-4">
              <NotificationToggle
                id="weekly_summary_enabled"
                label="주간 학습 요약"
                description="매주 월요일에 지난주 학습 성과와 이번주 예정 복습에 대한 요약을 받습니다."
                register={notificationForm.register}
                fieldName="weekly_summary_enabled"
              />
              <TimeSelector
                label="요약 발송 시간"
                hour={weeklyHour}
                onChange={setWeeklyHour}
                setValue={notificationForm.setValue}
                fieldName="weekly_summary_time"
              />
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