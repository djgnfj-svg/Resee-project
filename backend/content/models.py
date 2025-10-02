from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from resee.models import BaseModel, BaseUserModel
from resee.validators import validate_content_length, validate_category_name

User = get_user_model()


class Category(BaseModel):
    """Content category"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True, max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = [['name', 'user'], ['slug', 'user']]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(name=''),
                name='category_name_not_empty'
            ),
        ]
    
    def clean(self):
        """Validate model data"""
        super().clean()
        validate_category_name(self.name)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            self.slug = slugify(self.name)
            # Handle cases where slugify returns empty string (e.g., emojis)
            if not self.slug:
                # Use a fallback slug based on the category ID or a unique identifier
                import uuid
                self.slug = f"category-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Content(BaseModel):
    """Learning content"""

    REVIEW_MODE_CHOICES = [
        ('objective', '객관식 (내용 보고 기억함/모름 선택)'),
        ('subjective', '주관식 (먼저 작성 후 AI 자동 평가)'),
    ]

    title = models.CharField(max_length=30)  # 프론트엔드와 동기화
    content = models.TextField(help_text='Markdown content')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contents')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    review_mode = models.CharField(
        max_length=20,
        choices=REVIEW_MODE_CHOICES,
        default='objective',
        help_text='Review test mode: objective or subjective with AI auto-evaluation'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at'], name='content_author_created'),
            models.Index(fields=['author', 'category', '-created_at'], name='content_auth_cat_created'),
            models.Index(fields=['category', '-created_at'], name='content_category_created'),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(title=''),
                name='content_title_not_empty'
            ),
            models.CheckConstraint(
                check=~models.Q(content=''),
                name='content_body_not_empty'
            ),
        ]
    
    def clean(self):
        """Validate model data"""
        super().clean()
        validate_content_length(self.content)

        if not self.title or not self.title.strip():
            raise ValidationError({'title': 'Title cannot be empty.'})

        # 서술 평가 모드일 때는 콘텐츠가 200자 이상이어야 함
        if self.review_mode == 'subjective':
            content_length = len(self.content.strip())
            if content_length < 200:
                raise ValidationError({
                    'content': f'서술 평가 모드는 콘텐츠가 최소 200자 이상이어야 합니다. (현재: {content_length}자)'
                })

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title