"""
Tests for review app
"""
import pytest
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from content.models import Content
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()


class TestReviewScheduleModel:
    """Test ReviewSchedule model"""
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def content(self, db, user):
        return Content.objects.create(
            title='Test Content',
            content='Test content for review',
            author=user
        )
    
    @pytest.mark.django_db
    def test_create_review_schedule(self, user, content):
        """Test creating a review schedule"""
        next_review = timezone.now() + timedelta(days=1)
        
        schedule = ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=next_review,
            interval_index=0
        )
        
        assert schedule.content == content
        assert schedule.user == user
        assert schedule.interval_index == 0
        assert schedule.is_active is True
        assert str(schedule) == f"{user.username} - {content.title} - {next_review}"
    
    @pytest.mark.django_db
    def test_get_next_interval(self, user, content):
        """Test getting next review interval"""
        schedule = ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=timezone.now() + timedelta(days=1),
            interval_index=0
        )
        
        # Default intervals: [1, 3, 7, 14, 30]
        assert schedule.get_next_interval() == 3  # Next after index 0
        
        schedule.interval_index = 2
        assert schedule.get_next_interval() == 14  # Next after index 2
        
        schedule.interval_index = 4  # Last interval
        assert schedule.get_next_interval() == 30  # Should stay at last interval
    
    @pytest.mark.django_db
    def test_advance_schedule(self, user, content):
        """Test advancing review schedule"""
        schedule = ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=timezone.now(),
            interval_index=0
        )
        
        original_date = schedule.next_review_date
        schedule.advance_schedule()
        
        assert schedule.interval_index == 1
        assert schedule.next_review_date > original_date
    
    @pytest.mark.django_db
    def test_reset_schedule(self, user, content):
        """Test resetting review schedule"""
        schedule = ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=timezone.now(),
            interval_index=3
        )
        
        schedule.reset_schedule()
        
        assert schedule.interval_index == 0
        # Should be set to 1 day from now
        expected_date = timezone.now() + timedelta(days=1)
        time_diff = abs((schedule.next_review_date - expected_date).total_seconds())
        assert time_diff < 60  # Within 1 minute
    
    @pytest.mark.django_db
    def test_unique_content_user(self, user, content):
        """Test unique constraint on content and user"""
        ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=timezone.now() + timedelta(days=1)
        )
        
        # Should raise IntegrityError for duplicate content-user pair
        with pytest.raises(Exception):
            ReviewSchedule.objects.create(
                content=content,
                user=user,
                next_review_date=timezone.now() + timedelta(days=2)
            )


class TestReviewHistoryModel:
    """Test ReviewHistory model"""
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @pytest.fixture
    def content(self, db, user):
        return Content.objects.create(
            title='Test Content',
            content='Test content for review',
            author=user
        )
    
    @pytest.mark.django_db
    def test_create_review_history(self, user, content):
        """Test creating review history"""
        history = ReviewHistory.objects.create(
            content=content,
            user=user,
            result='remembered',
            time_spent=120,  # 2 minutes
            notes='Good recall'
        )
        
        assert history.content == content
        assert history.user == user
        assert history.result == 'remembered'
        assert history.time_spent == 120
        assert history.notes == 'Good recall'
        assert str(history) == f"{user.username} - {content.title} - remembered"
    
    @pytest.mark.django_db
    def test_review_result_choices(self, user, content):
        """Test review result choices"""
        valid_results = ['remembered', 'partial', 'forgot']
        
        for result in valid_results:
            history = ReviewHistory.objects.create(
                content=content,
                user=user,
                result=result
            )
            assert history.result == result
    
    @pytest.mark.django_db
    def test_review_history_ordering(self, user, content):
        """Test review history is ordered by review_date descending"""
        # Create multiple history entries
        history1 = ReviewHistory.objects.create(
            content=content,
            user=user,
            result='remembered'
        )
        
        history2 = ReviewHistory.objects.create(
            content=content,
            user=user,
            result='forgot'
        )
        
        # Get all histories
        histories = list(ReviewHistory.objects.all())
        
        # Should be ordered by review_date descending (newest first)
        assert histories[0] == history2
        assert histories[1] == history1