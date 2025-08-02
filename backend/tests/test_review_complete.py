"""
Test review completion flow and data accuracy
"""
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()


@pytest.mark.django_db
class TestReviewCompleteFlow:
    """Test the complete review flow from start to finish"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self):
        user = User.objects.create_user(
            email='reviewer@test.com',
            password='testpass123'
        )
        user.is_active = True
        user.save()
        return user
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client
    
    @pytest.fixture
    def test_content(self, user):
        category = Category.objects.create(
            name='Python',
            slug='python',
            user=user
        )
        content = Content.objects.create(
            title='Python List Comprehension',
            content='List comprehension syntax: [expression for item in iterable]',
            category=category,
            author=user,
            priority='medium'
        )
        # Create review schedule manually since signals might not work in tests
        from review.models import ReviewSchedule
        ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=timezone.now(),
            interval_index=0,
            is_active=True,
            initial_review_completed=False
        )
        return content
    
    def test_review_completion_creates_history(self, authenticated_client, test_content):
        """Test that completing a review creates proper history record"""
        # Get review schedule
        schedule = ReviewSchedule.objects.get(content=test_content)
        
        # Complete review
        response = authenticated_client.post('/api/review/complete/', {
            'content_id': test_content.id,
            'result': 'remembered',
            'time_spent': 120
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check history created
        history = ReviewHistory.objects.get(content=test_content)
        assert history.user == test_content.author
        assert history.result == 'remembered'
        assert history.time_spent == 120
        
    def test_review_completion_updates_schedule(self, authenticated_client, test_content):
        """Test that completing a review updates the schedule correctly"""
        # Get initial schedule
        schedule = ReviewSchedule.objects.get(content=test_content)
        initial_interval_index = schedule.interval_index
        initial_review_date = schedule.next_review_date
        
        # Complete review successfully
        response = authenticated_client.post('/api/review/complete/', {
            'content_id': test_content.id,
            'result': 'remembered',
            'time_spent': 90
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check schedule updated
        schedule.refresh_from_db()
        assert schedule.interval_index == initial_interval_index + 1
        assert schedule.next_review_date > initial_review_date
        assert schedule.initial_review_completed is True
        
    def test_failed_review_resets_schedule(self, authenticated_client, test_content):
        """Test that failing a review resets the schedule"""
        # Advance schedule first
        schedule = ReviewSchedule.objects.get(content=test_content)
        schedule.interval_index = 3  # Set to day 7
        schedule.save()
        
        # Fail the review
        response = authenticated_client.post('/api/review/complete/', {
            'content_id': test_content.id,
            'result': 'forgot',
            'time_spent': 60
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check schedule reset
        schedule.refresh_from_db()
        assert schedule.interval_index == 0  # Reset to beginning
        
    def test_multiple_reviews_same_day(self, authenticated_client, test_content):
        """Test that multiple reviews on same day are recorded properly"""
        # Complete first review
        response1 = authenticated_client.post('/api/review/complete/', {
            'content_id': test_content.id,
            'result': 'remembered',
            'time_spent': 100
        })
        assert response1.status_code == status.HTTP_200_OK
        
        # Reset schedule to allow another review
        schedule = ReviewSchedule.objects.get(content=test_content)
        schedule.next_review_date = timezone.now()
        schedule.save()
        
        # Complete second review
        response2 = authenticated_client.post('/api/review/complete/', {
            'content_id': test_content.id,
            'result': 'partial',
            'time_spent': 80
        })
        assert response2.status_code == status.HTTP_200_OK
        
        # Check both histories exist
        histories = ReviewHistory.objects.filter(content=test_content).order_by('review_date')
        assert histories.count() == 2
        assert histories[0].result == 'remembered'
        assert histories[1].result == 'partial'
        
    def test_review_completion_with_notes(self, authenticated_client, test_content):
        """Test review completion with notes"""
        notes = "Need to practice more examples with nested list comprehensions"
        
        response = authenticated_client.post('/api/review/complete/', {
            'content_id': test_content.id,
            'result': 'partial',
            'time_spent': 150,
            'notes': notes
        })
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check notes saved
        history = ReviewHistory.objects.get(content=test_content)
        assert history.notes == notes