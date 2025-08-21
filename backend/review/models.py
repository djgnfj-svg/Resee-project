from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from resee.models import BaseUserModel

User = get_user_model()


class ReviewSchedule(BaseUserModel):
    """Review schedule for content"""
    content = models.ForeignKey('content.Content', on_delete=models.CASCADE, related_name='review_schedules')
    next_review_date = models.DateTimeField()
    interval_index = models.IntegerField(default=0, help_text='Index in REVIEW_INTERVALS')
    is_active = models.BooleanField(default=True)
    initial_review_completed = models.BooleanField(default=False, help_text='Whether the initial review has been completed')
    
    class Meta:
        unique_together = ['content', 'user']
        ordering = ['next_review_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} - {self.next_review_date}"
    
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
        
        # Handle case where current index exceeds new subscription limits
        if self.interval_index >= len(intervals):
            self.interval_index = len(intervals) - 1
        elif self.interval_index < len(intervals) - 1:
            self.interval_index += 1
        
        # Ensure we don't exceed subscription limits
        max_allowed_index = len(intervals) - 1
        if self.interval_index > max_allowed_index:
            self.interval_index = max_allowed_index
        
        next_interval = intervals[self.interval_index]
        
        # Additional safety check: ensure interval doesn't exceed user's max allowed
        user_max_interval = self.user.get_max_review_interval()
        if next_interval > user_max_interval:
            # Find the highest allowed interval for this user
            allowed_intervals = [i for i in intervals if i <= user_max_interval]
            if allowed_intervals:
                next_interval = max(allowed_intervals)
                # Update interval_index to match the corrected interval
                try:
                    self.interval_index = intervals.index(next_interval)
                except ValueError:
                    # Fallback to the last allowed interval
                    self.interval_index = len(allowed_intervals) - 1
                    next_interval = allowed_intervals[-1]
            else:
                # Fallback to minimum interval if no intervals are allowed (shouldn't happen)
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
    
    content = models.ForeignKey('content.Content', on_delete=models.CASCADE, related_name='review_history')
    review_date = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    time_spent = models.IntegerField(help_text='Time spent in seconds', null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-review_date']
        verbose_name_plural = 'Review histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} - {self.result}"