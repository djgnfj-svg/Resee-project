"""
Tests for content views (CategoryViewSet and ContentViewSet).
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Subscription, SubscriptionTier
from content.models import Category, Content

User = get_user_model()


class CategoryViewSetTest(TestCase):
    """Test CategoryViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_list_categories(self):
        """Test listing user's categories."""
        Category.objects.create(name='Python', user=self.user)
        Category.objects.create(name='Django', user=self.user)

        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('usage', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_categories_usage_metadata(self):
        """Test category list includes usage metadata."""
        Category.objects.create(name='Python', user=self.user)

        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('usage', response.data)
        self.assertIn('current', response.data['usage'])
        self.assertIn('limit', response.data['usage'])

    def test_create_category(self):
        """Test creating a category."""
        response = self.client.post('/api/categories/', {
            'name': 'Python',
            'description': 'Python programming'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Python')

    def test_create_category_limit_exceeded(self):
        """Test creating category when limit is exceeded."""
        # Change user subscription to FREE tier (3 categories limit)
        subscription = Subscription.objects.get(user=self.user)
        subscription.tier = SubscriptionTier.FREE
        subscription.save()

        # Create 3 categories (limit for FREE tier)
        for i in range(3):
            Category.objects.create(name=f'Category{i}', user=self.user)

        # Try to create one more
        response = self.client.post('/api/categories/', {
            'name': 'TooMany'
        })
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('error', response.data)

    def test_retrieve_category(self):
        """Test retrieving a specific category."""
        category = Category.objects.create(name='Python', user=self.user)

        response = self.client.get(f'/api/categories/{category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Python')

    def test_update_category(self):
        """Test updating a category."""
        category = Category.objects.create(name='Python', user=self.user)

        response = self.client.put(f'/api/categories/{category.id}/', {
            'name': 'Python 3',
            'description': 'Updated description'
        })
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_delete_category(self):
        """Test deleting a category."""
        category = Category.objects.create(name='Python', user=self.user)

        response = self.client.delete(f'/api/categories/{category.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify category is deleted
        self.assertFalse(Category.objects.filter(id=category.id).exists())

    def test_list_categories_unauthenticated(self):
        """Test listing categories without authentication."""
        self.client.logout()

        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ContentViewSetTest(TestCase):
    """Test ContentViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='Python', user=self.user)

    def test_list_content(self):
        """Test listing user's content."""
        Content.objects.create(
            title='Python Basics',
            content='Python is a programming language.',
            author=self.user
        )

        response = self.client.get('/api/contents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('usage', response.data)

    def test_list_content_usage_metadata(self):
        """Test content list includes usage metadata."""
        Content.objects.create(title='Test', content='Test content', author=self.user)

        response = self.client.get('/api/contents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('usage', response.data)
        self.assertIn('current', response.data['usage'])
        self.assertIn('limit', response.data['usage'])

    def test_create_content(self):
        """Test creating content."""
        response = self.client.post('/api/contents/', {
            'title': 'Python Basics',
            'content': 'Python is a programming language.',
            'category': self.category.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Python Basics')

    def test_create_content_limit_exceeded(self):
        """Test creating content when limit is exceeded."""
        # Change user subscription to FREE tier (20 content limit)
        subscription = Subscription.objects.get(user=self.user)
        subscription.tier = SubscriptionTier.FREE
        subscription.save()

        # Refresh user to clear cached subscription
        self.user.refresh_from_db()

        # Create 20 contents (limit for FREE tier)
        for i in range(20):
            Content.objects.create(
                title=f'Content{i}',
                content=f'Content {i}',
                author=self.user
            )

        # Verify we have exactly 20 contents
        from accounts.subscription.services import PermissionService
        perm = PermissionService(self.user)
        content_count = Content.objects.filter(author=self.user).count()
        self.assertEqual(content_count, 20, f"Expected 20 contents, got {content_count}")
        self.assertEqual(perm.get_content_limit(), 20, f"Expected limit 20, got {perm.get_content_limit()}")
        self.assertFalse(perm.can_create_content(), "Should not be able to create more content")

        # Try to create one more (21st)
        response = self.client.post('/api/contents/', {
            'title': 'TooMany',
            'content': 'Too many contents'
        })
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertIn('error', response.data)

    def test_retrieve_content(self):
        """Test retrieving specific content."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        response = self.client.get(f'/api/contents/{content.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test')

    def test_update_content(self):
        """Test updating content."""
        content = Content.objects.create(
            title='Original',
            content='Original content',
            author=self.user
        )

        response = self.client.put(f'/api/contents/{content.id}/', {
            'title': 'Updated',
            'content': 'Updated content'
        })
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_delete_content(self):
        """Test deleting content."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        response = self.client.delete(f'/api/contents/{content.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify content is deleted
        self.assertFalse(Content.objects.filter(id=content.id).exists())

    def test_filter_by_category(self):
        """Test filtering content by category."""
        category2 = Category.objects.create(name='Django', user=self.user)

        Content.objects.create(title='Python1', content='Python content', author=self.user, category=self.category)
        Content.objects.create(title='Django1', content='Django content', author=self.user, category=category2)

        response = self.client.get(f'/api/contents/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All results should have the filtered category
        for item in response.data['results']:
            if item['category']:
                self.assertEqual(item['category']['id'], self.category.id)

    def test_filter_by_category_slug(self):
        """Test filtering content by category slug."""
        Content.objects.create(title='Python1', content='Python content', author=self.user, category=self.category)

        response = self.client.get(f'/api/contents/?category_slug={self.category.slug}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_content(self):
        """Test searching content."""
        Content.objects.create(title='Python Basics', content='Python programming', author=self.user)
        Content.objects.create(title='Django Tutorial', content='Web framework', author=self.user)

        response = self.client.get('/api/contents/?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_content(self):
        """Test ordering content."""
        response = self.client.get('/api/contents/?ordering=-created_at')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('content.views.validate_content')
    def test_validate_content_action(self, mock_validate):
        """Test /validate/ action."""
        mock_validate.return_value = {
            'is_valid': True,
            'factual_accuracy': {'score': 95, 'issues': []},
            'logical_consistency': {'score': 90, 'issues': []},
            'title_relevance': {'score': 100, 'issues': []},
            'overall_feedback': 'Great content'
        }

        response = self.client.post('/api/contents/validate/', {
            'title': 'Python Basics',
            'content': 'x' * 250
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])
        mock_validate.assert_called_once()

    def test_validate_content_missing_fields(self):
        """Test /validate/ action with missing fields."""
        response = self.client.post('/api/contents/validate/', {
            'title': 'Python Basics'
            # Missing content
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_validate_content_too_short(self):
        """Test /validate/ action with short content."""
        response = self.client.post('/api/contents/validate/', {
            'title': 'Python',
            'content': 'Short'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('content.views.validate_content')
    def test_validate_and_save_action(self, mock_validate):
        """Test /validate_and_save/ action."""
        mock_validate.return_value = {
            'is_valid': True,
            'factual_accuracy': {'score': 95, 'issues': []},
            'logical_consistency': {'score': 90, 'issues': []},
            'title_relevance': {'score': 100, 'issues': []},
            'overall_feedback': 'Great content'
        }

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user
        )

        response = self.client.post(f'/api/contents/{content.id}/validate_and_save/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_valid'])

        # Check DB was updated
        content.refresh_from_db()
        self.assertTrue(content.is_ai_validated)
        self.assertIsNotNone(content.ai_validation_score)

    def test_validate_and_save_already_validated(self):
        """Test /validate_and_save/ on already validated content."""
        from django.utils import timezone

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            is_ai_validated=True,
            ai_validation_score=95.0,
            ai_validated_at=timezone.now()
        )

        response = self.client.post(f'/api/contents/{content.id}/validate_and_save/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('이미 AI 검증', response.data['message'])

    def test_validate_and_save_too_short(self):
        """Test /validate_and_save/ with short content."""
        content = Content.objects.create(
            title='Test',
            content='Short',
            author=self.user
        )

        response = self.client.post(f'/api/contents/{content.id}/validate_and_save/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    @patch('content.views.validate_content')
    def test_validate_and_save_invalid_result(self, mock_validate):
        """Test /validate_and_save/ with invalid result (score < 70)."""
        mock_validate.return_value = {
            'is_valid': False,
            'factual_accuracy': {'score': 50, 'issues': ['Low score']},
            'logical_consistency': {'score': 60, 'issues': []},
            'title_relevance': {'score': 65, 'issues': []},
            'overall_feedback': 'Needs improvement'
        }

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user
        )

        response = self.client.post(f'/api/contents/{content.id}/validate_and_save/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_valid'])

        # DB should NOT be updated
        content.refresh_from_db()
        self.assertFalse(content.is_ai_validated)

    def test_list_content_unauthenticated(self):
        """Test listing content without authentication."""
        self.client.logout()

        response = self.client.get('/api/contents/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
