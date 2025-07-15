"""
Tests for content app
"""
import pytest
from django.contrib.auth import get_user_model
from content.models import Category, Tag, Content

User = get_user_model()


class TestCategoryModel:
    """Test Category model"""
    
    @pytest.mark.django_db
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Python',
            description='Python programming language'
        )
        
        assert category.name == 'Python'
        assert category.slug == 'python'
        assert category.description == 'Python programming language'
        assert str(category) == 'Python'
    
    @pytest.mark.django_db
    def test_category_slug_auto_generation(self):
        """Test category slug is auto-generated from name"""
        category = Category.objects.create(name='Machine Learning')
        assert category.slug == 'machine-learning'
    
    @pytest.mark.django_db
    def test_category_unique_name(self):
        """Test category name must be unique"""
        Category.objects.create(name='Python')
        
        with pytest.raises(Exception):  # IntegrityError
            Category.objects.create(name='Python')


class TestTagModel:
    """Test Tag model"""
    
    @pytest.mark.django_db
    def test_create_tag(self):
        """Test creating a tag"""
        tag = Tag.objects.create(name='algorithm')
        
        assert tag.name == 'algorithm'
        assert tag.slug == 'algorithm'
        assert str(tag) == 'algorithm'
    
    @pytest.mark.django_db
    def test_tag_slug_auto_generation(self):
        """Test tag slug is auto-generated from name"""
        tag = Tag.objects.create(name='Data Structure')
        assert tag.slug == 'data-structure'


class TestContentModel:
    """Test Content model"""
    
    @pytest.mark.django_db
    def test_create_content(self):
        """Test creating content"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        category = Category.objects.create(name='Python')
        
        content = Content.objects.create(
            title='Python Basics',
            content='# Python Basics\n\nThis is markdown content',
            author=user,
            category=category,
            priority='high'
        )
        
        assert content.title == 'Python Basics'
        assert content.author == user
        assert content.category == category
        assert content.priority == 'high'
        assert str(content) == 'Python Basics'
    
    @pytest.mark.django_db
    def test_content_with_tags(self):
        """Test content with tags"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        tag1 = Tag.objects.create(name='beginner')
        tag2 = Tag.objects.create(name='tutorial')
        
        content = Content.objects.create(
            title='Python Tutorial',
            content='Tutorial content',
            author=user
        )
        content.tags.set([tag1, tag2])
        
        assert content.tags.count() == 2
        assert tag1 in content.tags.all()
        assert tag2 in content.tags.all()
    
    @pytest.mark.django_db
    def test_content_default_priority(self):
        """Test content default priority is medium"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        content = Content.objects.create(
            title='Test Content',
            content='Content',
            author=user
        )
        
        assert content.priority == 'medium'