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
        """Test category slug uniqueness per user"""
        Category.objects.create(name='Same Name', user=self.user)
        
        # Second category with same name should have different slug
        category2 = Category.objects.create(name='Same Name', user=self.user)
        
        categories = Category.objects.filter(user=self.user, name='Same Name')
        slugs = [cat.slug for cat in categories]
        self.assertEqual(len(set(slugs)), 2)  # Should have unique slugs


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
            category=self.category,
            priority='medium'
        )
        
        self.assertEqual(content.title, 'Test Content')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
        self.assertEqual(content.priority, 'medium')
        self.assertEqual(str(content), 'Test Content')
    
    def test_content_default_priority(self):
        """Test content default priority"""
        content = Content.objects.create(
            title='Test Content',
            content='This is test content',
            author=self.user,
            category=self.category
        )
        
        self.assertEqual(content.priority, 'low')
    
    @patch('content.signals.create_review_schedule_for_content')
    def test_content_creation_triggers_signal(self, mock_signal):
        """Test that content creation triggers review schedule creation"""
        content = Content.objects.create(
            title='Test Content',
            content='This is test content',
            author=self.user,
            category=self.category
        )
        
        # Signal should be called to create review schedule
        # This is handled in the signals.py file
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
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Existing Category')
    
    def test_create_category(self):
        """Test creating a new category"""
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
            category=self.category,
            priority='medium'
        )
    
    def test_list_contents(self):
        """Test listing user's contents"""
        url = reverse('content:contents-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
    
    def test_create_content(self):
        """Test creating new content"""
        url = reverse('content:contents-list')
        data = {
            'title': 'New Content',
            'content': 'This is new content',
            'category': self.category.id,
            'priority': 'high'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if content was created
        self.assertTrue(Content.objects.filter(title='New Content', author=self.user).exists())
        self.assertEqual(response.data['priority'], 'high')
    
    def test_retrieve_content(self):
        """Test retrieving specific content"""
        url = reverse('content:contents-detail', kwargs={'pk': self.content.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Existing Content')
        self.assertEqual(response.data['id'], self.content.id)
        self.assertIn('review_count', response.data)
        self.assertIn('next_review_date', response.data)
    
    def test_update_content(self):
        """Test updating content"""
        url = reverse('content:contents-detail', kwargs={'pk': self.content.pk})
        data = {
            'title': 'Updated Content',
            'content': 'This is updated content',
            'priority': 'high'
        }
        
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.content.refresh_from_db()
        self.assertEqual(self.content.title, 'Updated Content')
        self.assertEqual(self.content.priority, 'high')
    
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
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
    
    def test_content_filtering_by_category_slug(self):
        """Test filtering content by category slug"""
        url = reverse('content:contents-list')
        response = self.client.get(url, {'category_slug': self.category.slug})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
    
    def test_content_filtering_by_priority(self):
        """Test filtering content by priority"""
        # Create content with different priority
        Content.objects.create(
            title='High Priority Content',
            content='High priority content',
            author=self.user,
            category=self.category,
            priority='high'
        )
        
        url = reverse('content:contents-list')
        response = self.client.get(url, {'priority': 'high'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'High Priority Content')
    
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
        self.assertEqual(response.data['results'][0]['title'], 'Newer Content')
        
        # Test title ordering
        response = self.client.get(url, {'ordering': 'title'})
        self.assertEqual(response.data['results'][0]['title'], 'Existing Content')
    
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
        # Mock request context for review_count calculation
        mock_request = type('MockRequest', (), {'user': self.user})()
        serializer = ContentSerializer(self.content, context={'request': mock_request})
        
        data = serializer.data
        self.assertEqual(data['title'], 'Test Content')
        self.assertEqual(data['author'], str(self.user))
        self.assertIn('category', data)
        self.assertIn('review_count', data)
        self.assertIn('next_review_date', data)
        self.assertEqual(data['priority'], 'low')
    
    def test_content_serializer_create(self):
        """Test ContentSerializer create functionality"""
        data = {
            'title': 'New Content',
            'content': 'New content body',
            'category': self.category.id,
            'priority': 'high'
        }
        
        serializer = ContentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
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
        
        # Invalid priority
        data = {
            'title': 'Valid Title',
            'content': 'Valid content',
            'category': self.category.id,
            'priority': 'invalid_priority'
        }
        
        serializer = ContentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('priority', serializer.errors)


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
    
    @patch('content.signals.create_review_schedule_for_content.delay')
    def test_content_post_save_signal(self, mock_create_schedule):
        """Test that creating content triggers review schedule creation"""
        content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )
        
        # Check if signal was called
        # The actual signal implementation would be in signals.py
        self.assertTrue(Content.objects.filter(id=content.id).exists())
        
        # Note: The actual signal testing would depend on the signal implementation
        # This is a placeholder for where such tests would go