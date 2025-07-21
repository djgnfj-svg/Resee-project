"""
종합적인 사용자 워크플로우 테스트
실제 사용자가 시스템을 사용하는 전체 플로우를 검증
"""

import time
import json
from datetime import timedelta
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from accounts.models import User
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory
from review.tasks import create_review_schedule_for_content, send_daily_review_notifications

User = get_user_model()


class FullWorkflowTestCase(APITestCase):
    """완전한 사용자 워크플로우 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.client = APIClient()
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'timezone': 'Asia/Seoul',
        }
    
    def test_complete_user_journey(self):
        """완전한 사용자 여정 테스트: 회원가입 → 로그인 → 콘텐츠 생성 → 복습 완료"""
        print("\n🚀 완전한 사용자 여정 테스트 시작")
        
        # Step 1: 회원가입
        print("1. 회원가입 테스트")
        register_url = reverse('accounts:users-list')
        response = self.client.post(register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        user_id = response.data['id']
        print(f"   ✅ 사용자 생성 완료 (ID: {user_id})")
        
        # Step 2: 로그인 및 JWT 토큰 획득
        print("2. 로그인 및 JWT 토큰 획득")
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        print(f"   ✅ JWT 토큰 획득 완료")
        
        # Step 3: 카테고리 생성
        print("3. 카테고리 생성")
        category_url = reverse('content:categories-list')
        category_data = {
            'name': '프로그래밍',
            'description': 'Python, JavaScript 등 프로그래밍 관련 학습'
        }
        response = self.client.post(category_url, category_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data['id']
        print(f"   ✅ 카테고리 생성 완료 (ID: {category_id})")
        
        # Step 4: 학습 콘텐츠 생성
        print("4. 학습 콘텐츠 생성")
        content_url = reverse('content:contents-list')
        content_data = {
            'title': 'Python 기초 - 변수와 자료형',
            'content': """
# Python 변수와 자료형

## 변수 선언
```python
name = "김철수"
age = 25
height = 175.5
is_student = True
```

## 기본 자료형
- **문자열 (str)**: 텍스트 데이터
- **정수 (int)**: 정수 데이터
- **실수 (float)**: 소수점 데이터
- **불린 (bool)**: True/False
            """,
            'category': category_id,
            'priority': 'high'
        }
        response = self.client.post(content_url, content_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content_id = response.data['id']
        print(f"   ✅ 콘텐츠 생성 완료 (ID: {content_id})")
        
        # Step 5: 복습 스케줄 자동 생성 확인
        print("5. 복습 스케줄 자동 생성 확인")
        time.sleep(1)  # 시그널 처리 대기
        
        schedule = ReviewSchedule.objects.filter(
            content_id=content_id,
            user_id=user_id
        ).first()
        self.assertIsNotNone(schedule)
        self.assertFalse(schedule.initial_review_completed)
        self.assertEqual(schedule.interval_index, 0)
        print(f"   ✅ 복습 스케줄 자동 생성 확인 (다음 복습: {schedule.next_review_date})")
        
        # Step 6: 즉시 복습 가능한 콘텐츠 조회
        print("6. 오늘의 복습 목록 조회")
        today_reviews_url = reverse('review:today-reviews')
        response = self.client.get(today_reviews_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content']['id'], content_id)
        print(f"   ✅ 오늘의 복습 목록에서 콘텐츠 확인")
        
        # Step 7: 첫 번째 복습 완료 (기억함)
        print("7. 첫 번째 복습 완료")
        complete_review_url = reverse('review:complete-review')
        review_data = {
            'content_id': content_id,
            'result': 'remembered',
            'time_spent': 120,  # 2분
            'notes': '기본 자료형 개념을 잘 이해했습니다.'
        }
        response = self.client.post(complete_review_url, review_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f"   ✅ 첫 번째 복습 완료 (결과: 기억함)")
        
        # Step 8: 복습 기록 확인
        print("8. 복습 기록 확인")
        history = ReviewHistory.objects.filter(
            content_id=content_id,
            user_id=user_id
        ).first()
        self.assertIsNotNone(history)
        self.assertEqual(history.result, 'remembered')
        self.assertEqual(history.time_spent, 120)
        print(f"   ✅ 복습 기록 저장 확인")
        
        # Step 9: 복습 스케줄 업데이트 확인
        print("9. 복습 스케줄 업데이트 확인")
        schedule.refresh_from_db()
        self.assertTrue(schedule.initial_review_completed)
        self.assertEqual(schedule.interval_index, 1)  # 다음 간격으로 이동
        
        # 다음 복습일이 1일 후인지 확인
        expected_next_review = timezone.now() + timedelta(days=1)
        time_diff = abs((schedule.next_review_date - expected_next_review).total_seconds())
        self.assertLess(time_diff, 60)  # 1분 이내 오차 허용
        print(f"   ✅ 스케줄 업데이트 확인 (다음 복습: {schedule.next_review_date})")
        
        # Step 10: 대시보드 데이터 확인
        print("10. 대시보드 데이터 확인")
        dashboard_url = reverse('analytics:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        dashboard_data = response.data
        self.assertEqual(dashboard_data['total_content'], 1)
        self.assertEqual(dashboard_data['total_reviews_30_days'], 1)
        self.assertEqual(dashboard_data['success_rate'], 100.0)  # 1/1 = 100%
        print(f"   ✅ 대시보드 데이터 확인 (성공률: {dashboard_data['success_rate']}%)")
        
        print("\n✅ 완전한 사용자 여정 테스트 성공!")
        return {
            'user_id': user_id,
            'content_id': content_id,
            'category_id': category_id,
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    
    def test_multiple_content_review_workflow(self):
        """여러 콘텐츠 복습 워크플로우 테스트"""
        print("\n📚 여러 콘텐츠 복습 워크플로우 테스트")
        
        # 초기 설정
        result = self.test_complete_user_journey()
        user_id = result['user_id']
        category_id = result['category_id']
        
        # 추가 콘텐츠 생성
        content_list = []
        content_titles = [
            'Python 리스트와 튜플',
            'Python 딕셔너리',
            'Python 함수 정의',
            'Python 클래스와 객체'
        ]
        
        print("1. 추가 콘텐츠 생성")
        content_url = reverse('content:contents-list')
        for title in content_titles:
            content_data = {
                'title': title,
                'content': f'# {title}\n\n이것은 {title}에 대한 학습 내용입니다.',
                'category': category_id,
                'priority': 'medium'
            }
            response = self.client.post(content_url, content_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            content_list.append(response.data['id'])
            print(f"   ✅ '{title}' 생성 완료")
        
        # 모든 콘텐츠에 대한 복습 스케줄 확인
        print("2. 복습 스케줄 생성 확인")
        time.sleep(2)  # 시그널 처리 대기
        
        total_schedules = ReviewSchedule.objects.filter(user_id=user_id).count()
        self.assertEqual(total_schedules, 5)  # 기존 1개 + 새로운 4개
        print(f"   ✅ 총 {total_schedules}개 복습 스케줄 생성 확인")
        
        # 오늘의 복습 목록 확인
        print("3. 오늘의 복습 목록 확인")
        today_reviews_url = reverse('review:today-reviews')
        response = self.client.get(today_reviews_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # 새로 생성된 4개 (기존 1개는 이미 복습 완료)
        print(f"   ✅ 오늘 복습할 콘텐츠 {len(response.data)}개 확인")
        
        # 배치 복습 완료
        print("4. 배치 복습 완료")
        complete_review_url = reverse('review:complete-review')
        results = ['remembered', 'partial', 'forgot', 'remembered']
        
        for i, content_id in enumerate(content_list):
            review_data = {
                'content_id': content_id,
                'result': results[i],
                'time_spent': 90 + i * 10,
                'notes': f'{content_titles[i]} 복습 완료'
            }
            response = self.client.post(complete_review_url, review_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            print(f"   ✅ '{content_titles[i]}' 복습 완료 (결과: {results[i]})")
        
        # 복습 통계 확인
        print("5. 복습 통계 확인")
        dashboard_url = reverse('analytics:dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        dashboard_data = response.data
        self.assertEqual(dashboard_data['total_content'], 5)
        self.assertEqual(dashboard_data['total_reviews_30_days'], 5)
        expected_success_rate = (3 / 5) * 100  # remembered: 3개, partial: 1개, forgot: 1개
        self.assertEqual(dashboard_data['success_rate'], expected_success_rate)
        print(f"   ✅ 통계 확인 - 총 콘텐츠: {dashboard_data['total_content']}, 성공률: {dashboard_data['success_rate']}%")
        
        print("\n✅ 여러 콘텐츠 복습 워크플로우 테스트 성공!")
    
    def test_jwt_token_lifecycle(self):
        """JWT 토큰 전체 라이프사이클 테스트"""
        print("\n🔐 JWT 토큰 라이프사이클 테스트")
        
        # 사용자 생성
        user = User.objects.create_user(
            email='tokentest@example.com',
            password='TokenTest123!'
        )
        
        # 1. 토큰 발급
        print("1. 토큰 발급")
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': 'tokentest@example.com',
            'password': 'TokenTest123!'
        }
        response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        print(f"   ✅ 토큰 발급 완료")
        
        # 2. 액세스 토큰으로 API 호출
        print("2. 액세스 토큰으로 API 호출")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'tokentest@example.com')
        print(f"   ✅ 액세스 토큰으로 프로필 조회 성공")
        
        # 3. 토큰 검증
        print("3. 토큰 검증")
        verify_url = reverse('token_verify')
        verify_data = {'token': access_token}
        response = self.client.post(verify_url, verify_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"   ✅ 토큰 검증 성공")
        
        # 4. 리프레시 토큰으로 새 액세스 토큰 발급
        print("4. 리프레시 토큰으로 새 액세스 토큰 발급")
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        new_access_token = response.data['access']
        self.assertNotEqual(access_token, new_access_token)
        print(f"   ✅ 새 액세스 토큰 발급 성공")
        
        # 5. 새 토큰으로 API 호출
        print("5. 새 토큰으로 API 호출")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"   ✅ 새 토큰으로 API 호출 성공")
        
        # 6. 잘못된 토큰으로 API 호출
        print("6. 잘못된 토큰으로 API 호출")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer invalid_token')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print(f"   ✅ 잘못된 토큰 거부 확인")
        
        print("\n✅ JWT 토큰 라이프사이클 테스트 성공!")
    
    def test_spaced_repetition_algorithm(self):
        """에빙하우스 망각곡선 기반 복습 알고리즘 테스트"""
        print("\n🧠 복습 알고리즘 정확성 테스트")
        
        # 사용자 및 콘텐츠 생성
        user = User.objects.create_user(
            email='algorithm@example.com',
            password='Algorithm123!'
        )
        category = Category.objects.create(
            name='테스트 카테고리',
            user=user
        )
        content = Content.objects.create(
            title='알고리즘 테스트 콘텐츠',
            content='이것은 테스트 콘텐츠입니다.',
            author=user,
            category=category
        )
        
        # 복습 스케줄 생성
        schedule = ReviewSchedule.objects.create(
            content=content,
            user=user,
            next_review_date=timezone.now()
        )
        
        expected_intervals = [1, 3, 7, 14, 30]  # 일 단위
        
        print("1. 복습 간격 진행 테스트")
        for i, expected_interval in enumerate(expected_intervals):
            print(f"   단계 {i+1}: 예상 간격 {expected_interval}일")
            
            # 복습 완료 (성공)
            ReviewHistory.objects.create(
                content=content,
                user=user,
                result='remembered',
                time_spent=60
            )
            
            # 스케줄 진행
            schedule.advance_schedule()
            
            if i < len(expected_intervals) - 1:
                # 다음 간격 확인
                next_interval = schedule.get_next_interval()
                self.assertEqual(next_interval, expected_intervals[i + 1])
                print(f"   ✅ 다음 간격: {next_interval}일")
            else:
                # 마지막 간격에서는 더 이상 증가하지 않음
                next_interval = schedule.get_next_interval()
                self.assertEqual(next_interval, expected_intervals[-1])
                print(f"   ✅ 최대 간격 유지: {next_interval}일")
        
        print("2. 복습 실패 시 리셋 테스트")
        # 복습 실패
        ReviewHistory.objects.create(
            content=content,
            user=user,
            result='forgot',
            time_spent=90
        )
        
        # 스케줄 리셋
        schedule.reset_schedule()
        self.assertEqual(schedule.interval_index, 0)
        next_interval = schedule.get_next_interval()
        self.assertEqual(next_interval, expected_intervals[0])
        print(f"   ✅ 스케줄 리셋 확인 (다음 간격: {next_interval}일)")
        
        print("\n✅ 복습 알고리즘 정확성 테스트 성공!")


class CeleryTaskTestCase(TransactionTestCase):
    """Celery 백그라운드 작업 테스트"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='celerytest@example.com',
            password='CeleryTest123!'
        )
        self.category = Category.objects.create(
            name='셀러리 테스트',
            user=self.user
        )
    
    @patch('review.tasks.send_daily_review_notifications.delay')
    def test_daily_notification_task(self, mock_task):
        """일일 복습 알림 작업 테스트"""
        print("\n📧 일일 복습 알림 작업 테스트")
        
        # 복습할 콘텐츠 생성
        content = Content.objects.create(
            title='알림 테스트 콘텐츠',
            content='이것은 알림 테스트입니다.',
            author=self.user,
            category=self.category
        )
        
        # 복습 스케줄 생성 (어제 복습 예정)
        yesterday = timezone.now() - timedelta(days=1)
        ReviewSchedule.objects.create(
            content=content,
            user=self.user,
            next_review_date=yesterday
        )
        
        # 알림 작업 실행
        result = send_daily_review_notifications()
        
        print(f"   ✅ 알림 작업 실행 완료: {result}")
        
    def test_review_schedule_creation_signal(self):
        """콘텐츠 생성 시 복습 스케줄 자동 생성 시그널 테스트"""
        print("\n⚡ 복습 스케줄 자동 생성 시그널 테스트")
        
        # 콘텐츠 생성 전 스케줄 수 확인
        initial_count = ReviewSchedule.objects.count()
        
        # 콘텐츠 생성
        content = Content.objects.create(
            title='시그널 테스트 콘텐츠',
            content='이것은 시그널 테스트입니다.',
            author=self.user,
            category=self.category
        )
        
        # 스케줄 자동 생성 확인
        final_count = ReviewSchedule.objects.count()
        self.assertEqual(final_count, initial_count + 1)
        
        # 생성된 스케줄 확인
        schedule = ReviewSchedule.objects.filter(
            content=content,
            user=self.user
        ).first()
        
        self.assertIsNotNone(schedule)
        self.assertFalse(schedule.initial_review_completed)
        self.assertEqual(schedule.interval_index, 0)
        
        print(f"   ✅ 복습 스케줄 자동 생성 확인")
        print(f"   ✅ 초기 설정 올바름 (initial_review_completed: {schedule.initial_review_completed})")


class PerformanceTestCase(APITestCase):
    """성능 테스트"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='performance@example.com',
            password='Performance123!'
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = Category.objects.create(
            name='성능 테스트',
            user=self.user
        )
    
    def test_large_content_creation(self):
        """대용량 콘텐츠 생성 성능 테스트"""
        print("\n⚡ 대용량 콘텐츠 생성 성능 테스트")
        
        content_count = 100
        start_time = time.time()
        
        content_url = reverse('content:contents-list')
        
        for i in range(content_count):
            content_data = {
                'title': f'성능 테스트 콘텐츠 {i+1}',
                'content': f'이것은 {i+1}번째 성능 테스트 콘텐츠입니다.' * 10,
                'category': self.category.id,
                'priority': 'medium'
            }
            response = self.client.post(content_url, content_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / content_count
        
        print(f"   ✅ {content_count}개 콘텐츠 생성 완료")
        print(f"   ✅ 총 소요 시간: {total_time:.2f}초")
        print(f"   ✅ 평균 생성 시간: {avg_time:.3f}초/개")
        
        # 성능 기준: 평균 0.5초 미만이어야 함
        self.assertLess(avg_time, 0.5, f"성능 기준 미달: {avg_time:.3f}초 > 0.5초")
        
        # 생성된 스케줄 확인
        schedule_count = ReviewSchedule.objects.filter(user=self.user).count()
        self.assertEqual(schedule_count, content_count)
        print(f"   ✅ {schedule_count}개 복습 스케줄 자동 생성 확인")
    
    def test_large_scale_review_completion(self):
        """대규모 복습 완료 성능 테스트"""
        print("\n⚡ 대규모 복습 완료 성능 테스트")
        
        # 100개 콘텐츠와 스케줄 미리 생성
        contents = []
        for i in range(100):
            content = Content.objects.create(
                title=f'복습 테스트 콘텐츠 {i+1}',
                content=f'복습 내용 {i+1}',
                author=self.user,
                category=self.category
            )
            contents.append(content)
        
        time.sleep(1)  # 시그널 처리 대기
        
        # 배치 복습 완료
        start_time = time.time()
        complete_review_url = reverse('review:complete-review')
        
        for i, content in enumerate(contents):
            review_data = {
                'content_id': content.id,
                'result': 'remembered' if i % 3 == 0 else 'partial',
                'time_spent': 60 + (i % 30),
                'notes': f'복습 {i+1} 완료'
            }
            response = self.client.post(complete_review_url, review_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(contents)
        
        print(f"   ✅ {len(contents)}개 복습 완료")
        print(f"   ✅ 총 소요 시간: {total_time:.2f}초")
        print(f"   ✅ 평균 복습 시간: {avg_time:.3f}초/개")
        
        # 성능 기준: 평균 0.3초 미만이어야 함
        self.assertLess(avg_time, 0.3, f"성능 기준 미달: {avg_time:.3f}초 > 0.3초")
        
        # 복습 기록 확인
        history_count = ReviewHistory.objects.filter(user=self.user).count()
        self.assertEqual(history_count, len(contents))
        print(f"   ✅ {history_count}개 복습 기록 저장 확인")