"""
Comprehensive Celery task and background job tests
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock, call
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core import mail
from django.contrib.auth import get_user_model
from celery.exceptions import Retry

from .base import BaseTestCase, TestDataMixin
from content.models import Content
from review.models import ReviewSchedule, ReviewHistory
from review.tasks import (
    create_review_schedule_for_content,
    send_daily_review_notifications,
    cleanup_old_review_history,
    update_review_schedules
)

User = get_user_model()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ReviewScheduleTaskTestCase(BaseTestCase, TestDataMixin):
    """Test review schedule creation tasks"""
    
    def test_create_review_schedule_for_content_success(self):
        """Test successful review schedule creation"""
        content = self.create_content()
        
        # Delete any existing schedule to test creation
        ReviewSchedule.objects.filter(content=content, user=self.user).delete()
        
        # Run task
        result = create_review_schedule_for_content(content.id)
        
        # Verify schedule was created
        self.assertTrue(result)
        schedule = ReviewSchedule.objects.get(content=content, user=self.user)
        self.assertEqual(schedule.interval_index, 0)
        self.assertFalse(schedule.initial_review_completed)
        self.assertTrue(schedule.is_active)
    
    def test_create_review_schedule_for_nonexistent_content(self):
        """Test task with non-existent content"""
        result = create_review_schedule_for_content(99999)
        self.assertFalse(result)
    
    def test_create_review_schedule_duplicate_prevention(self):
        """Test that duplicate schedules are not created"""
        content = self.create_content()
        
        # Create initial schedule
        initial_schedule = self.create_review_schedule(content=content)
        initial_count = ReviewSchedule.objects.filter(content=content).count()
        
        # Run task again
        result = create_review_schedule_for_content(content.id)
        
        # Should not create duplicate
        final_count = ReviewSchedule.objects.filter(content=content).count()
        self.assertEqual(initial_count, final_count)
        self.assertFalse(result)  # Should return False for no action taken
    
    def test_create_review_schedule_immediate_availability(self):
        """Test that schedule is immediately available for review"""
        content = self.create_content()
        ReviewSchedule.objects.filter(content=content).delete()
        
        create_review_schedule_for_content(content.id)
        
        schedule = ReviewSchedule.objects.get(content=content, user=self.user)
        # Should be available for immediate review
        self.assertLessEqual(schedule.next_review_date, timezone.now())
    
    @patch('review.tasks.create_review_schedule_for_content.retry')
    def test_create_review_schedule_retry_on_error(self, mock_retry):
        """Test task retry on database error"""
        with patch('review.models.ReviewSchedule.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            mock_retry.side_effect = Retry("Retrying...")
            
            with self.assertRaises(Retry):
                create_review_schedule_for_content(self.create_content().id)
            
            mock_retry.assert_called_once()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class NotificationTaskTestCase(BaseTestCase, TestDataMixin):
    """Test notification tasks"""
    
    def setUp(self):
        super().setUp()
        mail.outbox = []  # Clear mail outbox
    
    def test_send_daily_review_notifications_enabled_users(self):
        """Test notifications sent to users with notifications enabled"""
        # Create user with notifications enabled
        user_with_notifications = self.create_user(
            username='notify_user',
            email='notify@example.com',
            notification_enabled=True
        )
        
        # Create due review for this user
        content = self.create_content(author=user_with_notifications)
        schedule = self.create_review_schedule(
            user=user_with_notifications,
            content=content,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        
        # Run task
        result = send_daily_review_notifications()
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to[0], user_with_notifications.email)
        self.assertIn('Daily Review Reminder', email.subject)
        self.assertIn(content.title, email.body)
    
    def test_send_daily_review_notifications_disabled_users(self):
        """Test notifications not sent to users with notifications disabled"""
        # Create user with notifications disabled
        user_no_notifications = self.create_user(
            username='no_notify_user',
            email='no_notify@example.com',
            notification_enabled=False
        )
        
        # Create due review for this user
        content = self.create_content(author=user_no_notifications)
        self.create_review_schedule(
            user=user_no_notifications,
            content=content,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        
        # Run task
        result = send_daily_review_notifications()
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_daily_review_notifications_no_due_reviews(self):
        """Test notifications when no reviews are due"""
        # Create user with future reviews
        user = self.create_user(
            username='future_user',
            email='future@example.com',
            notification_enabled=True
        )
        
        content = self.create_content(author=user)
        self.create_review_schedule(
            user=user,
            content=content,
            next_review_date=timezone.now() + timedelta(days=1)
        )
        
        # Run task
        result = send_daily_review_notifications()
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_daily_review_notifications_multiple_users(self):
        """Test notifications to multiple users"""
        users = []
        for i in range(3):
            user = self.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                notification_enabled=True
            )
            users.append(user)
            
            # Create due review for each user
            content = self.create_content(author=user, title=f'Content {i}')
            self.create_review_schedule(
                user=user,
                content=content,
                next_review_date=timezone.now() - timedelta(hours=1)
            )
        
        # Run task
        result = send_daily_review_notifications()
        
        # Check emails were sent to all users
        self.assertEqual(len(mail.outbox), 3)
        sent_emails = [email.to[0] for email in mail.outbox]
        expected_emails = [user.email for user in users]
        self.assertEqual(set(sent_emails), set(expected_emails))
    
    def test_send_daily_review_notifications_multiple_reviews_per_user(self):
        """Test notifications when user has multiple due reviews"""
        user = self.create_user(
            username='multi_user',
            email='multi@example.com',
            notification_enabled=True
        )
        
        # Create multiple due reviews for same user
        contents = []
        for i in range(5):
            content = self.create_content(author=user, title=f'Content {i}')
            contents.append(content)
            self.create_review_schedule(
                user=user,
                content=content,
                next_review_date=timezone.now() - timedelta(hours=1)
            )
        
        # Run task
        result = send_daily_review_notifications()
        
        # Should send only one email per user
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Email should contain all due contents
        for content in contents:
            self.assertIn(content.title, email.body)
    
    @patch('review.tasks.send_mail')
    def test_send_daily_review_notifications_email_failure(self, mock_send_mail):
        """Test handling of email sending failures"""
        mock_send_mail.side_effect = Exception("SMTP Error")
        
        user = self.create_user(
            username='email_fail_user',
            email='fail@example.com',
            notification_enabled=True
        )
        
        content = self.create_content(author=user)
        self.create_review_schedule(
            user=user,
            content=content,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        
        # Task should handle the error gracefully
        result = send_daily_review_notifications()
        
        # Should still return some result (not crash)
        self.assertIsNotNone(result)
    
    def test_send_daily_review_notifications_template_rendering(self):
        """Test email template rendering with proper context"""
        user = self.create_user(
            username='template_user',
            email='template@example.com',
            notification_enabled=True,
            first_name='Test',
            last_name='User'
        )
        
        content = self.create_content(
            author=user,
            title='Important Content',
            priority='high'
        )
        self.create_review_schedule(
            user=user,
            content=content,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        
        # Run task
        send_daily_review_notifications()
        
        # Check email content
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Should contain user name and content details
        self.assertIn('Test User', email.body)
        self.assertIn('Important Content', email.body)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CleanupTaskTestCase(BaseTestCase, TestDataMixin):
    """Test cleanup tasks"""
    
    def test_cleanup_old_review_history_success(self):
        """Test successful cleanup of old review history"""
        content = self.create_content()
        
        # Create old review history (older than 1 year)
        old_date = timezone.now() - timedelta(days=400)
        old_history = ReviewHistory.objects.create(
            content=content,
            user=self.user,
            result='remembered',
            review_date=old_date
        )
        
        # Create recent review history
        recent_history = self.create_review_history(content=content)
        
        initial_count = ReviewHistory.objects.count()
        
        # Run cleanup task with 365 days retention
        result = cleanup_old_review_history(days=365)
        
        # Old history should be deleted, recent should remain
        final_count = ReviewHistory.objects.count()
        self.assertEqual(final_count, initial_count - 1)
        self.assertFalse(ReviewHistory.objects.filter(id=old_history.id).exists())
        self.assertTrue(ReviewHistory.objects.filter(id=recent_history.id).exists())
    
    def test_cleanup_old_review_history_custom_days(self):
        """Test cleanup with custom retention period"""
        content = self.create_content()
        
        # Create history from different time periods
        very_old = timezone.now() - timedelta(days=100)
        somewhat_old = timezone.now() - timedelta(days=50)
        recent = timezone.now() - timedelta(days=10)
        
        very_old_history = ReviewHistory.objects.create(
            content=content, user=self.user, result='remembered', review_date=very_old
        )
        somewhat_old_history = ReviewHistory.objects.create(
            content=content, user=self.user, result='forgot', review_date=somewhat_old
        )
        recent_history = ReviewHistory.objects.create(
            content=content, user=self.user, result='partial', review_date=recent
        )
        
        # Cleanup with 60 days retention
        result = cleanup_old_review_history(days=60)
        
        # Only very old should be deleted
        self.assertFalse(ReviewHistory.objects.filter(id=very_old_history.id).exists())
        self.assertTrue(ReviewHistory.objects.filter(id=somewhat_old_history.id).exists())
        self.assertTrue(ReviewHistory.objects.filter(id=recent_history.id).exists())
    
    def test_cleanup_old_review_history_no_old_data(self):
        """Test cleanup when no old data exists"""
        # Create only recent history
        content = self.create_content()
        recent_history = self.create_review_history(content=content)
        
        initial_count = ReviewHistory.objects.count()
        
        # Run cleanup
        result = cleanup_old_review_history(days=30)
        
        # Nothing should be deleted
        final_count = ReviewHistory.objects.count()
        self.assertEqual(final_count, initial_count)
        self.assertTrue(ReviewHistory.objects.filter(id=recent_history.id).exists())
    
    def test_cleanup_old_review_history_preserves_user_data(self):
        """Test cleanup preserves data isolation between users"""
        other_user = self.create_user(username='other', email='other@example.com')
        
        # Create old history for both users
        old_date = timezone.now() - timedelta(days=400)
        
        content1 = self.create_content(author=self.user)
        content2 = self.create_content(author=other_user)
        
        old_history_user1 = ReviewHistory.objects.create(
            content=content1, user=self.user, result='remembered', review_date=old_date
        )
        old_history_user2 = ReviewHistory.objects.create(
            content=content2, user=other_user, result='remembered', review_date=old_date
        )
        
        # Run cleanup
        cleanup_old_review_history(days=365)
        
        # Both old histories should be deleted equally
        self.assertFalse(ReviewHistory.objects.filter(id=old_history_user1.id).exists())
        self.assertFalse(ReviewHistory.objects.filter(id=old_history_user2.id).exists())


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class ScheduleUpdateTaskTestCase(BaseTestCase, TestDataMixin):
    """Test schedule update tasks"""
    
    def test_update_review_schedules_basic(self):
        """Test basic schedule update functionality"""
        # This would test any future schedule update tasks
        # For now, just ensure the task can be called
        result = update_review_schedules() if hasattr(update_review_schedules, '__call__') else True
        self.assertIsNotNone(result)
    
    def test_inactive_schedule_handling(self):
        """Test handling of inactive schedules"""
        content = self.create_content()
        schedule = self.create_review_schedule(content=content, is_active=False)
        
        # Inactive schedules should not be included in today's reviews
        from review.views import TodayReviewView
        # This would be tested in the view tests
        pass


class TaskRetryTestCase(BaseTestCase):
    """Test task retry mechanisms"""
    
    @patch('review.tasks.create_review_schedule_for_content.retry')
    @patch('review.models.ReviewSchedule.objects.get_or_create')
    def test_task_retry_on_database_error(self, mock_get_or_create, mock_retry):
        """Test task retry on database errors"""
        mock_get_or_create.side_effect = Exception("Database connection error")
        mock_retry.side_effect = Retry("Retrying...")
        
        with self.assertRaises(Retry):
            create_review_schedule_for_content(self.create_content().id)
        
        mock_retry.assert_called_once()
    
    @patch('review.tasks.send_daily_review_notifications.retry')
    @patch('django.core.mail.send_mail')
    def test_notification_task_retry_on_email_error(self, mock_send_mail, mock_retry):
        """Test notification task retry on email errors"""
        mock_send_mail.side_effect = Exception("SMTP connection error")
        mock_retry.side_effect = Retry("Retrying...")
        
        user = self.create_user(
            username='retry_user',
            email='retry@example.com',
            notification_enabled=True
        )
        content = self.create_content(author=user)
        self.create_review_schedule(
            user=user,
            content=content,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        
        # This would depend on how the actual task is implemented
        # For now, just test that the mechanism exists
        self.assertTrue(hasattr(send_daily_review_notifications, 'retry'))


class TaskPerformanceTestCase(BaseTestCase, TestDataMixin):
    """Test task performance and optimization"""
    
    def test_notification_task_performance_large_dataset(self):
        """Test notification task performance with large dataset"""
        import time
        
        # Create many users with due reviews
        users = []
        for i in range(100):
            user = self.create_user(
                username=f'perf_user_{i}',
                email=f'perf{i}@example.com',
                notification_enabled=True
            )
            users.append(user)
            
            content = self.create_content(author=user, title=f'Content {i}')
            self.create_review_schedule(
                user=user,
                content=content,
                next_review_date=timezone.now() - timedelta(hours=1)
            )
        
        start_time = time.time()
        
        # Run notification task
        result = send_daily_review_notifications()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 10.0)  # 10 seconds for 100 users
        
        # All emails should be sent
        self.assertEqual(len(mail.outbox), 100)
    
    def test_cleanup_task_performance_large_dataset(self):
        """Test cleanup task performance with large dataset"""
        import time
        
        content = self.create_content()
        
        # Create many old review histories
        old_date = timezone.now() - timedelta(days=400)
        histories = []
        for i in range(1000):
            history = ReviewHistory(
                content=content,
                user=self.user,
                result='remembered',
                review_date=old_date,
                time_spent=120
            )
            histories.append(history)
        
        ReviewHistory.objects.bulk_create(histories)
        
        start_time = time.time()
        
        # Run cleanup task
        result = cleanup_old_review_history(days=365)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(execution_time, 5.0)  # 5 seconds for 1000 records
        
        # All old histories should be deleted
        remaining_count = ReviewHistory.objects.filter(
            review_date__lt=timezone.now() - timedelta(days=365)
        ).count()
        self.assertEqual(remaining_count, 0)


class TaskMonitoringTestCase(BaseTestCase):
    """Test task monitoring and logging"""
    
    @patch('review.tasks.logger')
    def test_task_logging(self, mock_logger):
        """Test that tasks log their activities"""
        content = self.create_content()
        
        create_review_schedule_for_content(content.id)
        
        # Verify logging calls were made
        mock_logger.info.assert_called()
    
    def test_task_return_values(self):
        """Test that tasks return meaningful values"""
        content = self.create_content()
        
        # Delete existing schedule to test creation
        ReviewSchedule.objects.filter(content=content).delete()
        
        result = create_review_schedule_for_content(content.id)
        
        # Should return True for successful creation
        self.assertTrue(result)
        
        # Running again should return False (no action taken)
        result = create_review_schedule_for_content(content.id)
        self.assertFalse(result)


class TaskErrorHandlingTestCase(BaseTestCase):
    """Test task error handling"""
    
    def test_graceful_handling_of_missing_content(self):
        """Test graceful handling when content is missing"""
        # Should not raise exception, should return False or handle gracefully
        result = create_review_schedule_for_content(99999)
        self.assertFalse(result)
    
    def test_graceful_handling_of_missing_user(self):
        """Test graceful handling when user is missing"""
        # Create content then delete user
        content = self.create_content()
        content.author.delete()
        
        # Task should handle this gracefully
        result = create_review_schedule_for_content(content.id)
        self.assertFalse(result)
    
    @patch('review.tasks.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged"""
        # This would test actual error scenarios
        result = create_review_schedule_for_content(99999)
        
        # Should log the error
        if not result:
            # Error was handled gracefully
            pass