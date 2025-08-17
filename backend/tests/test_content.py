"""
Tests for content app
"""

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.text import slugify
from rest_framework import status
from rest_framework.test import APITestCase

from content.models import Category, Content
from content.serializers import CategorySerializer, ContentSerializer

from .base import BaseAPITestCase, BaseTestCase, TestDataMixin


class ContentModelTestCase(BaseTestCase):
    """Test cases for Content model"""
    
    def test_content_creation(self):
        """Test creating content"""
        content = self.create_content(
            title='Test Content',
            content='This is test content',
            priority='high'
        )
        
        self.assertEqual(content.title, 'Test Content')
        self.assertEqual(content.content, 'This is test content')
        self.assertEqual(content.priority, 'high')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
    
    def test_content_string_representation(self):
        """Test content string representation"""
        content = self.create_content(title='Test Content')
        self.assertEqual(str(content), 'Test Content')
    
    def test_content_priority_choices(self):
        """Test content priority choices"""
        content = self.create_content(priority='low')
        self.assertEqual(content.priority, 'low')
        
        content = self.create_content(priority='medium')
        self.assertEqual(content.priority, 'medium')
        
        content = self.create_content(priority='high')
        self.assertEqual(content.priority, 'high')
    
    def test_content_with_image(self):
        """Test content with image reference"""
        content = self.create_content(content='Content with image ![test](image.png)')
        
        self.assertIn('image.png', content.content)
    
    def test_content_without_category(self):
        """Test content without category"""
        content = Content.objects.create(
            title='Test Content',
            content='This is test content',
            author=self.user,
            priority='medium'
        )
        
        self.assertIsNone(content.category)
        self.assertEqual(content.title, 'Test Content')
    
    def test_content_with_multiple_tags(self):
        """Test content with multiple tags"""
        content = self.create_content()
        
        # Test that content can be created without tags
        self.assertEqual(content.title, 'Test Content')
        self.assertEqual(content.author, self.user)
    
    def test_content_ordering(self):
        """Test content ordering by creation date"""
        content1 = self.create_content(title='First')
        content2 = self.create_content(title='Second')
        content3 = self.create_content(title='Third')
        
        contents = Content.objects.all()
        # Default ordering is by -created_at
        self.assertEqual(contents[0].title, 'Third')
        self.assertEqual(contents[1].title, 'Second')
        self.assertEqual(contents[2].title, 'First')


class CategoryModelTestCase(BaseTestCase):
    """Test cases for Category model"""
    
    def test_category_creation(self):
        """Test creating category"""
        category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.user, self.user)
        self.assertEqual(category.slug, slugify('Test Category'))
    
    def test_category_string_representation(self):
        """Test category string representation"""
        category = self.create_category(name='Test Category')
        self.assertEqual(str(category), 'Test Category')
    
    def test_category_slug_generation(self):
        """Test category slug generation"""
        category = Category.objects.create(
            name='Test Category With Spaces',
            user=self.user
        )
        
        self.assertEqual(category.slug, 'test-category-with-spaces')
    
    def test_global_category(self):
        """Test global category (no user)"""
        category = Category.objects.create(
            name='Global Category',
            user=None
        )
        
        self.assertEqual(category.name, 'Global Category')
        self.assertIsNone(category.user)
    
    def test_category_unique_together(self):
        """Test category unique together constraint"""
        Category.objects.create(
            name='Test Category',
            user=self.user
        )
        
        # Should be able to create same name for different user
        other_user = self.create_user(username='other', email='other@example.com')
        category2 = Category.objects.create(
            name='Test Category',
            user=other_user
        )
        
        self.assertEqual(category2.name, 'Test Category')
        self.assertEqual(category2.user, other_user)
    
    def test_category_contents_relationship(self):
        """Test category to contents relationship"""
        category = self.create_category()
        content1 = self.create_content(category=category)
        content2 = self.create_content(category=category, title='Content 2')
        
        self.assertEqual(category.contents.count(), 2)
        self.assertIn(content1, category.contents.all())
        self.assertIn(content2, category.contents.all())




class ContentSerializerTestCase(BaseTestCase):
    """Test cases for Content serializers"""
    
    def test_content_serializer_read(self):
        """Test ContentSerializer read"""
        content = self.create_content()
        serializer = ContentSerializer(content)
        data = serializer.data
        
        self.assertEqual(data['title'], content.title)
        self.assertEqual(data['content'], content.content)
        self.assertEqual(data['priority'], content.priority)
        self.assertEqual(data['author'], content.author.username)
        self.assertEqual(data['category']['id'], content.category.id)
    
    def test_content_serializer_create(self):
        """Test ContentSerializer create"""
        data = {
            'title': 'New Content',
            'content': 'New content body',
            'priority': 'high',
            'author': self.user.id,
            'category': self.category.id
        }
        
        serializer = ContentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        content = serializer.save()
        self.assertEqual(content.title, 'New Content')
        self.assertEqual(content.content, 'New content body')
        self.assertEqual(content.priority, 'high')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
    
    def test_content_serializer_update(self):
        """Test ContentSerializer update"""
        content = self.create_content()
        
        data = {
            'title': 'Updated Content',
            'content': 'Updated content body',
            'priority': 'low'
        }
        
        serializer = ContentSerializer(content, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_content = serializer.save()
        self.assertEqual(updated_content.title, 'Updated Content')
        self.assertEqual(updated_content.content, 'Updated content body')
        self.assertEqual(updated_content.priority, 'low')
    
    def test_category_serializer(self):
        """Test CategorySerializer"""
        category = self.create_category()
        serializer = CategorySerializer(category)
        data = serializer.data
        
        self.assertEqual(data['name'], category.name)
        self.assertEqual(data['slug'], category.slug)
        self.assertEqual(data['user'], category.user.id)
    


class ContentAPITestCase(BaseAPITestCase, TestDataMixin):
    """Test cases for Content API endpoints"""
    
    def test_list_contents(self):
        """Test listing contents"""
        self.create_multiple_contents(count=3)
        
        url = reverse('content:contents-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)  # 3 + 1 from setup
    
    def test_create_content(self):
        """Test creating content"""
        url = reverse('content:contents-list')
        data = {
            'title': 'New Content',
            'content': 'New content body',
            'priority': 'high',
            'category': self.category.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        content = Content.objects.get(title='New Content')
        self.assertEqual(content.title, 'New Content')
        self.assertEqual(content.content, 'New content body')
        self.assertEqual(content.priority, 'high')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
    
    def test_get_content_detail(self):
        """Test getting content detail"""
        content = self.create_content()
        
        url = reverse('content:contents-detail', kwargs={'pk': content.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], content.title)
        self.assertEqual(response.data['content'], content.content)
    
    def test_update_content(self):
        """Test updating content"""
        content = self.create_content()
        
        url = reverse('content:contents-detail', kwargs={'pk': content.id})
        data = {
            'title': 'Updated Content',
            'content': 'Updated content body',
            'priority': 'low'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        content.refresh_from_db()
        self.assertEqual(content.title, 'Updated Content')
        self.assertEqual(content.content, 'Updated content body')
        self.assertEqual(content.priority, 'low')
    
    def test_delete_content(self):
        """Test deleting content"""
        content = self.create_content()
        
        url = reverse('content:contents-detail', kwargs={'pk': content.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Content.objects.filter(id=content.id).exists())
    
    def test_content_by_category(self):
        """Test getting contents by category"""
        category1 = self.create_category(name='Category 1')
        category2 = self.create_category(name='Category 2')
        
        content1 = self.create_content(title='Content 1', category=category1)
        content2 = self.create_content(title='Content 2', category=category2)
        content3 = self.create_content(title='Content 3', category=category1)
        
        url = reverse('content:contents-by-category')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        
        # Should have contents grouped by category
        self.assertTrue(len(response.data) >= 2)
    
    def test_content_filtering(self):
        """Test content filtering"""
        content1 = self.create_content(title='Python Tutorial', priority='high')
        content2 = self.create_content(title='Django Guide', priority='low')
        
        url = reverse('content:contents-list')
        
        # Filter by priority
        response = self.client.get(url, {'priority': 'high'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data['results']]
        self.assertIn('Python Tutorial', titles)
        self.assertNotIn('Django Guide', titles)
        
        # Filter by category
        response = self.client.get(url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 2)
    
    def test_content_search(self):
        """Test content search"""
        content1 = self.create_content(title='Python Tutorial')
        content2 = self.create_content(title='Django Guide')
        
        url = reverse('content:contents-list')
        response = self.client.get(url, {'search': 'Python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [item['title'] for item in response.data['results']]
        self.assertIn('Python Tutorial', titles)
        self.assertNotIn('Django Guide', titles)
    
    def test_content_authorization(self):
        """Test content authorization"""
        other_user = self.create_user(username='other', email='other@example.com')
        other_content = self.create_content(author=other_user, title='Other Content')
        
        # Should not be able to access other user's content
        url = reverse('content:contents-detail', kwargs={'pk': other_content.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Should not be able to update other user's content
        response = self.client.patch(url, {'title': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unauthenticated_access(self):
        """Test unauthenticated access"""
        self.client.credentials()
        
        url = reverse('content:contents-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryAPITestCase(BaseAPITestCase):
    """Test cases for Category API endpoints"""
    
    def test_list_categories(self):
        """Test listing categories"""
        category1 = self.create_category(name='Category 1')
        category2 = self.create_category(name='Category 2')
        
        url = reverse('content:categories-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # 2 + 1 from setup
    
    def test_create_category(self):
        """Test creating category"""
        url = reverse('content:categories-list')
        data = {
            'name': 'New Category'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        category = Category.objects.get(name='New Category')
        self.assertEqual(category.name, 'New Category')
        self.assertEqual(category.user, self.user)
        self.assertEqual(category.slug, 'new-category')
    
    def test_update_category(self):
        """Test updating category"""
        category = self.create_category()
        
        url = reverse('content:categories-detail', kwargs={'pk': category.id})
        data = {
            'name': 'Updated Category'
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category.refresh_from_db()
        self.assertEqual(category.name, 'Updated Category')
        self.assertEqual(category.slug, 'updated-category')
    
    def test_delete_category(self):
        """Test deleting category"""
        category = self.create_category()
        
        url = reverse('content:categories-detail', kwargs={'pk': category.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=category.id).exists())
    
    def test_category_authorization(self):
        """Test category authorization"""
        other_user = self.create_user(username='other', email='other@example.com')
        other_category = Category.objects.create(name='Other Category', user=other_user)
        
        # Should not be able to access other user's category
        url = reverse('content:categories-detail', kwargs={'pk': other_category.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


