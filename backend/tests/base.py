"""
Base test utilities and fixtures for Resee backend tests
"""

import io
import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class BaseTestCase(TestCase):
    """Base test case with common setup for all tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = self.create_user(email='test@example.com')
        self.category = self.create_category()
        self.content = self.create_content()
    
    def create_user(self, **kwargs):
        """Create a test user"""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        defaults = {
            'email': f'test_{unique_suffix}@example.com',
            'password': 'testpass123',
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
    
    def create_category(self, **kwargs):
        """Create a test category"""
        defaults = {
            'name': 'Test Category',
            'user': self.user if hasattr(self, 'user') else self.create_user(),
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)
    
    
    def create_content(self, **kwargs):
        """Create test content"""
        defaults = {
            'title': 'Test Content',
            'content': 'This is test content',
            'author': self.user if hasattr(self, 'user') else self.create_user(),
            'category': self.category if hasattr(self, 'category') else self.create_category(),
            'priority': 'medium',
        }
        defaults.update(kwargs)
        content = Content.objects.create(**defaults)
        return content
    
    def create_review_schedule(self, **kwargs):
        """Create a review schedule"""
        defaults = {
            'user': self.user if hasattr(self, 'user') else self.create_user(),
            'content': self.content if hasattr(self, 'content') else self.create_content(),
            'next_review_date': timezone.now(),
            'interval_index': 0,
            'is_active': True,
            'initial_review_completed': False,
        }
        defaults.update(kwargs)
        
        # Check if schedule already exists for this user-content pair
        existing_schedule = ReviewSchedule.objects.filter(
            user=defaults['user'],
            content=defaults['content']
        ).first()
        
        if existing_schedule:
            # Update existing schedule with new values
            for key, value in defaults.items():
                setattr(existing_schedule, key, value)
            existing_schedule.save()
            return existing_schedule
        else:
            return ReviewSchedule.objects.create(**defaults)
    
    def create_review_history(self, **kwargs):
        """Create review history"""
        defaults = {
            'user': self.user if hasattr(self, 'user') else self.create_user(),
            'content': self.content if hasattr(self, 'content') else self.create_content(),
            'result': 'remembered',
            'review_date': timezone.now(),
        }
        defaults.update(kwargs)
        return ReviewHistory.objects.create(**defaults)
    
    def create_test_image(self, format='PNG'):
        """Create a test image file (stub - image upload functionality removed)"""
        # Create a simple fake image file for any remaining tests
        return SimpleUploadedFile(
            name=f'test.{format.lower()}',
            content=b'fake image content',
            content_type=f'image/{format.lower()}'
        )


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication setup"""
    
    def setUp(self):
        """Set up API test fixtures"""
        self.user = self.create_user(email='test@example.com')
        self.authenticate_user()
        self.category = self.create_category()
        self.content = self.create_content()
    
    def create_user(self, **kwargs):
        """Create a test user"""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        defaults = {
            'email': f'test_{unique_suffix}@example.com',
            'password': 'testpass123',
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)
    
    def authenticate_user(self, user=None):
        """Authenticate user for API tests"""
        if user is None:
            user = self.user
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def create_category(self, **kwargs):
        """Create a test category"""
        defaults = {
            'name': 'Test Category',
            'user': self.user,
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)
    
    
    def create_content(self, **kwargs):
        """Create test content"""
        defaults = {
            'title': 'Test Content',
            'content': 'This is test content',
            'author': self.user,
            'category': self.category,
            'priority': 'medium',
        }
        defaults.update(kwargs)
        content = Content.objects.create(**defaults)
        return content
    
    def create_review_schedule(self, **kwargs):
        """Create a review schedule"""
        defaults = {
            'user': self.user,
            'content': self.content,
            'next_review_date': timezone.now(),
            'interval_index': 0,
            'is_active': True,
            'initial_review_completed': False,
        }
        defaults.update(kwargs)
        
        # Check if schedule already exists for this user-content pair
        existing_schedule = ReviewSchedule.objects.filter(
            user=defaults['user'],
            content=defaults['content']
        ).first()
        
        if existing_schedule:
            # Update existing schedule with new values
            for key, value in defaults.items():
                setattr(existing_schedule, key, value)
            existing_schedule.save()
            return existing_schedule
        else:
            return ReviewSchedule.objects.create(**defaults)
    
    def create_review_history(self, **kwargs):
        """Create review history"""
        defaults = {
            'user': self.user,
            'content': self.content,
            'result': 'remembered',
            'review_date': timezone.now(),
        }
        defaults.update(kwargs)
        return ReviewHistory.objects.create(**defaults)
    
    def create_test_image(self, format='PNG'):
        """Create a test image file (stub - image upload functionality removed)"""
        # Create a simple fake image file for any remaining tests
        return SimpleUploadedFile(
            name=f'test.{format.lower()}',
            content=b'fake image content',
            content_type=f'image/{format.lower()}'
        )


class TestDataMixin:
    """Mixin for creating test data consistently"""
    
    def create_multiple_users(self, count=3):
        """Create multiple test users"""
        users = []
        for i in range(count):
            user = User.objects.create_user(
                email=f'test{i}@example.com',
                password='testpass123',
            )
            users.append(user)
        return users
    
    def create_multiple_contents(self, count=3, author=None):
        """Create multiple test contents"""
        if author is None:
            author = self.user
        contents = []
        for i in range(count):
            content = Content.objects.create(
                title=f'Test Content {i}',
                content=f'This is test content {i}',
                author=author,
                category=self.category,
                priority='medium',
            )
            # Tag functionality has been removed
            contents.append(content)
        return contents
    
    def create_review_chain(self, content=None, intervals=None):
        """Create a complete review chain for testing spaced repetition"""
        if content is None:
            content = self.content
        if intervals is None:
            intervals = [0, 1, 2, 3, 4]  # All intervals
        
        schedule = ReviewSchedule.objects.create(
            user=self.user,
            content=content,
            next_review_date=timezone.now(),
            interval_index=0,
            is_active=True,
            initial_review_completed=False,
        )
        
        histories = []
        for i, interval in enumerate(intervals):
            history = ReviewHistory.objects.create(
                user=self.user,
                content=content,
                result='remembered',
                review_date=timezone.now() - timezone.timedelta(days=i),
                time_spent=180,  # 3 minutes
            )
            histories.append(history)
        
        return schedule, histories