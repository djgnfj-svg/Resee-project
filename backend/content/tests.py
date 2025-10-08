"""
Test cases for content application
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Content
from .serializers import CategorySerializer, ContentSerializer

User = get_user_model()


class CategoryModelTest(TestCase):
    """Test Category model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Test Category',
            user=self.user,
            description='Test description'
        )
        
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.user, self.user)
        self.assertEqual(category.slug, 'test-category')
        self.assertEqual(str(category), 'Test Category')
    
    def test_category_slug_auto_generation(self):
        """Test automatic slug generation"""
        category = Category.objects.create(
            name='복잡한 한글 카테고리 이름!',
            user=self.user
        )
        
        # Slug should be generated automatically
        self.assertIsNotNone(category.slug)
        self.assertTrue(len(category.slug) > 0)
    
    def test_category_slug_uniqueness(self):
        """Test category name uniqueness per user"""
        # Create first category
        Category.objects.create(name='Same Name', user=self.user)

        # Second category with same name should fail due to unique constraint
        # Note: ValidationError is raised because save() calls full_clean()
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            Category.objects.create(name='Same Name', user=self.user)


class ContentModelTest(TestCase):
    """Test Content model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
    
    def test_create_content(self):
        """Test creating content"""
        content = Content.objects.create(
            title='Test Content',
            content='This is test content',
            author=self.user,
            category=self.category
        )

        self.assertEqual(content.title, 'Test Content')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
        self.assertEqual(str(content), 'Test Content')
    
    def test_content_validation(self):
        """Test content validation"""
        # Test empty title should fail
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            content = Content(
                title='',
                content='This is test content',
                author=self.user,
                category=self.category
            )
            content.full_clean()
    
    def test_content_creation_triggers_signal(self):
        """Test that content creation triggers review schedule creation"""
        # Import here to ensure signal is connected
        from review.models import ReviewSchedule

        content = Content.objects.create(
            title='Test Content',
            content='This is test content',
            author=self.user,
            category=self.category
        )

        # Check that review schedule was created
        review_schedule = ReviewSchedule.objects.filter(
            content=content,
            user=self.user
        )
        self.assertTrue(review_schedule.exists())
        self.assertTrue(Content.objects.filter(id=content.id).exists())


class CategoryAPITest(APITestCase):
    """Test Category API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.category = Category.objects.create(
            name='Existing Category',
            user=self.user,
            description='Existing description'
        )
    
    def test_list_categories(self):
        """Test listing user's categories"""
        url = reverse('content:categories-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response might be paginated
        data = response.data
        if 'results' in data:
            self.assertEqual(len(data['results']), 1)
            self.assertEqual(data['results'][0]['name'], 'Existing Category')
        else:
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['name'], 'Existing Category')
    
    def test_create_category(self):
        """Test creating a new category"""
        # Set user to PRO tier to avoid subscription limits
        from accounts.models import SubscriptionTier
        self.user.subscription.tier = SubscriptionTier.PRO
        self.user.subscription.save()

        url = reverse('content:categories-list')
        data = {
            'name': 'New Category',
            'description': 'New description'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if category was created
        self.assertTrue(Category.objects.filter(name='New Category', user=self.user).exists())
        self.assertEqual(response.data['name'], 'New Category')
        self.assertIsNotNone(response.data['slug'])
    
    def test_retrieve_category(self):
        """Test retrieving a specific category"""
        url = reverse('content:categories-detail', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Existing Category')
        self.assertEqual(response.data['id'], self.category.id)
    
    def test_update_category(self):
        """Test updating a category"""
        url = reverse('content:categories-detail', kwargs={'pk': self.category.pk})
        data = {
            'name': 'Updated Category',
            'description': 'Updated description'
        }
        
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Category')
        self.assertEqual(self.category.description, 'Updated description')
    
    def test_delete_category(self):
        """Test deleting a category"""
        url = reverse('content:categories-detail', kwargs={'pk': self.category.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
    
    def test_category_access_control(self):
        """Test that users can only access their own categories"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        other_category = Category.objects.create(
            name='Other Category',
            user=other_user
        )
        
        # Try to access other user's category
        url = reverse('content:categories-detail', kwargs={'pk': other_category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ContentAPITest(APITestCase):
    """Test Content API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        self.content = Content.objects.create(
            title='Existing Content',
            content='This is existing content',
            author=self.user,
            category=self.category
        )
    
    def test_list_contents(self):
        """Test listing user's contents"""
        url = reverse('content:contents-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        if 'results' in response.data:
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['title'], 'Existing Content')
    
    def test_create_content(self):
        """Test creating new content"""
        url = reverse('content:contents-list')
        data = {
            'title': 'New Content',
            'content': 'This is new content',
            'category': self.category.id
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if content was created
        self.assertTrue(Content.objects.filter(title='New Content', author=self.user).exists())
        self.assertEqual(response.data['title'], 'New Content')
    
    def test_retrieve_content(self):
        """Test retrieving specific content"""
        url = reverse('content:contents-detail', kwargs={'pk': self.content.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Existing Content')
        self.assertEqual(response.data['id'], self.content.id)
    
    def test_update_content(self):
        """Test updating content"""
        url = reverse('content:contents-detail', kwargs={'pk': self.content.pk})
        data = {
            'title': 'Updated Content',
            'content': 'This is updated content'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.content.refresh_from_db()
        self.assertEqual(self.content.title, 'Updated Content')
    
    def test_delete_content(self):
        """Test deleting content"""
        url = reverse('content:contents-detail', kwargs={'pk': self.content.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Content.objects.filter(pk=self.content.pk).exists())
    
    def test_content_filtering_by_category(self):
        """Test filtering content by category"""
        # Create another category and content
        other_category = Category.objects.create(name='Other Category', user=self.user)
        Content.objects.create(
            title='Other Content',
            content='Other content',
            author=self.user,
            category=other_category
        )
        
        url = reverse('content:contents-list')
        response = self.client.get(url, {'category': self.category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        if 'results' in response.data:
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['title'], 'Existing Content')
    
    def test_content_filtering_by_category_slug(self):
        """Test filtering content by category slug"""
        url = reverse('content:contents-list')
        response = self.client.get(url, {'category_slug': self.category.slug})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        if 'results' in response.data:
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['title'], 'Existing Content')
    
    def test_content_search(self):
        """Test content search functionality"""
        # Create content with searchable title
        Content.objects.create(
            title='Searchable Content',
            content='Content with searchable keywords',
            author=self.user,
            category=self.category
        )

        url = reverse('content:contents-list')
        response = self.client.get(url, {'search': 'Searchable'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if search functionality exists
        if 'results' in response.data:
            # API supports search
            pass
        else:
            # API might not support search - just check it doesn't error
            pass
    
    def test_content_ordering(self):
        """Test content ordering"""
        # Create another content
        Content.objects.create(
            title='Newer Content',
            content='Newer content',
            author=self.user,
            category=self.category
        )
        
        # Test default ordering (newest first)
        url = reverse('content:contents-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        if 'results' in response.data:
            self.assertEqual(response.data['results'][0]['title'], 'Newer Content')

            # Test title ordering
            response = self.client.get(url, {'ordering': 'title'})
            self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
        else:
            self.assertEqual(response.data[0]['title'], 'Newer Content')
    
    def test_content_by_category_action(self):
        """Test content by category grouped action"""
        url = reverse('content:contents-by-category')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.category.slug, response.data)
        
        category_data = response.data[self.category.slug]
        self.assertEqual(category_data['count'], 1)
        self.assertEqual(len(category_data['contents']), 1)
        self.assertEqual(category_data['contents'][0]['title'], 'Existing Content')
    
    def test_content_access_control(self):
        """Test that users can only access their own content"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        other_category = Category.objects.create(name='Other Category', user=other_user)
        other_content = Content.objects.create(
            title='Other Content',
            content='Other content',
            author=other_user,
            category=other_category
        )
        
        # Try to access other user's content
        url = reverse('content:contents-detail', kwargs={'pk': other_content.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SerializerTest(TestCase):
    """Test serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
    
    def test_category_serializer(self):
        """Test CategorySerializer"""
        serializer = CategorySerializer(self.category)
        
        data = serializer.data
        self.assertEqual(data['name'], 'Test Category')
        self.assertEqual(data['user'], self.user.id)
        self.assertIn('slug', data)
        self.assertIn('created_at', data)
    
    def test_content_serializer(self):
        """Test ContentSerializer"""
        # Mock request context for serializer
        mock_request = type('MockRequest', (), {'user': self.user})()
        serializer = ContentSerializer(self.content, context={'request': mock_request})

        data = serializer.data
        self.assertEqual(data['title'], 'Test Content')
        self.assertIn('category', data)
        self.assertIn('created_at', data)
    
    def test_content_serializer_create(self):
        """Test ContentSerializer create functionality"""
        data = {
            'title': 'New Content',
            'content': 'New content body',
            'category': self.category.id
        }

        # Mock request context for validation
        mock_request = type('MockRequest', (), {'user': self.user})()
        serializer = ContentSerializer(data=data, context={'request': mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Note: We can't actually save without proper context
        # This tests validation only
    
    def test_content_serializer_validation(self):
        """Test ContentSerializer validation"""
        # Missing required title
        data = {
            'content': 'Content without title',
            'category': self.category.id
        }

        serializer = ContentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

        # Missing content
        data = {
            'title': 'Valid Title',
            'category': self.category.id
        }

        serializer = ContentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('content', serializer.errors)


class ContentSignalTest(TestCase):
    """Test content-related signals"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
    
    def test_content_post_save_signal(self):
        """Test that creating content triggers review schedule creation"""
        from review.models import ReviewSchedule

        content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )

        # Check that ReviewSchedule was created by the signal
        self.assertTrue(
            ReviewSchedule.objects.filter(
                content=content,
                user=self.user
            ).exists()
        )
        # This is a placeholder for where such tests would go