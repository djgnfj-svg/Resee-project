"""
Serializers for AI Review API
"""
from rest_framework import serializers

from content.models import Content, Category

from .models import (AIEvaluation, AIQuestion,
                     AIQuestionType, AIReviewSession,
                     ContentUnderstandingCheck, WeeklyTest,
                     WeeklyTestQuestion)


class AIQuestionTypeSerializer(serializers.ModelSerializer):
    """Serializer for AI question types"""
    
    class Meta:
        model = AIQuestionType
        fields = ['id', 'name', 'display_name', 'description', 'is_active']
        read_only_fields = ['id']


class AIQuestionSerializer(serializers.ModelSerializer):
    """Serializer for AI questions"""
    question_type_display = serializers.CharField(source='question_type.display_name', read_only=True)
    content_title = serializers.CharField(source='content.title', read_only=True)
    
    class Meta:
        model = AIQuestion
        fields = [
            'id', 'content', 'content_title', 'question_type', 'question_type_display',
            'question_text', 'correct_answer', 'options', 'difficulty', 'explanation',
            'keywords', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GenerateQuestionsSerializer(serializers.Serializer):
    """Serializer for question generation request"""
    content_id = serializers.IntegerField()
    question_types = serializers.ListField(
        child=serializers.CharField(),
        help_text="질문 유형 이름 목록 (multiple_choice, fill_blank, blur_processing)"
    )
    difficulty = serializers.IntegerField(min_value=1, max_value=5, default=1)
    count = serializers.IntegerField(min_value=1, max_value=10, default=3)
    
    def validate_content_id(self, value):
        """Validate that content exists and belongs to the user"""
        user = self.context['request'].user
        try:
            content = Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("콘텐츠를 찾을 수 없거나 접근 권한이 없습니다.")
        return value
    
    def validate_question_types(self, value):
        """Validate that question types exist and are active"""
        valid_types = AIQuestionType.objects.filter(
            name__in=value,
            is_active=True
        ).values_list('name', flat=True)
        
        invalid_types = set(value) - set(valid_types)
        if invalid_types:
            raise serializers.ValidationError(
                f"유효하지 않거나 비활성화된 질문 유형: {list(invalid_types)}"
            )
        
        return value


class GeneratedQuestionSerializer(serializers.Serializer):
    """Serializer for generated question response"""
    question_type = serializers.CharField()
    question_text = serializers.CharField()
    correct_answer = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField(), required=False)
    explanation = serializers.CharField(required=False)
    keywords = serializers.ListField(child=serializers.CharField(), required=False)
    difficulty = serializers.IntegerField()
    ai_model_used = serializers.CharField(required=False)
    processing_time_ms = serializers.IntegerField(required=False)


class AIReviewSessionSerializer(serializers.ModelSerializer):
    """Serializer for AI review sessions"""
    user_email = serializers.CharField(source='review_history.user.email', read_only=True)
    content_title = serializers.CharField(source='review_history.content.title', read_only=True)
    
    class Meta:
        model = AIReviewSession
        fields = [
            'id', 'review_history', 'user_email', 'content_title',
            'questions_generated', 'questions_answered', 'average_score',
            'session_duration_seconds', 'ai_processing_time_ms', 'session_type',
            'completion_percentage', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'completion_percentage', 'created_at', 'updated_at']


class FillBlankRequestSerializer(serializers.Serializer):
    """Serializer for fill-in-the-blank generation request"""
    content_id = serializers.IntegerField()
    num_blanks = serializers.IntegerField(min_value=1, max_value=10, default=3)
    
    def validate_content_id(self, value):
        """Validate that content exists and belongs to the user"""
        user = self.context['request'].user
        try:
            Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("콘텐츠를 찾을 수 없거나 접근 권한이 없습니다.")
        return value


class FillBlankResponseSerializer(serializers.Serializer):
    """Serializer for fill-in-the-blank response"""
    blanked_text = serializers.CharField()
    answers = serializers.DictField()
    keywords = serializers.ListField(child=serializers.CharField())
    ai_model_used = serializers.CharField(required=False)
    processing_time_ms = serializers.IntegerField(required=False)


class BlurRegionsRequestSerializer(serializers.Serializer):
    """Serializer for blur regions generation request"""
    content_id = serializers.IntegerField()
    
    def validate_content_id(self, value):
        """Validate that content exists and belongs to the user"""
        user = self.context['request'].user
        try:
            Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("콘텐츠를 찾을 수 없거나 접근 권한이 없습니다.")
        return value


class BlurRegionSerializer(serializers.Serializer):
    """Serializer for blur region data"""
    text = serializers.CharField()
    start_pos = serializers.IntegerField()
    end_pos = serializers.IntegerField()
    importance = serializers.FloatField()
    concept_type = serializers.CharField()


class BlurRegionsResponseSerializer(serializers.Serializer):
    """Serializer for blur regions response"""
    blur_regions = BlurRegionSerializer(many=True)
    concepts = serializers.ListField(child=serializers.CharField())
    ai_model_used = serializers.CharField(required=False)
    processing_time_ms = serializers.IntegerField(required=False)




class ExplanationEvaluationRequestSerializer(serializers.Serializer):
    """Serializer for explanation evaluation request"""
    content_id = serializers.IntegerField()
    user_explanation = serializers.CharField(
        max_length=2000,
        help_text="사용자가 입력한 서술형 설명"
    )
    
    def validate_content_id(self, value):
        """Validate that content exists and belongs to the user"""
        user = self.context['request'].user
        try:
            Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("콘텐츠를 찾을 수 없거나 접근 권한이 없습니다.")
        return value
    
    def validate_user_explanation(self, value):
        """Validate user explanation is not empty"""
        if not value.strip():
            raise serializers.ValidationError("설명을 입력해주세요.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("최소 10자 이상 입력해주세요.")
        return value.strip()


class ExplanationEvaluationResponseSerializer(serializers.Serializer):
    """Serializer for explanation evaluation response"""
    score = serializers.IntegerField(
        min_value=0, 
        max_value=100,
        help_text="AI 평가 점수 (0-100)"
    )
    feedback = serializers.CharField(
        help_text="AI가 제공하는 구체적인 피드백"
    )
    strengths = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="설명의 강점들"
    )
    improvements = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="개선할 점들"
    )
    key_concepts_covered = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="다룬 핵심 개념들"
    )
    missing_concepts = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="놓친 핵심 개념들"
    )
    ai_model_used = serializers.CharField(required=False)
    processing_time_ms = serializers.IntegerField(required=False)
    content_title = serializers.CharField(required=False)


# 새로운 AI 기능 시리얼라이저들
class WeeklyTestSerializer(serializers.ModelSerializer):
    """주간 시험 시리얼라이저 - 적응형 기능 포함"""
    accuracy_rate = serializers.ReadOnlyField()
    completion_rate = serializers.ReadOnlyField()
    time_spent_minutes = serializers.ReadOnlyField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = WeeklyTest
        fields = [
            'id', 'user', 'category', 'category_name', 'week_start_date', 'week_end_date',
            'total_questions', 'completed_questions', 'correct_answers',
            'score', 'time_limit_minutes', 'started_at', 'completed_at',
            'adaptive_mode', 'current_difficulty', 'consecutive_correct', 'consecutive_wrong',
            'question_type_distribution', 'estimated_proficiency',
            'difficulty_distribution', 'content_coverage', 'weak_areas',
            'improvement_from_last_week', 'status', 'accuracy_rate',
            'completion_rate', 'time_spent_minutes', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'category_name', 'accuracy_rate', 'completion_rate',
            'time_spent_minutes', 'consecutive_correct', 'consecutive_wrong',
            'estimated_proficiency', 'created_at'
        ]


class WeeklyTestQuestionSerializer(serializers.ModelSerializer):
    """주간 시험 문제 시리얼라이저"""
    question_text = serializers.CharField(source='ai_question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='ai_question.correct_answer', read_only=True)
    options = serializers.JSONField(source='ai_question.options', read_only=True)
    difficulty = serializers.IntegerField(source='ai_question.difficulty', read_only=True)
    
    class Meta:
        model = WeeklyTestQuestion
        fields = [
            'id', 'weekly_test', 'ai_question', 'order',
            'question_text', 'correct_answer', 'options', 'difficulty',
            'user_answer', 'is_correct', 'ai_score',
            'time_spent_seconds', 'answered_at'
        ]
        read_only_fields = ['id', 'question_text', 'correct_answer', 'options', 'difficulty']


class WeeklyTestCreateSerializer(serializers.Serializer):
    """주간 시험 생성 요청 시리얼라이저 - 카테고리 선택 포함"""
    category_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="카테고리 ID (없으면 전체 콘텐츠 대상)"
    )
    time_limit_minutes = serializers.ChoiceField(
        choices=[(30, '30분'), (60, '60분'), (0, '무제한')],
        default=30
    )
    adaptive_mode = serializers.BooleanField(
        default=True,
        help_text="적응형 모드 활성화"
    )
    total_questions = serializers.IntegerField(
        default=10,
        min_value=5,
        max_value=30,
        help_text="총 문제 수"
    )
    
    def validate_category_id(self, value):
        """카테고리 유효성 검증"""
        if value is not None:
            from content.models import Category
            user = self.context['request'].user
            try:
                category = Category.objects.get(id=value, user=user)
                return value
            except Category.DoesNotExist:
                raise serializers.ValidationError("존재하지 않거나 접근 권한이 없는 카테고리입니다.")
        return value


class CategoryChoiceSerializer(serializers.ModelSerializer):
    """카테고리 선택을 위한 시리얼라이저"""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class WeeklyTestStartSerializer(serializers.Serializer):
    """주간 시험 시작 시리얼라이저"""
    test_id = serializers.IntegerField()


class WeeklyTestAnswerSerializer(serializers.Serializer):
    """주간 시험 답안 제출 시리얼라이저"""
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField(max_length=1000)
    time_spent_seconds = serializers.IntegerField(min_value=0, required=False)


class ContentUnderstandingCheckSerializer(serializers.ModelSerializer):
    """콘텐츠 이해도 검사 시리얼라이저"""
    content_title = serializers.CharField(source='content.title', read_only=True)
    accuracy_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = ContentUnderstandingCheck
        fields = [
            'id', 'user', 'content', 'content_title',
            'questions_count', 'correct_count', 'understanding_score', 'accuracy_rate',
            'weak_points', 'feedback', 'duration_seconds', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'content_title', 'accuracy_rate', 'created_at']


class UnderstandingCheckRequestSerializer(serializers.Serializer):
    """이해도 검사 요청 시리얼라이저"""
    content_id = serializers.IntegerField()
    question_count = serializers.IntegerField(min_value=1, max_value=5, default=3)
    
    def validate_content_id(self, value):
        user = self.context['request'].user
        try:
            Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("콘텐츠를 찾을 수 없거나 접근 권한이 없습니다.")
        return value




