"""
Review notification tasks using Celery
"""
import logging
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from accounts.email.email_service import EmailService
from accounts.models import NotificationPreference
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_daily_review_reminders(self):
    """
    매일 오전 9시에 실행되는 복습 알림 태스크
    오늘 복습 예정인 사용자들에게 이메일 발송
    """
    try:
        today = timezone.now().date()

        # 오늘 복습 예정이고 알림을 활성화한 사용자들 조회
        schedules_today = ReviewSchedule.objects.filter(
            next_review_date__date=today,
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

        sent_count = 0
        failed_count = 0

        # 각 사용자에게 개별 이메일 발송
        for user_data in user_schedules.values():
            try:
                # 개별 이메일 발송 태스크 큐잉
                send_individual_review_reminder.delay(
                    user_data['user'].id,
                    [s.id for s in user_data['schedules']]
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue email for user {user_data['user'].email}: {str(e)}")
                failed_count += 1

        result_message = f"Daily reminders queued: {sent_count} sent, {failed_count} failed"
        logger.info(result_message)
        return result_message

    except Exception as exc:
        logger.error(f"Error in send_daily_review_reminders: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_individual_review_reminder(self, user_id: int, schedule_ids: List[int]):
    """
    개별 사용자에게 복습 알림 이메일 발송

    Args:
        user_id: 사용자 ID
        schedule_ids: 복습 스케줄 ID 목록
    """
    try:
        user = User.objects.get(id=user_id)
        schedules = ReviewSchedule.objects.filter(
            id__in=schedule_ids,
            user=user
        ).select_related('content').prefetch_related('content__category')

        if not schedules.exists():
            logger.warning(f"No schedules found for user {user.email}")
            return f"No schedules found for user {user.email}"

        # 이메일 컨텍스트 준비
        context = {
            'user': user,
            'schedules': schedules,
            'total_reviews': schedules.count(),
            'review_url': f"{settings.FRONTEND_URL}/review",
            'unsubscribe_url': user.notification_preference.generate_unsubscribe_url(),
            'company_name': getattr(settings, 'COMPANY_NAME', 'Resee'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@resee.com'),
        }

        # 이메일 제목
        if schedules.count() == 1:
            subject = f"[{context['company_name']}] 오늘 복습할 콘텐츠가 1개 있습니다"
        else:
            subject = f"[{context['company_name']}] 오늘 복습할 콘텐츠가 {schedules.count()}개 있습니다"

        # 이메일 발송
        email_service = EmailService()
        success = email_service.send_template_email(
            template_name='daily_review_notification',
            context=context,
            subject=subject,
            recipient_email=user.email
        )

        if success:
            result_message = f"Review reminder sent to {user.email} for {schedules.count()} items"
            logger.info(result_message)
            return result_message
        else:
            raise Exception("Email sending failed")

    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return f"User with id {user_id} does not exist"
    except Exception as exc:
        logger.error(f"Error sending reminder to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_evening_review_reminders(self):
    """
    매일 오후 8시에 실행되는 저녁 리마인더
    아직 완료하지 못한 오늘의 복습이 있는 사용자들에게 알림
    """
    try:
        today = timezone.now().date()

        # 오늘 복습 예정이었지만 아직 완료하지 않은 스케줄들
        pending_schedules = ReviewSchedule.objects.filter(
            next_review_date__date=today,
            is_active=True,
            user__notification_preference__email_notifications_enabled=True,
            user__notification_preference__evening_reminder_enabled=True
        ).select_related(
            'user', 'content', 'user__notification_preference'
        ).prefetch_related('content__category')

        # 오늘 이미 복습 완료한 콘텐츠 확인
        today_completed_content_ids = ReviewHistory.objects.filter(
            reviewed_at__date=today
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
                user_schedules[user_id] = []
            user_schedules[user_id].append(schedule)

        sent_count = 0
        failed_count = 0

        # 각 사용자에게 저녁 리마인더 발송
        for user_id, schedules in user_schedules.items():
            try:
                send_individual_evening_reminder.delay(
                    user_id,
                    [s.id for s in schedules]
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue evening reminder for user {user_id}: {str(e)}")
                failed_count += 1

        result_message = f"Evening reminders queued: {sent_count} sent, {failed_count} failed"
        logger.info(result_message)
        return result_message

    except Exception as exc:
        logger.error(f"Error in send_evening_review_reminders: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_individual_evening_reminder(self, user_id: int, schedule_ids: List[int]):
    """
    개별 사용자에게 저녁 리마인더 이메일 발송
    """
    try:
        user = User.objects.get(id=user_id)
        schedules = ReviewSchedule.objects.filter(
            id__in=schedule_ids,
            user=user
        ).select_related('content').prefetch_related('content__category')

        if not schedules.exists():
            return f"No pending schedules for user {user.email}"

        # 이메일 컨텍스트 준비
        context = {
            'user': user,
            'schedules': schedules,
            'total_reviews': schedules.count(),
            'review_url': f"{settings.FRONTEND_URL}/review",
            'unsubscribe_url': user.notification_preference.generate_unsubscribe_url(),
            'company_name': getattr(settings, 'COMPANY_NAME', 'Resee'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@resee.com'),
            'is_evening_reminder': True,
        }

        # 이메일 제목
        subject = f"[{context['company_name']}] 오늘의 복습을 잊지 마세요! ({schedules.count()}개 남음)"

        # 이메일 발송
        email_service = EmailService()
        success = email_service.send_template_email(
            template_name='daily_review_notification',  # 같은 템플릿 사용, is_evening_reminder로 구분
            context=context,
            subject=subject,
            recipient_email=user.email
        )

        if success:
            result_message = f"Evening reminder sent to {user.email} for {schedules.count()} items"
            logger.info(result_message)
            return result_message
        else:
            raise Exception("Email sending failed")

    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return f"User with id {user_id} does not exist"
    except Exception as exc:
        logger.error(f"Error sending evening reminder to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_weekly_summary(self):
    """
    주간 요약 이메일 발송 (매주 월요일 오전 9시)
    지난주 성과와 이번주 예정 복습에 대한 요약
    """
    try:
        # 지난주 기간 계산
        today = timezone.now().date()
        last_week_end = today - timedelta(days=today.weekday() + 1)  # 지난주 일요일
        last_week_start = last_week_end - timedelta(days=6)  # 지난주 월요일

        # 이번주 기간 계산
        this_week_start = today
        this_week_end = today + timedelta(days=6)

        # 주간 요약을 받을 사용자들
        users_for_summary = User.objects.filter(
            notification_preference__email_notifications_enabled=True,
            notification_preference__weekly_summary_enabled=True
        ).select_related('notification_preference')

        sent_count = 0
        failed_count = 0

        for user in users_for_summary:
            try:
                send_individual_weekly_summary.delay(
                    user.id,
                    last_week_start.isoformat(),
                    last_week_end.isoformat(),
                    this_week_start.isoformat(),
                    this_week_end.isoformat()
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue weekly summary for user {user.email}: {str(e)}")
                failed_count += 1

        result_message = f"Weekly summaries queued: {sent_count} sent, {failed_count} failed"
        logger.info(result_message)
        return result_message

    except Exception as exc:
        logger.error(f"Error in send_weekly_summary: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_individual_weekly_summary(self, user_id: int, last_week_start: str, last_week_end: str,
                                 this_week_start: str, this_week_end: str):
    """개별 사용자 주간 요약 이메일 발송"""
    try:
        from datetime import datetime
        user = User.objects.get(id=user_id)

        last_week_start_date = datetime.fromisoformat(last_week_start).date()
        last_week_end_date = datetime.fromisoformat(last_week_end).date()
        this_week_start_date = datetime.fromisoformat(this_week_start).date()
        this_week_end_date = datetime.fromisoformat(this_week_end).date()

        # 지난주 복습 통계
        last_week_reviews = ReviewHistory.objects.filter(
            schedule__user=user,
            reviewed_at__date__range=[last_week_start_date, last_week_end_date]
        )

        last_week_total = last_week_reviews.count()
        last_week_success = last_week_reviews.filter(success=True).count()
        last_week_success_rate = (last_week_success / last_week_total * 100) if last_week_total > 0 else 0

        # 이번주 예정 복습
        this_week_schedules = ReviewSchedule.objects.filter(
            user=user,
            next_review_date__date__range=[this_week_start_date, this_week_end_date],
            is_active=True
        ).select_related('content').prefetch_related('content__category')

        # 이메일 컨텍스트
        context = {
            'user': user,
            'last_week_total': last_week_total,
            'last_week_success': last_week_success,
            'last_week_success_rate': round(last_week_success_rate, 1),
            'this_week_schedules': this_week_schedules,
            'this_week_total': this_week_schedules.count(),
            'review_url': f"{settings.FRONTEND_URL}/review",
            'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
            'unsubscribe_url': user.notification_preference.generate_unsubscribe_url(),
            'company_name': getattr(settings, 'COMPANY_NAME', 'Resee'),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@resee.com'),
        }

        subject = f"[{context['company_name']}] 주간 학습 요약 - 지난주 {last_week_success}/{last_week_total}개 완료"

        # 주간 요약 템플릿이 없으면 기본 템플릿 사용
        template_name = 'weekly_summary'

        email_service = EmailService()
        success = email_service.send_template_email(
            template_name=template_name,
            context=context,
            subject=subject,
            recipient_email=user.email
        )

        if success:
            result_message = f"Weekly summary sent to {user.email}"
            logger.info(result_message)
            return result_message
        else:
            raise Exception("Email sending failed")

    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return f"User with id {user_id} does not exist"
    except Exception as exc:
        logger.error(f"Error sending weekly summary to user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)