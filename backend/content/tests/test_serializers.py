"""
Tests for content serializers.
"""
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from content.models import Category, Content
from content.serializers import CategorySerializer, ContentSerializer

User = get_user_model()


class CategorySerializerTest(TestCase):
    """Test CategorySerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_serialize_category(self):
        """Test serializing a category."""
        category = Category.objects.create(
            name='Python',
            description='Python programming',
            user=self.user
        )

        serializer = CategorySerializer(category)
        data = serializer.data

        self.assertEqual(data['name'], 'Python')
        self.assertEqual(data['description'], 'Python programming')
        self.assertEqual(data['slug'], 'python')

    def test_deserialize_category(self):
        """Test deserializing category data."""
        data = {
            'name': 'Django',
            'description': 'Django framework'
        }

        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'Django')

    def test_read_only_fields(self):
        """Test read-only fields cannot be written."""
        category = Category.objects.create(name='Test', user=self.user)

        # Try to update read-only fields
        data = {
            'name': 'Updated',
            'slug': 'custom-slug',  # Read-only
            'id': 999  # Read-only
        }

        serializer = CategorySerializer(category, data=data)
        self.assertTrue(serializer.is_valid())

        # slug and id should not be updated
        updated = serializer.save()
        self.assertEqual(updated.slug, 'test')  # Original slug
        self.assertNotEqual(updated.id, 999)


class ContentSerializerTest(TestCase):
    """Test ContentSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Python', user=self.user)

        self.factory = RequestFactory()

    def test_serialize_content(self):
        """Test serializing content."""
        content = Content.objects.create(
            title='Python Basics',
            content='Python is a programming language.',
            author=self.user,
            category=self.category
        )

        serializer = ContentSerializer(content)
        data = serializer.data

        self.assertEqual(data['title'], 'Python Basics')
        self.assertEqual(data['author'], str(self.user))
        self.assertIsNotNone(data['category'])
        self.assertEqual(data['category']['name'], 'Python')

    def test_serialize_content_without_category(self):
        """Test serializing content without category."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user,
            category=None
        )

        serializer = ContentSerializer(content)
        data = serializer.data

        self.assertIsNone(data['category'])

    def test_to_representation_category_nested(self):
        """Test category is represented as nested object."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user,
            category=self.category
        )

        serializer = ContentSerializer(content)
        data = serializer.data

        # Category should be a dict, not just ID
        self.assertIsInstance(data['category'], dict)
        self.assertEqual(data['category']['name'], 'Python')
        self.assertEqual(data['category']['slug'], 'python')

    def test_validate_category_none(self):
        """Test category can be None."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = ContentSerializer(
            data={
                'title': 'Test',
                'content': 'Test content',
                'category': None
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())

    def test_validate_category_belongs_to_user(self):
        """Test category must belong to user."""
        category2 = Category.objects.create(name='Django', user=self.user2)

        request = self.factory.post('/')
        request.user = self.user

        serializer = ContentSerializer(
            data={
                'title': 'Test',
                'content': 'Test content',
                'category': category2.id
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)

    def test_validate_category_no_auth(self):
        """Test category validation requires authentication."""
        request = self.factory.post('/')
        request.user = None

        serializer = ContentSerializer(
            data={
                'title': 'Test',
                'content': 'Test content',
                'category': self.category.id
            },
            context={'request': request}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn('category', serializer.errors)

    @patch('ai_services.generate_multiple_choice_options')
    def test_create_with_mc_mode(self, mock_generate_mc):
        """Test creating content with multiple_choice mode generates MC options."""
        mock_generate_mc.return_value = {
            'choices': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A'
        }

        request = self.factory.post('/')
        request.user = self.user

        serializer = ContentSerializer(
            data={
                'title': 'Test',
                'content': 'x' * 250,
                'review_mode': 'multiple_choice'
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
        content = serializer.save(author=self.user)

        # MC options should be generated (may be called by signal too)
        self.assertTrue(mock_generate_mc.called)
        content.refresh_from_db()
        self.assertIsNotNone(content.mc_choices)
        self.assertEqual(content.mc_choices['correct_answer'], 'A')

    @patch('ai_services.generate_multiple_choice_options')
    def test_update_regenerates_mc_on_content_change(self, mock_generate_mc):
        """Test updating content regenerates MC options if mode is MC."""
        mock_generate_mc.return_value = {
            'choices': ['New A', 'New B', 'New C', 'New D'],
            'correct_answer': 'New A'
        }

        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice',
            mc_choices={'choices': ['Old A'], 'correct_answer': 'Old A'}
        )

        # Reset mock to ignore creation calls
        mock_generate_mc.reset_mock()

        request = self.factory.put('/')
        request.user = self.user

        serializer = ContentSerializer(
            content,
            data={
                'title': 'Test',
                'content': 'y' * 250  # Changed
            },
            context={'request': request},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        updated = serializer.save()

        # MC options should be regenerated
        mock_generate_mc.assert_called_once()
        updated.refresh_from_db()
        self.assertEqual(updated.mc_choices['correct_answer'], 'New A')

    @patch('ai_services.generate_multiple_choice_options')
    def test_update_no_regenerate_if_content_unchanged(self, mock_generate_mc):
        """Test MC options not regenerated if content unchanged."""
        content = Content.objects.create(
            title='Test',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice',
            mc_choices={'choices': ['A'], 'correct_answer': 'A'}
        )

        # Reset mock to ignore creation calls
        mock_generate_mc.reset_mock()

        request = self.factory.put('/')
        request.user = self.user

        serializer = ContentSerializer(
            content,
            data={
                'title': 'Test',  # Same
                'content': 'x' * 250  # Same
            },
            context={'request': request},
            partial=True
        )

        self.assertTrue(serializer.is_valid())
        serializer.save()

        # MC options should NOT be regenerated
        mock_generate_mc.assert_not_called()

    def test_get_review_count_annotated(self):
        """Test get_review_count uses annotated value."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        # Simulate annotated value
        content.review_count_annotated = 5

        serializer = ContentSerializer(content)
        data = serializer.data

        self.assertEqual(data['review_count'], 5)

    def test_get_review_count_fallback(self):
        """Test get_review_count falls back to direct count."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        # No annotated value, should use direct count
        serializer = ContentSerializer(content)
        data = serializer.data

        self.assertEqual(data['review_count'], 0)

    def test_get_next_review_date_prefetched(self):
        """Test get_next_review_date uses prefetched value."""
        from datetime import datetime

        from django.utils import timezone

        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        # Simulate prefetched value
        mock_schedule = Mock()
        mock_schedule.next_review_date = timezone.now()
        content.user_review_schedules = [mock_schedule]

        request = self.factory.get('/')
        request.user = self.user

        serializer = ContentSerializer(content, context={'request': request})
        data = serializer.data

        self.assertIsNotNone(data['next_review_date'])

    def test_get_next_review_date_no_context(self):
        """Test get_next_review_date returns None without request context."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        # No request context
        serializer = ContentSerializer(content)
        data = serializer.data

        # Should handle gracefully
        self.assertIsNone(data['next_review_date'])

    def test_read_only_fields(self):
        """Test AI-related fields are read-only."""
        request = self.factory.post('/')
        request.user = self.user

        serializer = ContentSerializer(
            data={
                'title': 'Test',
                'content': 'Test content',
                'is_ai_validated': True,  # Read-only
                'ai_validation_score': 95.0,  # Read-only
                'mc_choices': {'choices': ['A']}  # Read-only
            },
            context={'request': request}
        )

        self.assertTrue(serializer.is_valid())
        content = serializer.save(author=self.user)

        # Read-only fields should remain default
        self.assertFalse(content.is_ai_validated)
        self.assertIsNone(content.ai_validation_score)
