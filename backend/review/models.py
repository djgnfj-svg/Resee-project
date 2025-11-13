from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from resee.models import BaseUserModel
from resee.validators import validate_review_interval_index
from accounts.subscription.services import SubscriptionService

User = get_user_model()


class ReviewSchedule(BaseUserModel):
    """Review schedule for content"""
    content = models.ForeignKey(
        'content.Content',
        on_delete=models.CASCADE,
        related_name='review_schedules'
    )
    next_review_date = models.DateTimeField()
    interval_index = models.IntegerField(
        default=0,
        help_text='Index in REVIEW_INTERVALS'
    )
    is_active = models.BooleanField(default=True)
    initial_review_completed = models.BooleanField(
        default=False,
        help_text='Whether the initial review has been completed'
    )
    
    class Meta:
        unique_together = ['content', 'user']
        ordering = ['next_review_date']
        indexes = [
            models.Index(fields=['user', 'next_review_date', 'is_active'], name='review_sched_user_active'),
            models.Index(fields=['next_review_date'], name='review_schedule_next_date'),
            models.Index(fields=['user', 'is_active'], name='review_schedule_user_active'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(interval_index__gte=0),
                name='review_schedule_interval_index_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(next_review_date__gte=models.F('created_at')),
                name='review_schedule_next_date_after_creation',
                violation_error_message='Next review date must be after creation date'
            ),
        ]
    
    def clean(self):
        """Validate model data"""
        super().clean()

        # Validate interval index against user's subscription
        if self.user_id and self.interval_index is not None:
            validate_review_interval_index(self.interval_index, self.user)

        # Validate content belongs to same user
        if self.content and self.user and self.content.author != self.user:
            raise ValidationError({
                'content': 'Content must belong to the same user as the review schedule.'
            })

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content.title} - {self.user.email} (interval: {self.interval_index})"
    
    def get_next_interval(self):
        """Get next review interval in days"""
        from .utils import get_review_intervals
        intervals = get_review_intervals(self.user)
        if self.interval_index < len(intervals) - 1:
            return intervals[self.interval_index + 1]
        return intervals[-1]  # Stay at the longest interval
    
    def advance_schedule(self):
        """Advance to next review interval with subscription tier limits"""
        from .utils import get_review_intervals
        intervals = get_review_intervals(self.user)
        user_max_interval = SubscriptionService(self.user).get_max_review_interval()

        # Step 1: Advance interval index (if not at max)
        if self.interval_index < len(intervals) - 1:
            self.interval_index += 1

        # Step 2: Cap interval index to subscription limits
        max_allowed_index = len(intervals) - 1
        self.interval_index = min(self.interval_index, max_allowed_index)

        # Step 3: Get interval and ensure it respects subscription tier
        next_interval = intervals[self.interval_index]
        if next_interval > user_max_interval:
            # Find highest allowed interval within user's subscription
            allowed_intervals = [i for i in intervals if i <= user_max_interval]
            if allowed_intervals:
                next_interval = max(allowed_intervals)
                try:
                    self.interval_index = intervals.index(next_interval)
                except ValueError:
                    self.interval_index = len(allowed_intervals) - 1
                    next_interval = allowed_intervals[-1]
            else:
                # Fallback to first interval (shouldn't happen)
                next_interval = intervals[0]
                self.interval_index = 0

        self.next_review_date = timezone.now() + timedelta(days=next_interval)
        self.save()
    
    def reset_schedule(self):
        """Reset to first interval (for failed reviews)"""
        from .utils import get_review_intervals
        self.interval_index = 0
        intervals = get_review_intervals(self.user)
        self.next_review_date = timezone.now() + timedelta(days=intervals[0])
        self.save()


class ReviewHistory(BaseUserModel):
    """History of review sessions"""
    RESULT_CHOICES = [
        ('remembered', '기억함'),
        ('partial', '애매함'),
        ('forgot', '모름'),
    ]

    content = models.ForeignKey(
        'content.Content',
        on_delete=models.CASCADE,
        related_name='review_history'
    )
    review_date = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    time_spent = models.IntegerField(
        help_text='Time spent in seconds',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, max_length=1000)

    # AI 서술형 답변 평가 (descriptive mode)
    descriptive_answer = models.TextField(
        blank=True,
        max_length=2000,
        help_text='User descriptive answer for AI evaluation'
    )
    ai_score = models.FloatField(
        null=True,
        blank=True,
        help_text='AI evaluation score (0-100)'
    )
    ai_feedback = models.TextField(
        null=True,
        blank=True,
        help_text='AI generated feedback'
    )

    # 객관식 모드 (multiple_choice mode)
    selected_choice = models.CharField(
        max_length=100,
        blank=True,
        help_text='User selected choice for multiple choice mode'
    )

    # 주관식 모드 (subjective mode - title guessing)
    user_title = models.CharField(
        max_length=100,
        blank=True,
        help_text='User guessed title for subjective mode'
    )
    
    class Meta:
        ordering = ['-review_date']
        verbose_name_plural = 'Review histories'
        indexes = [
            models.Index(fields=['user', '-review_date'], name='review_history_user_date'),
            models.Index(fields=['content', '-review_date'], name='review_history_content_date'),
            models.Index(fields=['user', 'result', '-review_date'], name='review_hist_user_result'),
            models.Index(fields=['-review_date'], name='review_history_date_only'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(time_spent__gte=0) | models.Q(time_spent__isnull=True),
                name='review_history_time_spent_non_negative'
            ),
        ]
    
    def clean(self):
        """Validate model data"""
        super().clean()

        # Validate content belongs to same user
        if self.content and self.user and self.content.author != self.user:
            raise ValidationError({
                'content': 'Review history must belong to the same user as the content.'
            })

        # Validate time_spent is reasonable (max 24 hours)
        if self.time_spent and self.time_spent > 86400:  # 24 hours in seconds
            raise ValidationError({
                'time_spent': 'Time spent cannot exceed 24 hours (86400 seconds).'
            })

    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.content.title} - {self.result}"