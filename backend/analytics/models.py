"""
Simple learning analytics for basic statistics
"""
from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from resee.models import BaseModel

User = get_user_model()


class DailyStats(BaseModel):
    """
    Track basic daily learning statistics
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField(db_index=True)

    # Basic learning metrics
    contents_created = models.IntegerField(default=0, help_text="Contents created today")
    reviews_completed = models.IntegerField(default=0, help_text="Reviews completed today")
    success_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Daily success rate percentage"
    )
    study_streak_days = models.IntegerField(default=0, help_text="Current study streak")

    class Meta:
        db_table = 'analytics_daily_stats'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date}"