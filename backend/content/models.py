from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import slugify
from resee.models import BaseModel, BaseUserModel

User = get_user_model()


class Category(BaseModel):
    """Content category"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = [['name', 'user'], ['slug', 'user']]
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Handle cases where slugify returns empty string (e.g., emojis)
            if not self.slug:
                # Use a fallback slug based on the category ID or a unique identifier
                import uuid
                self.slug = f"category-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)


class Content(BaseModel):
    """Learning content"""
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('medium', '보통'),
        ('high', '높음'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField(help_text='Markdown content')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contents')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at'], name='content_author_created'),
            models.Index(fields=['author', 'category', '-created_at'], name='content_author_category_created'),
            models.Index(fields=['category', '-created_at'], name='content_category_created'),
            models.Index(fields=['priority', '-created_at'], name='content_priority_created'),
        ]
    
    def __str__(self):
        return self.title