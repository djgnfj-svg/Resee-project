"""
Integration tests for complete workflows
"""

from datetime import timedelta
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseTestCase, BaseAPITestCase, TestDataMixin
from accounts.models import User
from content.models import Content, Category, Tag
from review.models import ReviewSchedule, ReviewHistory
from review.tasks import create_review_schedule_for_content, send_daily_review_notifications

User = get_user_model()


class CompleteUserWorkflowTestCase(BaseAPITestCase, TestDataMixin):
    """Test complete user workflow from registration to review completion"""
    
    def test_complete_user_journey(self):
        """Test complete user journey from registration to review completion"""
        # 1. User Registration
        self.client.credentials()  # Remove authentication
        
        registration_url = reverse('accounts:users-register')
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'timezone': 'Asia/Seoul',
            'notification_enabled': True,
        }
        
        response = self.client.post(registration_url, registration_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2. User Login
        login_url = reverse('token_obtain_pair')
        login_data = {
            'username': 'newuser',
            'password': 'newpass123',
        }
        
        response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Set authentication token
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # 3. Create Category
        category_url = reverse('content:categories-list')
        category_data = {
            'name': 'Python Learning'
        }
        
        response = self.client.post(category_url, category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data['id']
        
        # 4. Create Tag
        tag_url = reverse('content:tags-list')
        tag_data = {
            'name': 'basics'
        }
        
        response = self.client.post(tag_url, tag_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tag_id = response.data['id']
        
        # 5. Create Content
        content_url = reverse('content:contents-list')
        content_data = {
            'title': 'Python Variables',
            'content': 'Variables in Python are used to store data values.',
            'priority': 'high',
            'category': category_id,
            'tag_ids': [tag_id]
        }
        
        response = self.client.post(content_url, content_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content_id = response.data['id']
        
        # 6. Verify Review Schedule was created automatically
        schedule = ReviewSchedule.objects.get(content_id=content_id)
        self.assertEqual(schedule.interval_index, 0)
        self.assertFalse(schedule.initial_review_completed)
        
        # 7. Get Today's Reviews (should include immediate review)
        today_url = reverse('review:today')
        response = self.client.get(today_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], schedule.id)
        
        # 8. Complete Initial Review
        complete_url = reverse('review:complete')
        complete_data = {
            'schedule_id': schedule.id,
            'result': 'remembered',
            'time_spent': 120,
            'notes': 'Good initial understanding'
        }
        
        response = self.client.post(complete_url, complete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 9. Verify Schedule was updated
        schedule.refresh_from_db()
        self.assertEqual(schedule.interval_index, 1)
        self.assertTrue(schedule.initial_review_completed)
        
        # 10. Verify Review History was created
        history = ReviewHistory.objects.get(content_id=content_id)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.time_spent, 120)
        self.assertEqual(history.notes, 'Good initial understanding')
        
        # 11. Check Analytics Dashboard
        dashboard_url = reverse('analytics:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        dashboard_data = response.data
        self.assertEqual(dashboard_data['total_contents'], 1)
        self.assertEqual(dashboard_data['total_reviews'], 1)
        self.assertEqual(dashboard_data['categories_count'], 1)
        
        # 12. Check Review Stats
        stats_url = reverse('analytics:review-stats')
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats_data = response.data
        self.assertEqual(stats_data['total_reviews'], 1)
        self.assertEqual(stats_data['success_rate'], 100.0)
        self.assertEqual(stats_data['average_time_spent'], 120.0)
        
        # 13. Test Today's Reviews (should be empty now)
        response = self.client.get(today_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
        
        # 14. Test Profile Update
        profile_url = reverse('accounts:profile')
        profile_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'timezone': 'America/New_York',
            'notification_enabled': False,
        }
        
        response = self.client.patch(profile_url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 15. Test Password Change
        password_url = reverse('accounts:password-change')
        password_data = {
            'current_password': 'newpass123',
            'new_password': 'updatedpass123',
            'new_password_confirm': 'updatedpass123',
        }
        
        response = self.client.post(password_url, password_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_multi_content_review_cycle(self):
        """Test review cycle with multiple contents"""
        # Create multiple contents
        contents = []
        for i in range(5):
            content = self.create_content(title=f'Content {i}')
            contents.append(content)
        
        # Create schedules for all contents
        schedules = []
        for content in contents:
            schedule = self.create_review_schedule(
                content=content,
                next_review_date=timezone.now() - timedelta(hours=1)
            )
            schedules.append(schedule)
        
        # Get today's reviews
        today_url = reverse('review:today')
        response = self.client.get(today_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        
        # Complete all reviews with different results
        results = ['remembered', 'forgot', 'partial', 'remembered', 'forgot']
        complete_url = reverse('review:complete')
        
        for i, (schedule, result) in enumerate(zip(schedules, results)):
            complete_data = {
                'schedule_id': schedule.id,
                'result': result,
                'time_spent': 120 + i * 30,
                'notes': f'Review {i} completed'
            }
            
            response = self.client.post(complete_url, complete_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all schedules were updated correctly
        for i, (schedule, result) in enumerate(zip(schedules, results)):
            schedule.refresh_from_db()
            
            if result == 'remembered':
                self.assertEqual(schedule.interval_index, 1)
            elif result == 'forgot':
                self.assertEqual(schedule.interval_index, 0)
            elif result == 'partial':
                self.assertEqual(schedule.interval_index, 0)  # Stays same
        
        # Verify all history entries were created
        history_count = ReviewHistory.objects.count()
        self.assertEqual(history_count, 5)
        
        # Check analytics after multiple reviews
        dashboard_url = reverse('analytics:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        dashboard_data = response.data
        self.assertEqual(dashboard_data['total_contents'], 6)  # 5 + 1 from base setup
        self.assertEqual(dashboard_data['total_reviews'], 5)
        
        # Check review stats
        stats_url = reverse('analytics:review-stats')
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats_data = response.data
        self.assertEqual(stats_data['total_reviews'], 5)
        # Success rate: 2 remembered out of 5 = 40%
        self.assertEqual(stats_data['success_rate'], 40.0)
    
    def test_spaced_repetition_workflow(self):
        """Test complete spaced repetition workflow over time"""
        content = self.create_content(title='Spaced Repetition Test')
        schedule = self.create_review_schedule(
            content=content,
            next_review_date=timezone.now(),
            interval_index=0,
            initial_review_completed=False
        )
        
        complete_url = reverse('review:complete')
        
        # Simulate review cycles over time
        intervals = [0, 1, 2, 3, 4]  # Progress through all intervals
        
        for target_interval in intervals:
            # Set schedule to due
            schedule.next_review_date = timezone.now() - timedelta(hours=1)
            schedule.save()
            
            # Complete review with remembered result
            complete_data = {
                'schedule_id': schedule.id,
                'result': 'remembered',
                'time_spent': 120,
                'notes': f'Review at interval {target_interval}'
            }
            
            response = self.client.post(complete_url, complete_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify schedule advanced
            schedule.refresh_from_db()
            expected_interval = min(target_interval + 1, 4)  # Max interval index is 4
            self.assertEqual(schedule.interval_index, expected_interval)
            self.assertTrue(schedule.initial_review_completed)
        
        # Verify review history
        history_count = ReviewHistory.objects.filter(content=content).count()
        self.assertEqual(history_count, 5)
        
        # Test forgetting and reset
        schedule.next_review_date = timezone.now() - timedelta(hours=1)
        schedule.save()
        
        forgot_data = {
            'schedule_id': schedule.id,
            'result': 'forgot',
            'time_spent': 200,
            'notes': 'Forgot this time'
        }
        
        response = self.client.post(complete_url, forgot_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify schedule was reset
        schedule.refresh_from_db()
        self.assertEqual(schedule.interval_index, 0)
    
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_notification_workflow(self):
        """Test notification workflow"""
        # Create users with different settings
        user1 = self.create_user(
            username='user1',
            email='user1@example.com',
            notification_enabled=True
        )
        user2 = self.create_user(
            username='user2',
            email='user2@example.com',
            notification_enabled=False
        )
        
        # Create content and schedules due for review
        content1 = self.create_content(title='Content 1', author=user1)
        content2 = self.create_content(title='Content 2', author=user2)
        
        schedule1 = self.create_review_schedule(
            user=user1,
            content=content1,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        schedule2 = self.create_review_schedule(
            user=user2,
            content=content2,
            next_review_date=timezone.now() - timedelta(hours=1)
        )
        
        # Send notifications
        send_daily_review_notifications()
        
        # Only user1 should receive notification
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], user1.email)
        self.assertIn('Daily Review Reminder', mail.outbox[0].subject)
    
    def test_category_filtering_workflow(self):
        """Test workflow with category filtering"""
        # Create categories
        python_category = self.create_category(name='Python')
        django_category = self.create_category(name='Django')
        js_category = self.create_category(name='JavaScript')
        
        # Create content in different categories
        python_content = self.create_content(title='Python Content', category=python_category)
        django_content = self.create_content(title='Django Content', category=django_category)
        js_content = self.create_content(title='JS Content', category=js_category)
        
        # Create review history for each
        self.create_review_history(content=python_content, result='remembered')
        self.create_review_history(content=django_content, result='forgot')
        self.create_review_history(content=js_content, result='partial')
        
        # Test analytics with category filtering
        stats_url = reverse('analytics:review-stats')
        
        # Filter by Python category
        response = self.client.get(stats_url, {'category': python_category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats_data = response.data
        self.assertEqual(stats_data['total_reviews'], 1)
        self.assertEqual(stats_data['success_rate'], 100.0)
        
        # Filter by Django category
        response = self.client.get(stats_url, {'category': django_category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stats_data = response.data
        self.assertEqual(stats_data['total_reviews'], 1)
        self.assertEqual(stats_data['success_rate'], 0.0)
    
    def test_image_upload_workflow(self):
        """Test image upload workflow"""
        # Create test image
        image = self.create_test_image()
        
        # Upload image
        upload_url = reverse('content:upload-image')
        response = self.client.post(upload_url, {'image': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        uploaded_filename = response.data['filename']
        uploaded_url = response.data['url']
        
        # Create content with uploaded image
        content_url = reverse('content:contents-list')
        content_data = {
            'title': 'Content with Image',
            'content': f'Content with image: {uploaded_url}',
            'priority': 'medium',
            'category': self.category.id,
            'tag_ids': [self.tag.id]
        }
        
        response = self.client.post(content_url, content_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        content_id = response.data['id']
        
        # Verify content was created
        content = Content.objects.get(id=content_id)
        self.assertEqual(content.title, 'Content with Image')
        self.assertIn(uploaded_url, content.content)
        
        # Clean up - delete image
        delete_url = reverse('content:delete-image', kwargs={'filename': uploaded_filename})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_data_isolation(self):
        """Test that user data is properly isolated"""
        # Create another user
        other_user = self.create_user(username='other', email='other@example.com')
        
        # Create content for other user
        other_category = self.create_category(name='Other Category', user=other_user)
        other_content = self.create_content(
            title='Other Content',
            author=other_user,
            category=other_category
        )
        other_schedule = self.create_review_schedule(
            user=other_user,
            content=other_content
        )
        other_history = self.create_review_history(
            user=other_user,
            content=other_content,
            result='remembered'
        )
        
        # Test that current user cannot see other user's data
        
        # Contents
        contents_url = reverse('content:contents-list')
        response = self.client.get(contents_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        content_titles = [item['title'] for item in response.data['results']]
        self.assertNotIn('Other Content', content_titles)
        
        # Categories
        categories_url = reverse('content:categories-list')
        response = self.client.get(categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_names = [item['name'] for item in response.data['results']]
        self.assertNotIn('Other Category', category_names)
        
        # Review schedules
        schedules_url = reverse('review:schedules-list')
        response = self.client.get(schedules_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        schedule_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(other_schedule.id, schedule_ids)
        
        # Review history
        history_url = reverse('review:history-list')
        response = self.client.get(history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        history_ids = [item['id'] for item in response.data['results']]
        self.assertNotIn(other_history.id, history_ids)
        
        # Analytics
        dashboard_url = reverse('analytics:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should not include other user's data
        self.assertEqual(response.data['total_contents'], 1)  # Only current user's content
    
    def test_error_handling_workflow(self):
        """Test error handling in various workflows"""
        # Test creating content with invalid data
        content_url = reverse('content:contents-list')
        invalid_data = {
            'title': '',  # Empty title
            'content': 'Valid content',
            'priority': 'invalid_priority',  # Invalid priority
            'category': 99999,  # Non-existent category
            'tag_ids': [99999]  # Non-existent tag
        }
        
        response = self.client.post(content_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test completing review with invalid data
        complete_url = reverse('review:complete')
        invalid_complete_data = {
            'schedule_id': 99999,  # Non-existent schedule
            'result': 'invalid_result',  # Invalid result
            'time_spent': -1  # Invalid time
        }
        
        response = self.client.post(complete_url, invalid_complete_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test accessing non-existent content
        detail_url = reverse('content:contents-detail', kwargs={'pk': 99999})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_performance_with_large_dataset(self):
        """Test system performance with large dataset"""
        # Create large dataset
        categories = []
        for i in range(5):
            category = self.create_category(name=f'Category {i}')
            categories.append(category)
        
        tags = []
        for i in range(10):
            tag = Tag.objects.create(name=f'tag-{i}')
            tags.append(tag)
        
        contents = []
        for i in range(50):
            content = self.create_content(
                title=f'Content {i}',
                category=categories[i % len(categories)]
            )
            # Add random tags
            content.tags.set(tags[:3])
            contents.append(content)
        
        # Create review schedules and history
        for content in contents:
            schedule = self.create_review_schedule(content=content)
            for j in range(5):
                result = ['remembered', 'forgot', 'partial'][j % 3]
                self.create_review_history(
                    content=content,
                    result=result,
                    review_date=timezone.now() - timedelta(days=j)
                )
        
        # Test API performance
        import time
        
        # Test contents list
        start_time = time.time()
        contents_url = reverse('content:contents-list')
        response = self.client.get(contents_url)
        contents_time = time.time() - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(contents_time, 2.0)  # Should complete within 2 seconds
        
        # Test analytics dashboard
        start_time = time.time()
        dashboard_url = reverse('analytics:dashboard')
        response = self.client.get(dashboard_url)
        dashboard_time = time.time() - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(dashboard_time, 3.0)  # Should complete within 3 seconds
        
        # Test review stats
        start_time = time.time()
        stats_url = reverse('analytics:review-stats')
        response = self.client.get(stats_url)
        stats_time = time.time() - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(stats_time, 3.0)  # Should complete within 3 seconds