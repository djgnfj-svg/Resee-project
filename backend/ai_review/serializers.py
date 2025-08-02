"""
Serializers for AI Review API
"""
from rest_framework import serializers

from content.models import Content

from .models import AIQuestionType, AIQuestion, AIEvaluation, AIReviewSession


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


class AIChatRequestSerializer(serializers.Serializer):
    """Serializer for AI chat request"""
    content_id = serializers.IntegerField()
    message = serializers.CharField(max_length=1000)
    
    def validate_content_id(self, value):
        """Validate that content exists and belongs to the user"""
        user = self.context['request'].user
        try:
            Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("콘텐츠를 찾을 수 없거나 접근 권한이 없습니다.")
        return value


class AIChatResponseSerializer(serializers.Serializer):
    """Serializer for AI chat response"""
    message = serializers.CharField()
    response = serializers.CharField()
    ai_model_used = serializers.CharField(required=False)
    processing_time_ms = serializers.IntegerField(required=False)
    content_title = serializers.CharField(required=False)