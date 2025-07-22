"""
Serializers for AI Review API
"""
from rest_framework import serializers
from .models import AIQuestionType, AIQuestion, AIEvaluation, AIReviewSession
from content.models import Content


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
        help_text="List of question type names (multiple_choice, short_answer, etc.)"
    )
    difficulty = serializers.IntegerField(min_value=1, max_value=5, default=1)
    count = serializers.IntegerField(min_value=1, max_value=10, default=3)
    
    def validate_content_id(self, value):
        """Validate that content exists and belongs to the user"""
        user = self.context['request'].user
        try:
            content = Content.objects.get(id=value, author=user)
        except Content.DoesNotExist:
            raise serializers.ValidationError("Content not found or access denied")
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
                f"Invalid or inactive question types: {list(invalid_types)}"
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


class AIEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for AI evaluations"""
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AIEvaluation
        fields = [
            'id', 'question', 'question_text', 'user', 'user_email',
            'user_answer', 'ai_score', 'feedback', 'similarity_score',
            'evaluation_details', 'ai_model_used', 'processing_time_ms',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class EvaluateAnswerSerializer(serializers.Serializer):
    """Serializer for answer evaluation request"""
    question_id = serializers.IntegerField()
    user_answer = serializers.CharField()
    
    def validate_question_id(self, value):
        """Validate that question exists"""
        try:
            AIQuestion.objects.get(id=value, is_active=True)
        except AIQuestion.DoesNotExist:
            raise serializers.ValidationError("Question not found or inactive")
        return value


class AnswerEvaluationResultSerializer(serializers.Serializer):
    """Serializer for answer evaluation response"""
    score = serializers.FloatField()
    feedback = serializers.CharField()
    similarity_score = serializers.FloatField(required=False)
    evaluation_details = serializers.DictField(required=False)
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
            raise serializers.ValidationError("Content not found or access denied")
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
            raise serializers.ValidationError("Content not found or access denied")
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