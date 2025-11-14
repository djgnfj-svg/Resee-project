"""
주간 시험 Balance Graph 테스트

난이도 분산 콘텐츠 선택 검증
"""

import pytest
from django.test import TestCase
from content.models import Content, Category
from accounts.models import User


@pytest.mark.django_db
class TestWeeklyTestBalanceGraph(TestCase):
    """Balance Graph 기능 테스트"""

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
            name='테스트 카테고리',
            user=self.user
        )

        # 다양한 난이도의 콘텐츠 생성 (15개)
        self.contents = []

        # Easy 콘텐츠 (5개) - 단순 정의
        for i in range(5):
            content = Content.objects.create(
                title=f'기본 개념 {i+1}',
                content=f"""
                기본적인 정의입니다.

                **핵심 특징:**
                1. 명확한 개념
                2. 간단한 설명
                3. 쉬운 예시

                **예시:**
                간단한 예제입니다.
                """,
                author=self.user,
                category=self.category,
                is_ai_validated=True,
                ai_validation_score=85
            )
            self.contents.append(content)

        # Medium 콘텐츠 (7개) - 개념 이해
        for i in range(7):
            content = Content.objects.create(
                title=f'중급 개념 {i+1}',
                content=f"""
                중급 수준의 개념 설명입니다.

                **핵심 내용:**
                1. 개념 간의 관계
                2. 비교와 대조
                3. 실전 적용 방법
                4. 주의사항

                **예시:**
                실무에서 사용되는 예제입니다.
                다양한 상황에서 적용 가능합니다.
                """,
                author=self.user,
                category=self.category,
                is_ai_validated=True,
                ai_validation_score=90
            )
            self.contents.append(content)

        # Hard 콘텐츠 (3개) - 복잡한 개념
        for i in range(3):
            content = Content.objects.create(
                title=f'고급 개념 {i+1}',
                content=f"""
                고급 수준의 복잡한 개념 설명입니다.

                **심화 내용:**
                1. 복잡한 개념 간의 상호작용
                2. 고급 패턴과 원리
                3. 성능 최적화 기법
                4. 엣지 케이스 처리
                5. 실무 응용 및 분석
                6. 아키텍처 설계 원칙

                **복잡한 예시:**
                실무에서 발생하는 복잡한 시나리오를 다룹니다.
                여러 요소가 복합적으로 작용하며,
                깊은 이해가 필요한 내용입니다.
                """,
                author=self.user,
                category=self.category,
                is_ai_validated=True,
                ai_validation_score=95
            )
            self.contents.append(content)

    def test_balance_graph_integration(self):
        """Balance Graph 통합 테스트"""
        from ai_services.graphs import select_balanced_contents_for_test

        # 콘텐츠 데이터 준비
        content_data = [
            {
                'id': content.id,
                'title': content.title,
                'content': content.content
            }
            for content in self.contents
        ]

        # Balance Graph 실행 (10개 선택)
        result = select_balanced_contents_for_test(
            contents=content_data,
            target_count=10
        )

        # 기본 구조 검증
        self.assertIn('selected_content_ids', result)
        self.assertIn('balance', result)
        self.assertIn('difficulty_scores', result)

        # 선택된 개수 확인
        selected_ids = result['selected_content_ids']
        self.assertEqual(len(selected_ids), 10)

        # 밸런스 정보 확인
        balance = result['balance']
        self.assertIn('easy', balance)
        self.assertIn('medium', balance)
        self.assertIn('hard', balance)

        # 총 개수 확인
        total = balance['easy'] + balance['medium'] + balance['hard']
        self.assertEqual(total, 10)

        # 난이도 점수 확인
        difficulty_scores = result['difficulty_scores']
        self.assertEqual(len(difficulty_scores), 15)  # 전체 콘텐츠 수

        # 선택된 콘텐츠가 모두 유효한지 확인
        content_ids = [c.id for c in self.contents]
        for selected_id in selected_ids:
            self.assertIn(selected_id, content_ids)

        # 로그 출력
        print(f"\n✅ Balance Graph 테스트 성공!")
        print(f"  선택된 콘텐츠: {len(selected_ids)}개")
        print(f"  난이도 분포:")
        print(f"    - Easy: {balance['easy']}개")
        print(f"    - Medium: {balance['medium']}개")
        print(f"    - Hard: {balance['hard']}개")

    def test_balance_distribution(self):
        """난이도 분포 비율 테스트"""
        from ai_services.graphs import select_balanced_contents_for_test

        content_data = [
            {
                'id': content.id,
                'title': content.title,
                'content': content.content
            }
            for content in self.contents
        ]

        result = select_balanced_contents_for_test(
            contents=content_data,
            target_count=10
        )

        balance = result['balance']

        # 30/50/20 비율 확인 (±1 허용)
        # 10개 기준: Easy 3개, Medium 5개, Hard 2개
        expected_easy = 3
        expected_medium = 5
        expected_hard = 2

        # 허용 오차 (부족한 경우 Medium으로 채워질 수 있음)
        self.assertGreaterEqual(balance['easy'], expected_easy - 1)
        self.assertGreaterEqual(balance['medium'], expected_medium - 2)
        self.assertGreaterEqual(balance['hard'], expected_hard - 1)

        print(f"\n✅ 난이도 분포 검증")
        print(f"  목표: Easy {expected_easy}, Medium {expected_medium}, Hard {expected_hard}")
        print(f"  실제: Easy {balance['easy']}, Medium {balance['medium']}, Hard {balance['hard']}")

    def test_insufficient_contents(self):
        """콘텐츠가 부족한 경우 테스트"""
        from ai_services.graphs import select_balanced_contents_for_test

        # 5개만 선택
        content_data = [
            {
                'id': content.id,
                'title': content.title,
                'content': content.content
            }
            for content in self.contents[:5]
        ]

        result = select_balanced_contents_for_test(
            contents=content_data,
            target_count=10  # 10개 요청하지만 5개만 있음
        )

        # 5개만 선택되어야 함
        selected_ids = result['selected_content_ids']
        self.assertLessEqual(len(selected_ids), 5)

        print(f"\n✅ 부족한 콘텐츠 처리")
        print(f"  요청: 10개, 가용: 5개, 선택: {len(selected_ids)}개")
