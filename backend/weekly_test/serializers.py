from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from .models import WeeklyTest, WeeklyTestQuestion, WeeklyTestAnswer
from content.serializers import ContentSerializer


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
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        allow_empty=False,
        help_text="시험에 포함할 카테고리 ID 목록 (필수)"
    )

    class Meta:
        model = WeeklyTest
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'status', 'total_questions', 'correct_answers', 'score_percentage',
            'started_at', 'completed_at', 'time_spent', 'created_at', 'updated_at',
            'questions', 'user_answers', 'category_ids'
        ]
        read_only_fields = [
            'id', 'total_questions', 'correct_answers', 'score_percentage',
            'started_at', 'completed_at', 'time_spent', 'created_at', 'updated_at'
        ]

    def validate_category_ids(self, value):
        """카테고리 ID 목록 유효성 검사"""
        if value:
            from content.models import Category
            user = self.context['request'].user

            # 사용자의 카테고리인지 확인
            valid_categories = Category.objects.filter(user=user, id__in=value)
            if len(valid_categories) != len(value):
                raise serializers.ValidationError("존재하지 않거나 권한이 없는 카테고리가 포함되어 있습니다.")

        return value

    def create(self, validated_data):
        """주간 시험 생성"""
        user = self.context['request'].user
        category_ids = validated_data.pop('category_ids', None)
        validated_data['user'] = user

        # 기본 날짜 설정 (지난 일주일)
        if 'end_date' not in validated_data:
            validated_data['end_date'] = timezone.now().date()
        if 'start_date' not in validated_data:
            validated_data['start_date'] = validated_data['end_date'] - timedelta(days=7)

        # 카테고리 조건에 맞는 콘텐츠 검증
        self._validate_content_requirements(user, validated_data['start_date'], validated_data['end_date'], category_ids)

        weekly_test = super().create(validated_data)

        # 선택된 카테고리 정보를 임시로 저장 (문제 생성에서 사용)
        weekly_test._selected_category_ids = category_ids

        return weekly_test

    def _validate_content_requirements(self, user, start_date, end_date, category_ids):
        """콘텐츠 요구사항 검증"""
        from content.models import Content
        from django.db.models import Q

        # 기본 쿼리: 해당 기간의 사용자 콘텐츠
        content_query = Q(
            author=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        # 카테고리 필터 추가
        if category_ids:
            content_query &= Q(category_id__in=category_ids)

        # 콘텐츠 조건 확인: 200자 이상, 최소 10개
        valid_contents = Content.objects.filter(content_query).extra(
            where=["LENGTH(content) >= %s"],
            params=[200]
        )

        valid_count = valid_contents.count()

        if valid_count < 10:
            if category_ids:
                from content.models import Category
                category_names = list(Category.objects.filter(id__in=category_ids).values_list('name', flat=True))
                category_str = ", ".join(category_names)
                raise serializers.ValidationError(
                    f"선택한 카테고리({category_str})에 충분한 콘텐츠가 없습니다. "
                    f"현재: {valid_count}개, 필요: 최소 10개의 200자 이상 콘텐츠"
                )
            else:
                raise serializers.ValidationError(
                    f"시험 생성에 필요한 콘텐츠가 부족합니다. "
                    f"현재: {valid_count}개, 필요: 최소 10개의 200자 이상 콘텐츠"
                )


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