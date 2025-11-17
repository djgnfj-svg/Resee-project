from django.utils import timezone
from rest_framework import serializers

from content.serializers import ContentSerializer

from .models import WeeklyTest, WeeklyTestAnswer, WeeklyTestQuestion


class WeeklyTestQuestionSerializer(serializers.ModelSerializer):
    """주간 시험 문제 시리얼라이저"""

    content = ContentSerializer(read_only=True)

    class Meta:
        model = WeeklyTestQuestion
        fields = [
            'id', 'question_type', 'question_text', 'choices',
            'correct_answer', 'explanation', 'order', 'points',
            'content', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WeeklyTestAnswerSerializer(serializers.ModelSerializer):
    """사용자 답변 시리얼라이저"""

    question = WeeklyTestQuestionSerializer(read_only=True)

    class Meta:
        model = WeeklyTestAnswer
        fields = [
            'id', 'question', 'user_answer', 'is_correct',
            'points_earned', 'ai_score', 'ai_feedback', 'answered_at'
        ]
        read_only_fields = ['id', 'is_correct', 'points_earned', 'ai_score', 'ai_feedback', 'answered_at']


class WeeklyTestSerializer(serializers.ModelSerializer):
    """주간 시험 시리얼라이저"""

    questions = WeeklyTestQuestionSerializer(many=True, read_only=True)
    user_answers = WeeklyTestAnswerSerializer(source='questions__answers', many=True, read_only=True)
    content_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,  # 자동 밸런싱 모드 지원
        min_length=7,
        max_length=10,
        help_text="시험에 포함할 콘텐츠 ID 목록 (7~10개, AI 검증 완료 필수). 비어있으면 자동 밸런싱 모드로 생성."
    )

    class Meta:
        model = WeeklyTest
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'status', 'total_questions', 'correct_answers', 'score_percentage',
            'started_at', 'completed_at', 'time_spent', 'created_at', 'updated_at',
            'questions', 'user_answers', 'content_ids'
        ]
        read_only_fields = [
            'id', 'total_questions', 'correct_answers', 'score_percentage',
            'started_at', 'completed_at', 'time_spent', 'created_at', 'updated_at'
        ]

    def validate_content_ids(self, value):
        """콘텐츠 ID 목록 유효성 검사"""
        from content.models import Content

        # 자동 밸런싱 모드 (빈 리스트 또는 None)
        if not value:
            return value

        user = self.context['request'].user

        # 중복 제거
        unique_ids = list(set(value))
        if len(unique_ids) != len(value):
            raise serializers.ValidationError("중복된 콘텐츠가 포함되어 있습니다.")

        # 콘텐츠 존재 및 소유 확인
        contents = Content.objects.filter(id__in=value, author=user)
        if contents.count() != len(value):
            raise serializers.ValidationError("유효하지 않은 콘텐츠가 포함되어 있습니다.")

        # AI 검증 확인 (핵심!)
        not_validated = contents.filter(is_ai_validated=False)
        if not_validated.exists():
            titles = list(not_validated.values_list('title', flat=True)[:3])
            count = not_validated.count()
            error_msg = f"AI 검증이 완료되지 않은 콘텐츠가 {count}개 있습니다: {', '.join(titles)}"
            if count > 3:
                error_msg += f" 외 {count - 3}개"
            raise serializers.ValidationError(error_msg)

        return value

    def create(self, validated_data):
        """주간 시험 생성"""
        user = self.context['request'].user
        content_ids = validated_data.pop('content_ids', None)
        validated_data['user'] = user

        # 생성 시각 기록
        if 'created_at' not in validated_data:
            validated_data['created_at'] = timezone.now()

        weekly_test = super().create(validated_data)

        # 선택된 콘텐츠 ID를 임시로 저장 (문제 생성에서 사용)
        weekly_test._selected_content_ids = content_ids

        return weekly_test


class WeeklyTestListSerializer(serializers.ModelSerializer):
    """주간 시험 목록용 간소화 시리얼라이저"""

    class Meta:
        model = WeeklyTest
        fields = [
            'id', 'title', 'start_date', 'end_date', 'status',
            'total_questions', 'correct_answers', 'score_percentage',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at']


class SubmitAnswerSerializer(serializers.Serializer):
    """답변 제출용 시리얼라이저"""

    question_id = serializers.IntegerField()
    user_answer = serializers.CharField()

    def validate_question_id(self, value):
        """문제 ID 유효성 검사"""
        try:
            question = WeeklyTestQuestion.objects.get(id=value)
            # 현재 사용자의 시험인지 확인
            user = self.context['request'].user
            if question.weekly_test.user != user:
                raise serializers.ValidationError("접근 권한이 없습니다.")
            return value
        except WeeklyTestQuestion.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 문제입니다.")


class StartTestSerializer(serializers.Serializer):
    """시험 시작용 시리얼라이저"""

    test_id = serializers.IntegerField()

    def validate_test_id(self, value):
        """시험 ID 유효성 검사"""
        try:
            test = WeeklyTest.objects.get(id=value)
            user = self.context['request'].user

            if test.user != user:
                raise serializers.ValidationError("접근 권한이 없습니다.")

            # pending 또는 in_progress 상태만 허용 (계속하기 기능 지원)
            if test.status not in ['pending', 'in_progress']:
                raise serializers.ValidationError("이미 완료된 시험입니다.")

            return value
        except WeeklyTest.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 시험입니다.")


class CompleteTestSerializer(serializers.Serializer):
    """시험 완료용 시리얼라이저"""

    test_id = serializers.IntegerField()

    def validate_test_id(self, value):
        """시험 ID 유효성 검사"""
        try:
            test = WeeklyTest.objects.get(id=value)
            user = self.context['request'].user

            if test.user != user:
                raise serializers.ValidationError("접근 권한이 없습니다.")

            if test.status != 'in_progress':
                raise serializers.ValidationError("진행 중인 시험이 아닙니다.")

            return value
        except WeeklyTest.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 시험입니다.")