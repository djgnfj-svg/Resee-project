from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

from resee.models import TimestampMixin
from resee.validators import validate_category_name, validate_content_length

User = get_user_model()


class Category(TimestampMixin):
    """콘텐츠 카테고리"""

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, blank=True)
    description = models.TextField(blank=True, max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]
        unique_together = [["name", "user"], ["slug", "user"]]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(name=""), name="category_name_not_empty"
            ),
        ]

    def clean(self):
        """모델 데이터를 검증합니다"""
        super().clean()
        validate_category_name(self.name)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slug:
            self.slug = slugify(self.name)
            # slugify가 빈 문자열을 반환하는 경우 처리 (예: 이모지)
            if not self.slug:
                # 카테고리 ID 또는 고유 식별자 기반 대체 슬러그 사용
                import uuid

                self.slug = f"category-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Content(TimestampMixin):
    """학습 콘텐츠"""

    REVIEW_MODE_CHOICES = [
        ("objective", "기억 확인 (제목만 보고 기억함/모름 선택)"),
        ("descriptive", "서술형 (제목 보고 내용 작성 후 AI 평가)"),
        ("multiple_choice", "객관식 (내용 보고 4지선다에서 제목 맞추기)"),
    ]

    title = models.CharField(max_length=30)  # 프론트엔드와 동기화
    content = models.TextField(help_text="Markdown content")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contents")
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True
    )
    review_mode = models.CharField(
        max_length=20,
        choices=REVIEW_MODE_CHOICES,
        default="objective",
        help_text="Review test mode: objective or subjective with AI auto-evaluation",
    )

    def __init__(self, *args, **kwargs):
        """추가 DB 쿼리 없이 변경 감지를 위해 원본 값 저장"""
        super().__init__(*args, **kwargs)
        # 변경 감지를 위한 원본 값 저장
        self._original_title = self.title
        self._original_content = self.content

    # AI 검증 관련 필드
    is_ai_validated = models.BooleanField(
        default=False,
        help_text="Whether AI validation is completed (required for exam generation)",
    )
    ai_validation_score = models.FloatField(
        null=True,
        blank=True,
        help_text="AI validation average score (0-100, average of 3 metrics)",
    )
    ai_validation_result = models.JSONField(
        null=True,
        blank=True,
        help_text="AI validation detailed result (factual_accuracy, logical_consistency, title_relevance)",
    )
    ai_validated_at = models.DateTimeField(
        null=True, blank=True, help_text="AI validation completion timestamp"
    )

    # 객관식 모드용 보기 저장
    mc_choices = models.JSONField(
        null=True,
        blank=True,
        help_text='Multiple choice options (AI generated): {"choices": [...], "correct_answer": "..."}',
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["author", "-created_at"], name="content_author_created"
            ),
            models.Index(
                fields=["author", "category", "-created_at"],
                name="content_auth_cat_created",
            ),
            models.Index(
                fields=["category", "-created_at"], name="content_category_created"
            ),
            models.Index(
                fields=["is_ai_validated", "-created_at"], name="content_ai_validated"
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(title=""), name="content_title_not_empty"
            ),
            models.CheckConstraint(
                check=~models.Q(content=""), name="content_body_not_empty"
            ),
        ]

    def clean(self):
        """모델 데이터를 검증합니다"""
        super().clean()
        validate_content_length(self.content)

        if not self.title or not self.title.strip():
            raise ValidationError({"title": "Title cannot be empty."})

        # AI 평가 모드(서술형, 객관식)는 정확한 판단을 위해 콘텐츠가 200자 이상이어야 함
        if self.review_mode in ["descriptive", "multiple_choice"]:
            content_length = len(self.content.strip())
            if content_length < 200:
                raise ValidationError(
                    {
                        "content": f"AI 평가 모드는 정확한 판단을 위해 콘텐츠가 최소 200자 이상이어야 합니다. (현재: {content_length}자)"
                    }
                )

    def save(self, *args, **kwargs):
        """검증 실행 및 AI 검증 리셋을 처리하도록 save를 오버라이드"""
        # 제목 또는 내용이 변경되었는지 확인 (DB 쿼리 불필요)
        if self.pk and (
            self._original_content != self.content or self._original_title != self.title
        ):
            # 콘텐츠가 변경됨, AI 검증 리셋
            self.is_ai_validated = False
            self.ai_validation_score = None
            self.ai_validation_result = None
            self.ai_validated_at = None
            # 객관식 모드인 경우 MC 선택지 리셋
            if self.review_mode == "multiple_choice":
                self.mc_choices = None

        self.full_clean()
        super().save(*args, **kwargs)

        # 저장 후 원본 값 업데이트
        self._original_title = self.title
        self._original_content = self.content

    def __str__(self):
        return self.title
