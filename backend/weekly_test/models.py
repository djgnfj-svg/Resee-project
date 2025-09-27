from django.db import models
from django.contrib.auth import get_user_model
from content.models import Content

User = get_user_model()


class WeeklyTest(models.Model):
    """주간 시험 모델"""

    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('preparing', '준비중'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_tests')
    title = models.CharField(max_length=200, default='주간 시험')
    description = models.TextField(blank=True)

    # 시험 기간 설정
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # 시험 상태
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # 점수 및 통계
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(null=True, blank=True)

    # 시간 추적
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'start_date', 'end_date']

    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.start_date} ~ {self.end_date})"

    def calculate_score(self):
        """점수 계산"""
        if self.total_questions > 0:
            self.score_percentage = (self.correct_answers / self.total_questions) * 100
        else:
            self.score_percentage = 0
        self.save()
        return self.score_percentage


class WeeklyTestQuestion(models.Model):
    """주간 시험 문제"""

    QUESTION_TYPES = [
        ('multiple_choice', '객관식'),
        ('true_false', 'O/X'),
    ]

    weekly_test = models.ForeignKey(WeeklyTest, on_delete=models.CASCADE, related_name='questions')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='test_questions')

    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    question_text = models.TextField()

    # 객관식 선택지 (JSON 형태로 저장)
    choices = models.JSONField(null=True, blank=True)
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=1)
    points = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['weekly_test', 'order']

    def __str__(self):
        return f"{self.weekly_test.title} - Q{self.order}: {self.question_text[:50]}"


class WeeklyTestAnswer(models.Model):
    """사용자 답변"""

    question = models.ForeignKey(WeeklyTestQuestion, on_delete=models.CASCADE, related_name='answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    user_answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)

    # AI 평가 (주관식용)
    ai_score = models.FloatField(null=True, blank=True)  # 0-100 점수
    ai_feedback = models.TextField(blank=True)

    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['question', 'user']

    def __str__(self):
        return f"{self.user.email} - {self.question.question_text[:30]} - {'✓' if self.is_correct else '✗'}"

    def save(self, *args, **kwargs):
        """답변 저장 시 정답 여부 확인"""
        # 객관식/O/X만 지원
        self.is_correct = self.user_answer.strip().lower() == self.question.correct_answer.strip().lower()

        # 점수 계산
        if self.is_correct:
            self.points_earned = self.question.points
        else:
            self.points_earned = 0

        super().save(*args, **kwargs)
