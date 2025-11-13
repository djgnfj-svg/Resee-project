"""
Review notification services
알림 관련 비즈니스 로직을 캡슐화하는 서비스 클래스들
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import NotificationPreference
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()
logger = logging.getLogger(__name__)


class ReviewNotificationService:
    """복습 알림 관련 비즈니스 로직을 담당하는 서비스 클래스"""

    @staticmethod
    def get_users_for_daily_reminder(target_date: Optional[datetime] = None) -> List[Dict]:
        """
        일일 복습 알림을 받을 사용자들과 그들의 복습 스케줄을 조회

        Args:
            target_date: 대상 날짜 (기본값: 오늘)

        Returns:
            List[Dict]: 사용자와 스케줄 정보가 담긴 딕셔너리 리스트
        """
        if target_date is None:
            target_date = timezone.now().date()

        # 오늘 복습 예정이고 알림을 활성화한 사용자들 조회
        schedules_today = ReviewSchedule.objects.filter(
            next_review_date__date=target_date,
            is_active=True,
            user__notification_preference__email_notifications_enabled=True,
            user__notification_preference__daily_reminder_enabled=True
        ).select_related(
            'user', 'content', 'user__notification_preference'
        ).prefetch_related('content__category')

        # 사용자별로 그룹화
        user_schedules = {}
        for schedule in schedules_today:
            user_id = schedule.user.id
            if user_id not in user_schedules:
                user_schedules[user_id] = {
                    'user': schedule.user,
                    'schedules': []
                }
            user_schedules[user_id]['schedules'].append(schedule)

        return list(user_schedules.values())

    @staticmethod
    def get_users_for_evening_reminder(target_date: Optional[datetime] = None) -> List[Dict]:
        """
        저녁 리마인더를 받을 사용자들과 미완료 스케줄을 조회

        Args:
            target_date: 대상 날짜 (기본값: 오늘)

        Returns:
            List[Dict]: 사용자와 미완료 스케줄 정보가 담긴 딕셔너리 리스트
        """
        if target_date is None:
            target_date = timezone.now().date()

        # 오늘 복습 예정이었지만 아직 완료하지 않은 스케줄들
        pending_schedules = ReviewSchedule.objects.filter(
            next_review_date__date=target_date,
            is_active=True,
            user__notification_preference__email_notifications_enabled=True,
            user__notification_preference__evening_reminder_enabled=True
        ).select_related(
            'user', 'content', 'user__notification_preference'
        ).prefetch_related('content__category')

        # 오늘 이미 복습 완료한 콘텐츠 확인
        today_completed_content_ids = ReviewHistory.objects.filter(
            reviewed_at__date=target_date
        ).values_list('schedule__content_id', flat=True)

        # 아직 완료하지 않은 스케줄만 필터링
        pending_schedules = pending_schedules.exclude(
            content_id__in=today_completed_content_ids
        )

        # 사용자별로 그룹화
        user_schedules = {}
        for schedule in pending_schedules:
            user_id = schedule.user.id
            if user_id not in user_schedules:
                user_schedules[user_id] = {
                    'user': schedule.user,
                    'schedules': []
                }
            user_schedules[user_id]['schedules'].append(schedule)

        return list(user_schedules.values())


class NotificationPreferenceService:
    """알림 설정 관리 서비스"""

    @staticmethod
    def update_notification_preferences(user: User, preferences: Dict) -> NotificationPreference:
        """
        사용자의 알림 설정을 업데이트

        Args:
            user: 사용자 객체
            preferences: 업데이트할 설정 딕셔너리

        Returns:
            NotificationPreference: 업데이트된 알림 설정 객체
        """
        notification_pref, created = NotificationPreference.objects.get_or_create(user=user)

        # 업데이트 가능한 필드들
        updatable_fields = [
            'email_notifications_enabled',
            'daily_reminder_enabled',
            'daily_reminder_time',
            'evening_reminder_enabled',
            'evening_reminder_time',
            'weekly_summary_enabled',
            'weekly_summary_day',
            'weekly_summary_time'
        ]

        for field in updatable_fields:
            if field in preferences:
                setattr(notification_pref, field, preferences[field])

        notification_pref.save()
        logger.info(f"Updated notification preferences for user {user.email}")
        return notification_pref

    @staticmethod
    def unsubscribe_user(token: str) -> Tuple[bool, str]:
        """
        구독 해지 토큰을 사용하여 사용자의 이메일 알림을 비활성화

        Args:
            token: 구독 해지 토큰

        Returns:
            Tuple[bool, str]: (성공 여부, 메시지)
        """
        try:
            notification_pref = NotificationPreference.objects.get(unsubscribe_token=token)
            notification_pref.email_notifications_enabled = False
            notification_pref.save()

            logger.info(f"User {notification_pref.user.email} unsubscribed via token")
            return True, f"이메일 알림이 성공적으로 해지되었습니다."

        except NotificationPreference.DoesNotExist:
            logger.warning(f"Invalid unsubscribe token: {token}")
            return False, "유효하지 않은 구독 해지 링크입니다."
        except Exception as e:
            logger.error(f"Error during unsubscribe: {str(e)}")
            return False, "구독 해지 처리 중 오류가 발생했습니다."

    @staticmethod
    def get_notification_statistics() -> Dict:
        """
        알림 시스템 전체 통계 조회

        Returns:
            Dict: 알림 관련 통계 정보
        """
        total_users = User.objects.count()

        notification_prefs = NotificationPreference.objects.aggregate(
            email_enabled=Count('id', filter=Q(email_notifications_enabled=True)),
            daily_enabled=Count('id', filter=Q(daily_reminder_enabled=True)),
            evening_enabled=Count('id', filter=Q(evening_reminder_enabled=True)),
            weekly_enabled=Count('id', filter=Q(weekly_summary_enabled=True))
        )

        return {
            'total_users': total_users,
            'email_notifications_enabled': notification_prefs['email_enabled'],
            'daily_reminders_enabled': notification_prefs['daily_enabled'],
            'evening_reminders_enabled': notification_prefs['evening_enabled'],
            'weekly_summaries_enabled': notification_prefs['weekly_enabled'],
            'email_notification_rate': round(
                (notification_prefs['email_enabled'] / total_users * 100) if total_users > 0 else 0, 1
            )
        }