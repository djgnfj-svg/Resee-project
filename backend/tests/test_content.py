"""
Tests for content app
"""

import tempfile
import os
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.text import slugify
from rest_framework import status
from rest_framework.test import APITestCase
from PIL import Image
import io

from .base import BaseTestCase, BaseAPITestCase, TestDataMixin
from content.models import Content, Category, Tag
from content.serializers import ContentSerializer, CategorySerializer, TagSerializer


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
        self.assertTrue(content.tags.filter(name='test-tag').exists())
    
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
        tag1 = Tag.objects.create(name='tag1')
        tag2 = Tag.objects.create(name='tag2')
        tag3 = Tag.objects.create(name='tag3')
        
        content = self.create_content()
        content.tags.add(tag1, tag2, tag3)
        
        self.assertEqual(content.tags.count(), 4)  # Including the default tag
        self.assertTrue(content.tags.filter(name='tag1').exists())
        self.assertTrue(content.tags.filter(name='tag2').exists())
        self.assertTrue(content.tags.filter(name='tag3').exists())
    
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


class TagModelTestCase(BaseTestCase):
    """Test cases for Tag model"""
    
    def test_tag_creation(self):
        """Test creating tag"""
        tag = Tag.objects.create(name='test-tag')
        
        self.assertEqual(tag.name, 'test-tag')
        self.assertEqual(tag.slug, 'test-tag')
    
    def test_tag_string_representation(self):
        """Test tag string representation"""
        tag = self.create_tag(name='test-tag')
        self.assertEqual(str(tag), 'test-tag')
    
    def test_tag_slug_generation(self):
        """Test tag slug generation"""
        tag = Tag.objects.create(name='Test Tag With Spaces')
        self.assertEqual(tag.slug, 'test-tag-with-spaces')
    
    def test_tag_unique_name(self):
        """Test tag unique name constraint"""
        Tag.objects.create(name='test-tag')
        
        with self.assertRaises(Exception):
            Tag.objects.create(name='test-tag')
    
    def test_tag_contents_relationship(self):
        """Test tag to contents relationship"""
        tag = self.create_tag()
        content1 = self.create_content()
        content2 = self.create_content(title='Content 2')
        
        content1.tags.add(tag)
        content2.tags.add(tag)
        
        self.assertEqual(tag.contents.count(), 2)
        self.assertIn(content1, tag.contents.all())
        self.assertIn(content2, tag.contents.all())


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
        self.assertEqual(len(data['tags']), 1)
        self.assertEqual(data['tags'][0]['name'], 'test-tag')
    
    def test_content_serializer_create(self):
        """Test ContentSerializer create"""
        tag1 = Tag.objects.create(name='tag1')
        tag2 = Tag.objects.create(name='tag2')
        
        data = {
            'title': 'New Content',
            'content': 'New content body',
            'priority': 'high',
            'author': self.user.id,
            'category': self.category.id,
            'tag_ids': [tag1.id, tag2.id]
        }
        
        serializer = ContentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        content = serializer.save()
        self.assertEqual(content.title, 'New Content')
        self.assertEqual(content.content, 'New content body')
        self.assertEqual(content.priority, 'high')
        self.assertEqual(content.author, self.user)
        self.assertEqual(content.category, self.category)
        self.assertEqual(content.tags.count(), 2)
    
    def test_content_serializer_update(self):
        """Test ContentSerializer update"""
        content = self.create_content()
        new_tag = Tag.objects.create(name='new-tag')
        
        data = {
            'title': 'Updated Content',
            'content': 'Updated content body',
            'priority': 'low',
            'tag_ids': [new_tag.id]
        }
        
        serializer = ContentSerializer(content, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_content = serializer.save()
        self.assertEqual(updated_content.title, 'Updated Content')
        self.assertEqual(updated_content.content, 'Updated content body')
        self.assertEqual(updated_content.priority, 'low')
        self.assertEqual(updated_content.tags.count(), 1)
        self.assertTrue(updated_content.tags.filter(name='new-tag').exists())
    
    def test_category_serializer(self):
        """Test CategorySerializer"""
        category = self.create_category()
        serializer = CategorySerializer(category)
        data = serializer.data
        
        self.assertEqual(data['name'], category.name)
        self.assertEqual(data['slug'], category.slug)
        self.assertEqual(data['user'], category.user.id)
    
    def test_tag_serializer(self):
        """Test TagSerializer"""
        tag = self.create_tag()
        serializer = TagSerializer(tag)
        data = serializer.data
        
        self.assertEqual(data['name'], tag.name)
        self.assertEqual(data['slug'], tag.slug)


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
            'category': self.category.id,
            'tag_ids': [self.tag.id]
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


class TagAPITestCase(BaseAPITestCase):
    """Test cases for Tag API endpoints"""
    
    def test_list_tags(self):
        """Test listing tags"""
        tag1 = Tag.objects.create(name='tag1')
        tag2 = Tag.objects.create(name='tag2')
        
        url = reverse('content:tags-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # 2 + 1 from setup
    
    def test_create_tag(self):
        """Test creating tag"""
        url = reverse('content:tags-list')
        data = {
            'name': 'new-tag'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        tag = Tag.objects.get(name='new-tag')
        self.assertEqual(tag.name, 'new-tag')
        self.assertEqual(tag.slug, 'new-tag')
    
    def test_tag_search(self):
        """Test tag search"""
        tag1 = Tag.objects.create(name='python')
        tag2 = Tag.objects.create(name='django')
        tag3 = Tag.objects.create(name='javascript')
        
        url = reverse('content:tags-list')
        response = self.client.get(url, {'search': 'python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item['name'] for item in response.data['results']]
        self.assertIn('python', names)
        self.assertNotIn('django', names)
        self.assertNotIn('javascript', names)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ImageUploadTestCase(BaseAPITestCase):
    """Test cases for image upload functionality"""
    
    def test_upload_image_valid(self):
        """Test uploading valid image"""
        url = reverse('content:upload-image')
        
        # Create test image
        image = self.create_test_image()
        
        response = self.client.post(url, {'image': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('url', response.data)
        self.assertIn('filename', response.data)
    
    def test_upload_image_invalid_format(self):
        """Test uploading invalid image format"""
        url = reverse('content:upload-image')
        
        # Create text file instead of image
        text_file = SimpleUploadedFile(
            "test.txt", 
            b"This is not an image", 
            content_type="text/plain"
        )
        
        response = self.client.post(url, {'image': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upload_image_too_large(self):
        """Test uploading image that's too large"""
        url = reverse('content:upload-image')
        
        # Create large image (larger than would be optimized)
        large_image = Image.new('RGB', (2000, 2000), color='red')
        file_obj = io.BytesIO()
        large_image.save(file_obj, format='PNG')
        file_obj.seek(0)
        
        large_image_file = SimpleUploadedFile(
            name='large.png',
            content=file_obj.read(),
            content_type='image/png'
        )
        
        response = self.client.post(url, {'image': large_image_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be optimized to smaller size
        self.assertIn('url', response.data)
    
    def test_upload_image_unauthenticated(self):
        """Test uploading image without authentication"""
        self.client.credentials()
        
        url = reverse('content:upload-image')
        image = self.create_test_image()
        
        response = self.client.post(url, {'image': image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_image(self):
        """Test deleting uploaded image"""
        # First upload an image
        upload_url = reverse('content:upload-image')
        image = self.create_test_image()
        
        upload_response = self.client.post(upload_url, {'image': image}, format='multipart')
        self.assertEqual(upload_response.status_code, status.HTTP_200_OK)
        
        filename = upload_response.data['filename']
        
        # Then delete it
        delete_url = reverse('content:delete-image', kwargs={'filename': filename})
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_delete_nonexistent_image(self):
        """Test deleting non-existent image"""
        url = reverse('content:delete-image', kwargs={'filename': 'nonexistent.jpg'})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def tearDown(self):
        """Clean up uploaded test files"""
        super().tearDown()
        # Clean up any uploaded files
        import shutil
        media_root = tempfile.mkdtemp()
        if os.path.exists(media_root):
            shutil.rmtree(media_root)