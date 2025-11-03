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
        ('objective', '기억 확인 (제목만 보고 기억함/모름 선택)'),
        ('descriptive', '서술형 (제목 보고 내용 작성 → AI 평가)'),
        ('multiple_choice', '객관식 (내용 보고 4지선다에서 제목 맞추기)'),
        ('subjective', '주관식 (내용 보고 제목 유추 작성 → AI 평가)'),
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

    # AI 검증 관련 필드
    is_ai_validated = models.BooleanField(
        default=False,
        help_text='AI 검증 완료 여부 (주간 시험 생성에 필수)'
    )
    ai_validation_score = models.FloatField(
        null=True,
        blank=True,
        help_text='AI 검증 평균 점수 (0-100, 3가지 항목의 평균)'
    )
    ai_validation_result = models.JSONField(
        null=True,
        blank=True,
        help_text='AI 검증 상세 결과 (factual_accuracy, logical_consistency, title_relevance)'
    )
    ai_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='AI 검증 완료 시각'
    )

    # 객관식 모드용 보기 저장
    mc_choices = models.JSONField(
        null=True,
        blank=True,
        help_text='Multiple choice options (AI generated): {"choices": [...], "correct_answer": "..."}'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at'], name='content_author_created'),
            models.Index(fields=['author', 'category', '-created_at'], name='content_auth_cat_created'),
            models.Index(fields=['category', '-created_at'], name='content_category_created'),
            models.Index(fields=['is_ai_validated', '-created_at'], name='content_ai_validated'),
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

        # AI 평가 모드(descriptive, multiple_choice, subjective)는 콘텐츠가 200자 이상이어야 함
        if self.review_mode in ['descriptive', 'multiple_choice', 'subjective']:
            content_length = len(self.content.strip())
            if content_length < 200:
                mode_names = {
                    'descriptive': '서술형',
                    'multiple_choice': '객관식',
                    'subjective': '주관식'
                }
                mode_name = mode_names.get(self.review_mode, self.review_mode)
                raise ValidationError({
                    'content': f'{mode_name} 모드는 AI 평가를 위해 콘텐츠가 최소 200자 이상이어야 합니다. (현재: {content_length}자)'
                })

    def save(self, *args, **kwargs):
        """Override save to run validation and handle AI validation reset"""
        # 기존 콘텐츠 수정 시 내용이 변경되었으면 AI 검증 상태 리셋
        if self.pk:
            try:
                old_content = Content.objects.get(pk=self.pk)
                # 제목 또는 내용이 변경되었으면 재검증 필요
                if old_content.content != self.content or old_content.title != self.title:
                    self.is_ai_validated = False
                    self.ai_validation_score = None
                    self.ai_validation_result = None
                    self.ai_validated_at = None
                    # 객관식 보기도 재생성 필요
                    if self.review_mode == 'multiple_choice':
                        self.mc_choices = None
            except Content.DoesNotExist:
                pass  # 새 콘텐츠 생성 시

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title