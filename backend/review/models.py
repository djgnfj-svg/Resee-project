from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class ReviewSchedule(models.Model):
    """Review schedule for content"""
    content = models.ForeignKey('content.Content', on_delete=models.CASCADE, related_name='review_schedules')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_schedules')
    next_review_date = models.DateTimeField()
    interval_index = models.IntegerField(default=0, help_text='Index in REVIEW_INTERVALS')
    is_active = models.BooleanField(default=True)
    initial_review_completed = models.BooleanField(default=False, help_text='Whether the initial review has been completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        """Advance to next review interval"""
        from .utils import get_review_intervals
        intervals = get_review_intervals(self.user)
        
        # Handle case where current index exceeds new subscription limits
        if self.interval_index >= len(intervals):
            self.interval_index = len(intervals) - 1
        elif self.interval_index < len(intervals) - 1:
            self.interval_index += 1
        
        next_interval = intervals[self.interval_index]
        self.next_review_date = timezone.now() + timedelta(days=next_interval)
        self.save()
    
    def reset_schedule(self):
        """Reset to first interval (for failed reviews)"""
        from .utils import get_review_intervals
        self.interval_index = 0
        intervals = get_review_intervals(self.user)
        self.next_review_date = timezone.now() + timedelta(days=intervals[0])
        self.save()


class ReviewHistory(models.Model):
    """History of review sessions"""
    RESULT_CHOICES = [
        ('remembered', '기억함'),
        ('partial', '애매함'),
        ('forgot', '모름'),
    ]
    
    content = models.ForeignKey('content.Content', on_delete=models.CASCADE, related_name='review_history')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_history')
    review_date = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    time_spent = models.IntegerField(help_text='Time spent in seconds', null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-review_date']
        verbose_name_plural = 'Review histories'
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} - {self.result}"