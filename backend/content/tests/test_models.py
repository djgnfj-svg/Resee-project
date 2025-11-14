"""
Tests for content models (Category and Content).
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from content.models import Category, Content

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test Category model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )

    def test_category_creation(self):
        """Test basic category creation."""
        category = Category.objects.create(
            name='Python',
            description='Python programming',
            user=self.user
        )
        self.assertEqual(category.name, 'Python')
        self.assertEqual(category.description, 'Python programming')
        self.assertEqual(category.user, self.user)

    def test_category_slug_auto_generation(self):
        """Test slug is automatically generated from name."""
        category = Category.objects.create(
            name='Python Basics',
            user=self.user
        )
        self.assertEqual(category.slug, 'python-basics')

    def test_category_emoji_only_name_validation(self):
        """Test emoji-only names are not allowed."""
        category = Category(
            name='🐍',
            user=self.user
        )
        # Emoji-only names should fail validation
        with self.assertRaises(ValidationError):
            category.save()

    def test_category_str(self):
        """Test category string representation."""
        category = Category.objects.create(
            name='Django',
            user=self.user
        )
        self.assertEqual(str(category), 'Django')

    def test_category_empty_name_validation(self):
        """Test category name cannot be empty."""
        category = Category(
            name='',
            user=self.user
        )
        with self.assertRaises(ValidationError):
            category.save()

    def test_category_unique_together(self):
        """Test name+user uniqueness constraint."""
        Category.objects.create(name='Python', user=self.user)

        # Same name for same user should fail
        duplicate = Category(name='Python', user=self.user)
        with self.assertRaises(ValidationError):
            duplicate.save()

    def test_category_different_user_same_name(self):
        """Test same name allowed for different users."""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )

        Category.objects.create(name='Python', user=self.user)
        category2 = Category.objects.create(name='Python', user=user2)

        self.assertEqual(category2.name, 'Python')
        self.assertEqual(category2.user, user2)


class ContentModelTest(TestCase):
    """Test Content model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.category = Category.objects.create(
            name='Python',
            user=self.user
        )

    def test_content_creation(self):
        """Test basic content creation."""
        content = Content.objects.create(
            title='Python Basics',
            content='Python is a programming language.',
            author=self.user,
            category=self.category
        )
        self.assertEqual(content.title, 'Python Basics')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
        self.assertEqual(content.review_mode, 'objective')  # default

    def test_content_str(self):
        """Test content string representation."""
        content = Content.objects.create(
            title='Django Tutorial',
            content='Django is a web framework.',
            author=self.user
        )
        self.assertEqual(str(content), 'Django Tutorial')

    def test_content_empty_title_validation(self):
        """Test content title cannot be empty."""
        content = Content(
            title='',
            content='Some content',
            author=self.user
        )
        with self.assertRaises(ValidationError):
            content.save()

    def test_content_whitespace_title_validation(self):
        """Test content title cannot be whitespace only."""
        content = Content(
            title='   ',
            content='Some content',
            author=self.user
        )
        with self.assertRaises(ValidationError):
            content.save()

    def test_content_empty_content_validation(self):
        """Test content body cannot be empty."""
        content = Content(
            title='Test',
            content='',
            author=self.user
        )
        with self.assertRaises(ValidationError):
            content.save()

    def test_content_review_mode_choices(self):
        """Test all review mode choices."""
        modes = ['objective', 'descriptive', 'multiple_choice', 'subjective']

        for mode in modes:
            content = Content.objects.create(
                title=f'Test {mode}',
                content='x' * 250,  # Long enough for AI modes
                author=self.user,
                review_mode=mode
            )
            self.assertEqual(content.review_mode, mode)

    def test_content_ai_mode_minimum_length(self):
        """Test AI modes require 200+ characters."""
        ai_modes = ['descriptive', 'multiple_choice', 'subjective']

        for mode in ai_modes:
            content = Content(
                title='Test',
                content='Short content',  # < 200 chars
                author=self.user,
                review_mode=mode
            )
            with self.assertRaises(ValidationError) as context:
                content.save()
            self.assertIn('200자 이상', str(context.exception))

    def test_content_objective_mode_no_length_requirement(self):
        """Test objective mode has no minimum length."""
        content = Content.objects.create(
            title='Short',
            content='Short content',
            author=self.user,
            review_mode='objective'
        )
        self.assertEqual(content.review_mode, 'objective')

    def test_content_ai_validation_reset_on_title_change(self):
        """Test AI validation is reset when title changes."""
        content = Content.objects.create(
            title='Original',
            content='x' * 250,
            author=self.user,
            is_ai_validated=True,
            ai_validation_score=95.0,
            ai_validated_at=timezone.now()
        )

        # Change title
        content.title = 'New Title'
        content.save()

        # AI validation should be reset
        self.assertFalse(content.is_ai_validated)
        self.assertIsNone(content.ai_validation_score)
        self.assertIsNone(content.ai_validated_at)

    def test_content_ai_validation_reset_on_content_change(self):
        """Test AI validation is reset when content changes."""
        content = Content.objects.create(
            title='Title',
            content='x' * 250,
            author=self.user,
            is_ai_validated=True,
            ai_validation_score=90.0,
            ai_validated_at=timezone.now()
        )

        # Change content
        content.content = 'y' * 250
        content.save()

        # AI validation should be reset
        self.assertFalse(content.is_ai_validated)
        self.assertIsNone(content.ai_validation_score)

    def test_content_mc_choices_reset_on_change(self):
        """Test MC choices are reset when content changes."""
        content = Content.objects.create(
            title='Title',
            content='x' * 250,
            author=self.user,
            review_mode='multiple_choice',
            mc_choices={'choices': ['A', 'B', 'C', 'D'], 'correct_answer': 'A'}
        )

        # Change content
        content.content = 'y' * 250
        content.save()

        # MC choices should be reset
        self.assertIsNone(content.mc_choices)

    def test_content_ai_validation_not_reset_on_other_change(self):
        """Test AI validation not reset when only category changes."""
        content = Content.objects.create(
            title='Title',
            content='x' * 250,
            author=self.user,
            is_ai_validated=True,
            ai_validation_score=95.0,
            ai_validated_at=timezone.now()
        )

        original_score = content.ai_validation_score

        # Change only category (not title/content)
        category2 = Category.objects.create(name='New Category', user=self.user)
        content.category = category2
        content.save()

        # AI validation should NOT be reset
        self.assertTrue(content.is_ai_validated)
        self.assertEqual(content.ai_validation_score, original_score)

    def test_content_original_values_tracking(self):
        """Test __init__ stores original values."""
        content = Content.objects.create(
            title='Original Title',
            content='Original content',
            author=self.user
        )

        # Check original values are stored
        self.assertEqual(content._original_title, 'Original Title')
        self.assertEqual(content._original_content, 'Original content')

        # Change and save
        content.title = 'New Title'
        content.save()

        # Original values should be updated after save
        self.assertEqual(content._original_title, 'New Title')

    def test_content_default_ai_fields(self):
        """Test AI-related fields default to None/False."""
        content = Content.objects.create(
            title='Test',
            content='Test content',
            author=self.user
        )

        self.assertFalse(content.is_ai_validated)
        self.assertIsNone(content.ai_validation_score)
        self.assertIsNone(content.ai_validation_result)
        self.assertIsNone(content.ai_validated_at)
        self.assertIsNone(content.mc_choices)
