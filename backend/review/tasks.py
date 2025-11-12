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
def send_hourly_notifications(self):
    """
    매시간 0분에 실행되는 통합 알림 태스크
    현재 시간에 맞춰 사용자별 설정된 시간에 알림 발송
    """
    try:
        current_time = timezone.now()
        current_hour = current_time.hour
        current_weekday = current_time.weekday()  # 0=월요일, 6=일요일

        logger.info(f"시간별 알림 처리 시작 - 현재 시간: {current_hour}시")

        # 1. 일일 복습 알림 처리
        daily_count = send_daily_reminders_for_hour(current_hour)

        # 2. 저녁 알림 처리
        evening_count = send_evening_reminders_for_hour(current_hour)

        # 3. 주간 요약 처리 (월요일에만)
        weekly_count = 0
        if current_weekday == 0:  # 월요일
            weekly_count = send_weekly_summaries_for_hour(current_hour)

        result_message = f"시간별 알림 완료 - 일일: {daily_count}, 저녁: {evening_count}, 주간: {weekly_count}"
        logger.info(result_message)
        return result_message

    except Exception as exc:
        logger.error(f"Error in send_hourly_notifications: {str(exc)}")
        raise self.retry(exc=exc)


def send_daily_reminders_for_hour(hour: int):
    """지정된 시간에 일일 복습 알림을 받을 사용자들에게 발송"""
    try:
        today = timezone.now().date()

        # 해당 시간에 일일 알림을 받을 사용자들 조회
        schedules_today = ReviewSchedule.objects.filter(
            next_review_date__date=today,
            is_active=True,
            user__notification_preference__email_notifications_enabled=True,
            user__notification_preference__daily_reminder_enabled=True,
            user__notification_preference__daily_reminder_time__hour=hour
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
        # 각 사용자에게 개별 이메일 발송
        for user_data in user_schedules.values():
            try:
                send_individual_review_reminder.delay(
                    user_data['user'].id,
                    [s.id for s in user_data['schedules']]
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to queue daily reminder for user {user_data['user'].email}: {str(e)}")

        if sent_count > 0:
            logger.info(f"일일 알림 {sent_count}개 큐잉 완료 - {hour}시")
        return sent_count

    except Exception as e:
        logger.error(f"Error in send_daily_reminders_for_hour({hour}): {str(e)}")
        return 0


def send_evening_reminders_for_hour(hour: int):
    """지정된 시간에 저녁 알림을 받을 사용자들에게 발송"""
    try:
        today = timezone.now().date()

        # 해당 시간에 저녁 알림을 받을 사용자들의 미완료 스케줄 조회
        pending_schedules = ReviewSchedule.objects.filter(
            next_review_date__date=today,
            is_active=True,
            user__notification_preference__email_notifications_enabled=True,
            user__notification_preference__evening_reminder_enabled=True,
            user__notification_preference__evening_reminder_time__hour=hour
        ).select_related(
            'user', 'content', 'user__notification_preference'
        ).prefetch_related('content__category')

        # 오늘 이미 복습 완료한 콘텐츠 확인
        today_completed_content_ids = ReviewHistory.objects.filter(
            review_date__date=today
        ).values_list('content_id', flat=True)

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

        if sent_count > 0:
            logger.info(f"저녁 알림 {sent_count}개 큐잉 완료 - {hour}시")
        return sent_count

    except Exception as e:
        logger.error(f"Error in send_evening_reminders_for_hour({hour}): {str(e)}")
        return 0


def send_weekly_summaries_for_hour(hour: int):
    """지정된 시간에 주간 요약을 받을 사용자들에게 발송 (월요일만)"""
    try:
        # 해당 시간에 주간 요약을 받을 사용자들
        users_for_summary = User.objects.filter(
            notification_preference__email_notifications_enabled=True,
            notification_preference__weekly_summary_enabled=True,
            notification_preference__weekly_summary_time__hour=hour
        ).select_related('notification_preference')

        # 지난주/이번주 기간 계산
        today = timezone.now().date()
        last_week_end = today - timedelta(days=today.weekday() + 1)
        last_week_start = last_week_end - timedelta(days=6)
        this_week_start = today
        this_week_end = today + timedelta(days=6)

        sent_count = 0
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

        if sent_count > 0:
            logger.info(f"주간 요약 {sent_count}개 큐잉 완료 - {hour}시")
        return sent_count

    except Exception as e:
        logger.error(f"Error in send_weekly_summaries_for_hour({hour}): {str(e)}")
        return 0


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
            user=user,
            review_date__date__range=[last_week_start_date, last_week_end_date]
        )

        last_week_total = last_week_reviews.count()
        last_week_success = last_week_reviews.filter(result='remembered').count()
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


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def adjust_review_schedules_on_subscription_change(self, subscription_id: int):
    """
    Adjust review schedules when subscription tier changes.

    This task is triggered asynchronously when a subscription is updated
    to prevent blocking the API response.

    Args:
        subscription_id: ID of the subscription that was changed
    """
    try:
        from accounts.models import Subscription
        from review.utils import get_review_intervals

        subscription = Subscription.objects.select_related('user').get(id=subscription_id)
        user = subscription.user

        # Get new intervals for the updated subscription
        new_intervals = get_review_intervals(user)
        new_max_interval = subscription.max_interval_days

        # Get all active review schedules for this user
        schedules = ReviewSchedule.objects.filter(
            user=user,
            is_active=True
        )

        adjusted_count = 0
        for schedule in schedules:
            schedule_changed = False

            # Check if current interval_index exceeds new tier limits
            if schedule.interval_index >= len(new_intervals):
                schedule.interval_index = len(new_intervals) - 1
                schedule_changed = True

            # Get the current interval for this schedule
            current_interval = new_intervals[schedule.interval_index]

            # Check if current interval exceeds new max interval
            if current_interval > new_max_interval:
                # Find the highest allowed interval
                allowed_intervals = [i for i in new_intervals if i <= new_max_interval]
                if allowed_intervals:
                    max_allowed_interval = max(allowed_intervals)
                    try:
                        schedule.interval_index = new_intervals.index(max_allowed_interval)
                        current_interval = max_allowed_interval
                        schedule_changed = True
                    except ValueError:
                        # Fallback to the last allowed interval
                        schedule.interval_index = len(allowed_intervals) - 1
                        current_interval = allowed_intervals[-1]
                        schedule_changed = True

            # If schedule was changed, update the next_review_date
            if schedule_changed:
                # Keep the review due soon if it was already due
                if schedule.next_review_date <= timezone.now():
                    # Keep it due today/now
                    pass
                else:
                    # Recalculate next review date with new interval
                    base_date = timezone.now()
                    if schedule.created_at:
                        # Calculate how far we should be from creation based on new interval
                        days_since_creation = (timezone.now() - schedule.created_at).days
                        if days_since_creation < current_interval:
                            base_date = schedule.created_at

                    schedule.next_review_date = base_date + timedelta(days=current_interval)

                schedule.save()
                adjusted_count += 1

        result_message = (
            f"Adjusted {adjusted_count} review schedules for user {user.email} "
            f"due to subscription change to {subscription.tier} (max: {new_max_interval} days)"
        )
        logger.info(result_message)
        return result_message

    except Subscription.DoesNotExist:
        logger.error(f"Subscription with id {subscription_id} does not exist")
        return f"Subscription with id {subscription_id} does not exist"
    except Exception as exc:
        logger.error(f"Error adjusting review schedules for subscription {subscription_id}: {str(exc)}")
        raise self.retry(exc=exc)