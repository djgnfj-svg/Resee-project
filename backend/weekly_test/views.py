from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
import random

from .models import WeeklyTest, WeeklyTestQuestion, WeeklyTestAnswer
from .serializers import (
    WeeklyTestSerializer, WeeklyTestListSerializer,
    WeeklyTestQuestionSerializer, SubmitAnswerSerializer,
    StartTestSerializer, CompleteTestSerializer
)
from content.models import Content
from resee.mixins import UserOwnershipMixin


class WeeklyTestListCreateView(UserOwnershipMixin, generics.ListCreateAPIView):
    """주간 시험 목록 조회 및 생성"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WeeklyTest.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WeeklyTestSerializer
        return WeeklyTestListSerializer

    def perform_create(self, serializer):
        """시험 생성 시 자동으로 문제 생성"""
        weekly_test = serializer.save(user=self.request.user)

        # AI 사용 불가능하면 preparing 상태로 설정
        if not self._is_ai_available():
            weekly_test.status = 'preparing'
            weekly_test.save()

        self._generate_questions(weekly_test)

    def create(self, request, *args, **kwargs):
        """Create 메서드 오버라이드로 중복 검사 및 주간 제한 확인"""
        from rest_framework.exceptions import ValidationError
        from datetime import datetime, timedelta
        from django.conf import settings
        from django.utils import timezone

        user = request.user

        # 날짜가 제공되지 않았다면 기본값 계산 (시리얼라이저와 동일한 로직)
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        if not end_date:
            end_date = timezone.now().date()
        else:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        if not start_date:
            start_date = end_date - timedelta(days=7)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        # 기존 같은 기간의 시험이 있는지 확인
        existing_test = WeeklyTest.objects.filter(
            user=user,
            start_date=start_date,
            end_date=end_date
        ).first()

        if existing_test:
            raise ValidationError({
                'detail': f'{start_date} ~ {end_date} 기간의 주간 시험이 이미 존재합니다.'
            })

        # 주간 시험 생성 제한 확인 (모든 티어에서 주당 1회)
        # 같은 주에 생성된 시험이 있는지 확인 (월요일 기준 주차)
        week_start = start_date - timedelta(days=start_date.weekday())
        week_end = week_start + timedelta(days=6)

        tests_this_week = WeeklyTest.objects.filter(
            user=user,
            start_date__gte=week_start,
            start_date__lte=week_end
        ).count()

        # 구독 설정에서 주간 제한 확인
        subscription_settings = settings.SUBSCRIPTION_SETTINGS
        user_tier = getattr(user, 'subscription_tier', 'FREE')
        tier_limits = subscription_settings.get(f'{user_tier}_TIER_LIMITS', subscription_settings['FREE_TIER_LIMITS'])
        max_weekly_tests = tier_limits.get('max_weekly_tests_per_week', 1)

        if tests_this_week >= max_weekly_tests:
            raise ValidationError({
                'detail': f'주간 시험은 주당 {max_weekly_tests}회만 생성할 수 있습니다. 이번 주에 이미 {tests_this_week}개의 시험을 생성했습니다.'
            })

        return super().create(request, *args, **kwargs)

    def _generate_questions(self, weekly_test):
        """선택된 카테고리 콘텐츠를 기반으로 문제 자동 생성"""
        from django.db.models import Q

        # 기본 쿼리: 해당 기간의 사용자 콘텐츠
        content_query = Q(
            author=self.request.user,
            created_at__date__gte=weekly_test.start_date,
            created_at__date__lte=weekly_test.end_date
        )

        # 카테고리 필터 적용 (serializer에서 전달받은 경우)
        if hasattr(weekly_test, '_selected_category_ids') and weekly_test._selected_category_ids:
            content_query &= Q(category_id__in=weekly_test._selected_category_ids)

        # 200자 이상 콘텐츠만 선택, 최대 10개, 랜덤 순서
        contents = Content.objects.filter(content_query).extra(
            where=["LENGTH(content) >= %s"],
            params=[200]
        ).order_by('?')[:10]

        if not contents.exists():
            return

        question_order = 1
        for content in contents:
            # AI API 사용 가능 여부 확인
            if self._is_ai_available():
                self._create_ai_question(weekly_test, content, question_order)
            else:
                self._create_simple_question(weekly_test, content, question_order)
            question_order += 1

        # 총 문제 수 업데이트
        weekly_test.total_questions = weekly_test.questions.count()

        # 문제 생성 완료 후 preparing 상태를 pending으로 변경
        if weekly_test.status == 'preparing':
            weekly_test.status = 'pending'

        weekly_test.save()

    def _is_ai_available(self):
        """AI API 사용 가능 여부 확인"""
        from .ai_service import ai_question_generator
        return ai_question_generator.is_available()

    def _create_ai_question(self, weekly_test, content, order):
        """AI를 사용한 고급 문제 생성"""
        from .ai_service import ai_question_generator

        try:
            # AI로 문제 생성 시도
            question_data = ai_question_generator.generate_question(content)

            if question_data:
                # AI가 성공적으로 문제를 생성한 경우
                WeeklyTestQuestion.objects.create(
                    weekly_test=weekly_test,
                    content=content,
                    question_type=question_data['question_type'],
                    question_text=question_data['question_text'],
                    choices=question_data.get('choices'),
                    correct_answer=question_data['correct_answer'],
                    explanation=question_data['explanation'],
                    order=order,
                    points=10
                )
                return True
            else:
                # AI 문제 생성 실패 시 fallback
                self._create_simple_question(weekly_test, content, order)
                return False

        except Exception as e:
            # 예외 발생 시 fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"AI 문제 생성 중 오류 발생: {e}")
            self._create_simple_question(weekly_test, content, order)
            return False

    def _create_simple_question(self, weekly_test, content, order):
        """간단한 문제 생성 (AI 없이) - 개선된 버전"""
        import re

        # 콘텐츠에서 의미있는 문장 추출
        sentences = self._extract_meaningful_sentences(content.content)

        if not sentences:
            # 문장 추출 실패 시 전체 내용 사용
            sentences = [content.content[:200]]

        # 첫 번째 의미있는 문장을 문제로 사용
        selected_sentence = sentences[0] if sentences else content.content[:200]

        # O/X 문제 생성 (50% 확률로 O 또는 X)
        is_correct_statement = random.choice([True, False])

        if is_correct_statement:
            # 실제 내용을 그대로 사용 (정답: O)
            question_text = f"'{content.title}'에 대한 다음 설명이 맞습니까? (O/X)\n\n{selected_sentence}"
            correct_answer = "O"
            explanation = f"O - 학습 내용에 정확히 포함된 내용입니다."
        else:
            # 내용을 살짝 변형하여 오답 생성 (정답: X)
            modified_sentence = self._create_modified_statement(content.title, selected_sentence)
            question_text = f"'{content.title}'에 대한 다음 설명이 맞습니까? (O/X)\n\n{modified_sentence}"
            correct_answer = "X"
            explanation = f"X - 학습 내용과 다릅니다. 정확한 내용: {selected_sentence[:100]}..."

        WeeklyTestQuestion.objects.create(
            weekly_test=weekly_test,
            content=content,
            question_type='true_false',
            question_text=question_text,
            choices=None,
            correct_answer=correct_answer,
            explanation=explanation,
            order=order,
            points=10
        )

    def _extract_meaningful_sentences(self, text):
        """텍스트에서 의미있는 문장 추출"""
        import re

        # 마크다운 헤더, 코드 블록 등 제거
        text = re.sub(r'#+\s+', '', text)  # 헤더 제거
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # 코드 블록 제거
        text = re.sub(r'`[^`]+`', '', text)  # 인라인 코드 제거

        # 문장 분리 (. ! ? 기준)
        sentences = re.split(r'[.!?]\s+', text)

        # 의미있는 길이의 문장만 필터링 (50-300자)
        meaningful = [s.strip() for s in sentences if 50 <= len(s.strip()) <= 300]

        return meaningful[:3]  # 최대 3개 반환

    def _create_modified_statement(self, title, original_sentence):
        """문장을 살짝 변형하여 오답 생성"""
        # 간단한 부정 또는 수정을 통해 오답 만들기
        modifications = [
            f"{original_sentence.replace('입니다', '가 아닙니다').replace('합니다', '하지 않습니다')}",
            f"{title}은(는) 다른 개념과 관련이 없습니다.",
            f"{original_sentence[:50]}... 는 잘못된 설명입니다.",
        ]

        return random.choice(modifications)


class WeeklyTestDetailView(UserOwnershipMixin, generics.RetrieveUpdateDestroyAPIView):
    """주간 시험 상세 조회/수정/삭제"""

    serializer_class = WeeklyTestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WeeklyTest.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_test(request):
    """시험 시작"""
    serializer = StartTestSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        test_id = serializer.validated_data['test_id']
        weekly_test = WeeklyTest.objects.get(id=test_id)

        # 시험 상태 업데이트
        weekly_test.status = 'in_progress'
        weekly_test.started_at = timezone.now()
        weekly_test.save()

        # 시험 정보 반환
        test_serializer = WeeklyTestSerializer(weekly_test)
        return Response({
            'message': '시험이 시작되었습니다.',
            'test': test_serializer.data
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    """답변 제출"""
    serializer = SubmitAnswerSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        question_id = serializer.validated_data['question_id']
        user_answer = serializer.validated_data['user_answer']

        question = WeeklyTestQuestion.objects.get(id=question_id)

        # 기존 답변이 있으면 업데이트, 없으면 생성
        answer, created = WeeklyTestAnswer.objects.get_or_create(
            question=question,
            user=request.user,
            defaults={'user_answer': user_answer}
        )

        if not created:
            answer.user_answer = user_answer
            answer.save()

        return Response({
            'message': '답변이 저장되었습니다.',
            'answer_id': answer.id,
            'is_correct': answer.is_correct,
            'points_earned': answer.points_earned
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_test(request):
    """시험 완료"""
    serializer = CompleteTestSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        test_id = serializer.validated_data['test_id']
        weekly_test = WeeklyTest.objects.get(id=test_id)

        # 시험 완료 처리
        weekly_test.status = 'completed'
        weekly_test.completed_at = timezone.now()

        # 소요 시간 계산
        if weekly_test.started_at:
            weekly_test.time_spent = weekly_test.completed_at - weekly_test.started_at

        # 점수 계산
        answered_questions = WeeklyTestAnswer.objects.filter(
            question__weekly_test=weekly_test,
            user=request.user
        )

        weekly_test.correct_answers = answered_questions.filter(is_correct=True).count()
        weekly_test.calculate_score()

        return Response({
            'message': '시험이 완료되었습니다.',
            'score_percentage': weekly_test.score_percentage,
            'correct_answers': weekly_test.correct_answers,
            'total_questions': weekly_test.total_questions,
            'time_spent': str(weekly_test.time_spent) if weekly_test.time_spent else None
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_results(request, test_id):
    """시험 결과 조회"""
    try:
        weekly_test = WeeklyTest.objects.get(id=test_id, user=request.user)

        if weekly_test.status != 'completed':
            return Response({
                'error': '완료된 시험이 아닙니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 답변 내역 조회
        answers = WeeklyTestAnswer.objects.filter(
            question__weekly_test=weekly_test,
            user=request.user
        ).select_related('question', 'question__content')

        result_data = {
            'test': WeeklyTestSerializer(weekly_test).data,
            'answers': []
        }

        for answer in answers:
            result_data['answers'].append({
                'question': {
                    'id': answer.question.id,
                    'question_text': answer.question.question_text,
                    'question_type': answer.question.question_type,
                    'correct_answer': answer.question.correct_answer,
                    'explanation': answer.question.explanation,
                    'content_title': answer.question.content.title
                },
                'user_answer': answer.user_answer,
                'is_correct': answer.is_correct,
                'points_earned': answer.points_earned,
                'ai_score': answer.ai_score,
                'ai_feedback': answer.ai_feedback
            })

        return Response(result_data, status=status.HTTP_200_OK)

    except WeeklyTest.DoesNotExist:
        return Response({
            'error': '존재하지 않는 시험입니다.'
        }, status=status.HTTP_404_NOT_FOUND)
