"""
AI Service 테스트

LangGraph 기반 Distractor 생성 품질 검증
"""

import pytest
from django.test import TestCase

from accounts.models import User
from ai_services import ai_question_generator
from content.models import Category, Content


@pytest.mark.django_db
class TestAIQuestionGenerator(TestCase):
    """AI Question Generator 테스트"""

    def setUp(self):
        """테스트 데이터 생성"""
        # 사용자 생성
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )

        # 카테고리 생성
        self.category = Category.objects.create(
            name='Python 기초',
            user=self.user
        )

        # 콘텐츠 생성
        self.content = Content.objects.create(
            title='Python 리스트 이해하기',
            content="""
            리스트(List)는 Python의 가장 기본적인 자료구조 중 하나입니다.

            **핵심 특징:**
            1. 순서가 있는 시퀀스 (ordered sequence)
            2. 가변적 (mutable) - 생성 후 수정 가능
            3. 다양한 타입의 요소를 담을 수 있음
            4. 대괄호 []로 표현
            5. 인덱스는 0부터 시작

            **예시:**
            ```python
            my_list = [1, 2, 3, "hello", True]
            my_list[0]  # 1 (첫 번째 요소)
            my_list.append(4)  # [1, 2, 3, "hello", True, 4]
            ```

            리스트는 mutable하기 때문에 append(), insert(), remove() 등의
            메서드로 자유롭게 요소를 추가, 삭제, 수정할 수 있습니다.
            """,
            author=self.user,
            category=self.category,
            is_ai_validated=True,
            ai_validation_score=95
        )

    def test_ai_availability(self):
        """AI 서비스 사용 가능 여부 테스트"""
        self.assertTrue(ai_question_generator.is_available())

    def test_generate_question_success(self):
        """문제 생성 성공 케이스"""
        result = ai_question_generator.generate_question(self.content)

        # 기본 구조 검증
        self.assertIsNotNone(result)
        self.assertIn('question_type', result)
        self.assertIn('question_text', result)
        self.assertIn('choices', result)
        self.assertIn('correct_answer', result)
        self.assertIn('explanation', result)
        self.assertIn('metadata', result)

        # 객관식 검증
        self.assertEqual(result['question_type'], 'multiple_choice')
        self.assertEqual(len(result['choices']), 4)
        self.assertIn(result['correct_answer'], result['choices'])

        # 메타데이터 검증
        metadata = result['metadata']
        self.assertIn('quality_score', metadata)
        self.assertIn('version', metadata)
        self.assertEqual(metadata['version'], 'langgraph')

    def test_distractor_quality(self):
        """Distractor 품질 테스트"""
        result = ai_question_generator.generate_question(self.content)

        if not result:
            self.skipTest("AI 문제 생성 실패")

        choices = result['choices']
        correct_answer = result['correct_answer']

        # 길이 균형 검증
        lengths = [len(c) for c in choices]
        avg_len = sum(lengths) / len(lengths)
        max_deviation = max(abs(l - avg_len) for l in lengths)

        # 평균 길이의 50% 이내 편차 허용
        self.assertLess(
            max_deviation,
            avg_len * 0.5,
            "선택지 길이 편차가 너무 큼"
        )

    def test_multiple_generations(self):
        """여러 번 생성 시 일관성 테스트"""
        results = []

        for i in range(2):
            result = ai_question_generator.generate_question(self.content)
            if result:
                results.append(result)

        if len(results) < 2:
            self.skipTest("연속 생성 실패")

        # 모두 4개의 선택지를 가지는지
        for result in results:
            self.assertEqual(len(result['choices']), 4)
