"""Base models for AI Review functionality."""
from django.db import models
from resee.models import BaseModel


class AIQuestionType(BaseModel):
    """Types of AI-generated questions."""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('blur_processing', 'Blur Processing'),
    ]
    
    name = models.CharField(
        max_length=50,
        choices=QUESTION_TYPES,
        unique=True,
        help_text="Internal name for the question type"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable name for the question type"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of how this question type works"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this question type is available for generation"
    )
    
    class Meta:
        db_table = 'ai_question_types'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name