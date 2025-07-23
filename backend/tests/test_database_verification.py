"""
실제 데이터베이스 저장/조회 검증 테스트
PostgreSQL에 데이터가 올바르게 저장되고 조회되는지 확인
"""

import time
import json
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone
from django.core.management import execute_from_command_line

from accounts.models import User
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory
from analytics.views import DashboardView

User = get_user_model()


class DatabaseVerificationTestCase(TransactionTestCase):
    """데이터베이스 저장/조회 검증 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_user = User.objects.create_user(
            email='dbtest@example.com',
            password='DbTest123!',
            first_name='Database',
            last_name='Tester'
        )
        
        self.test_category = Category.objects.create(
            name='DB 테스트 카테고리',
            description='데이터베이스 검증용 카테고리',
            user=self.test_user
        )
    
    def test_user_data_persistence(self):
        """사용자 데이터 저장 및 조회 검증"""
        print("\n👤 사용자 데이터 저장/조회 검증")
        
        # 사용자 데이터 생성 및 저장
        test_users = []
        for i in range(10):
            user = User.objects.create_user(
                email=f'testuser{i}@example.com',
                password='TestPass123!',
                first_name=f'Test{i}',
                last_name='User',
                timezone='Asia/Seoul',
                notification_enabled=(i % 2 == 0)
            )
            test_users.append(user)
        
        # 트랜잭션 커밋 강제
        transaction.commit()
        
        # 데이터베이스에서 직접 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT email, first_name, last_name, timezone, notification_enabled 
                FROM accounts_user 
                WHERE email LIKE 'testuser%@example.com'
                ORDER BY email
            """)
            db_users = cursor.fetchall()
        
        # 검증
        self.assertEqual(len(db_users), 10)
        
        for i, (email, first_name, last_name, timezone_str, notification_enabled) in enumerate(db_users):
            expected_email = f'testuser{i}@example.com'
            expected_first_name = f'Test{i}'
            
            self.assertEqual(email, expected_email)
            self.assertEqual(first_name, expected_first_name)
            self.assertEqual(last_name, 'User')
            self.assertEqual(timezone_str, 'Asia/Seoul')
            self.assertEqual(notification_enabled, (i % 2 == 0))
        
        print(f"   {len(db_users)} user data storage/retrieval verification completed")
    
    def test_content_data_persistence(self):
        """콘텐츠 데이터 저장 및 조회 검증"""
        print("\nContent data storage/retrieval verification")
        
        # 다양한 우선순위의 콘텐츠 생성
        priorities = ['low', 'medium', 'high']
        test_contents = []
        
        for i in range(15):
            priority = priorities[i % 3]
            content = Content.objects.create(
                title=f'테스트 콘텐츠 {i+1}',
                content=f"""
# 테스트 콘텐츠 {i+1}

## 개요
이것은 데이터베이스 검증을 위한 테스트 콘텐츠입니다.

## 내용
- 우선순위: {priority}
- 생성 순서: {i+1}
- 테스트 목적: 데이터 저장 검증

## 코드 예시
```python
def test_function_{i+1}():
    return "테스트 함수 {i+1}"
```

## 결론
데이터베이스 저장 테스트용 콘텐츠입니다.
                """,
                author=self.test_user,
                category=self.test_category,
                priority=priority
            )
            test_contents.append(content)
        
        # 트랜잭션 커밋 강제
        transaction.commit()
        
        # 데이터베이스에서 직접 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.title, c.content, c.priority, c.created_at, 
                       u.email, cat.name as category_name
                FROM content_content c
                JOIN accounts_user u ON c.author_id = u.id
                JOIN content_category cat ON c.category_id = cat.id
                WHERE u.email = %s
                ORDER BY c.created_at
            """, [self.test_user.email])
            
            db_contents = cursor.fetchall()
        
        # 검증
        self.assertEqual(len(db_contents), 15)
        
        priority_counts = {'low': 0, 'medium': 0, 'high': 0}
        for content_id, title, content_text, priority, created_at, author_email, category_name in db_contents:
            # 기본 필드 검증
            self.assertIsNotNone(content_id)
            self.assertTrue(title.startswith('테스트 콘텐츠'))
            self.assertIn('데이터베이스 검증을 위한', content_text)
            self.assertIn(priority, priorities)
            self.assertEqual(author_email, self.test_user.email)
            self.assertEqual(category_name, self.test_category.name)
            
            # 우선순위 카운트
            priority_counts[priority] += 1
        
        # 우선순위별 개수 검증 (각각 5개씩)
        for priority, count in priority_counts.items():
            self.assertEqual(count, 5, f"Priority {priority} should have 5 contents, got {count}")
        
        print(f"   {len(db_contents)} content data storage/retrieval verification completed")
        print(f"   Priority distribution: {priority_counts}")
    
    def test_review_schedule_data_persistence(self):
        """복습 스케줄 데이터 저장 및 조회 검증"""
        print("\nReview schedule data storage/retrieval verification")
        
        # 테스트용 콘텐츠 생성
        test_contents = []
        for i in range(5):
            content = Content.objects.create(
                title=f'복습 테스트 콘텐츠 {i+1}',
                content=f'복습 스케줄 테스트용 콘텐츠 {i+1}',
                author=self.test_user,
                category=self.test_category
            )
            test_contents.append(content)
        
        # 다양한 상태의 복습 스케줄 생성
        schedules_data = [
            {'interval_index': 0, 'initial_completed': False, 'days_offset': 0},    # 즉시 복습
            {'interval_index': 1, 'initial_completed': True, 'days_offset': 1},     # 1일 후
            {'interval_index': 2, 'initial_completed': True, 'days_offset': 3},     # 3일 후
            {'interval_index': 3, 'initial_completed': True, 'days_offset': 7},     # 7일 후
            {'interval_index': 4, 'initial_completed': True, 'days_offset': 14},    # 14일 후
        ]
        
        test_schedules = []
        for i, (content, schedule_data) in enumerate(zip(test_contents, schedules_data)):
            next_review_date = timezone.now() + timedelta(days=schedule_data['days_offset'])
            
            schedule = ReviewSchedule.objects.create(
                content=content,
                user=self.test_user,
                next_review_date=next_review_date,
                interval_index=schedule_data['interval_index'],
                initial_review_completed=schedule_data['initial_completed']
            )
            test_schedules.append(schedule)
        
        # 트랜잭션 커밋 강제
        transaction.commit()
        
        # 데이터베이스에서 직접 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT rs.id, rs.interval_index, rs.initial_review_completed, 
                       rs.next_review_date, rs.is_active,
                       c.title, u.email
                FROM review_reviewschedule rs
                JOIN content_content c ON rs.content_id = c.id
                JOIN accounts_user u ON rs.user_id = u.id
                WHERE u.email = %s
                ORDER BY rs.interval_index
            """, [self.test_user.email])
            
            db_schedules = cursor.fetchall()
        
        # 검증
        self.assertEqual(len(db_schedules), 5)
        
        for i, (schedule_id, interval_index, initial_completed, next_review_date, is_active, content_title, user_email) in enumerate(db_schedules):
            expected_data = schedules_data[i]
            
            # 기본 필드 검증
            self.assertIsNotNone(schedule_id)
            self.assertEqual(interval_index, expected_data['interval_index'])
            self.assertEqual(initial_completed, expected_data['initial_completed'])
            self.assertTrue(is_active)
            self.assertEqual(user_email, self.test_user.email)
            self.assertTrue(content_title.startswith('복습 테스트 콘텐츠'))
            
            # 날짜 검증 (1시간 오차 허용)
            expected_date = timezone.now() + timedelta(days=expected_data['days_offset'])
            time_diff = abs((next_review_date - expected_date).total_seconds())
            self.assertLess(time_diff, 3600, f"Schedule {i} date mismatch")
        
        print(f"   {len(db_schedules)} review schedule data storage/retrieval verification completed")
    
    def test_review_history_data_persistence(self):
        """복습 기록 데이터 저장 및 조회 검증"""
        print("\nReview history data storage/retrieval verification")
        
        # 테스트용 콘텐츠 생성
        content = Content.objects.create(
            title='복습 기록 테스트 콘텐츠',
            content='복습 기록 저장 테스트용 콘텐츠',
            author=self.test_user,
            category=self.test_category
        )
        
        # 다양한 결과의 복습 기록 생성
        review_results = ['remembered', 'partial', 'forgot']
        test_histories = []
        
        for i in range(30):  # 30개의 복습 기록
            result = review_results[i % 3]
            time_spent = 60 + (i * 10)  # 60초부터 시작해서 10초씩 증가
            
            history = ReviewHistory.objects.create(
                content=content,
                user=self.test_user,
                result=result,
                time_spent=time_spent,
                notes=f'복습 기록 {i+1}: {result} 결과'
            )
            test_histories.append(history)
            
            # 각 기록 사이에 약간의 시간 차이 두기
            time.sleep(0.01)
        
        # 트랜잭션 커밋 강제
        transaction.commit()
        
        # 데이터베이스에서 직접 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT rh.id, rh.result, rh.time_spent, rh.notes, rh.review_date,
                       c.title, u.email
                FROM review_reviewhistory rh
                JOIN content_content c ON rh.content_id = c.id
                JOIN accounts_user u ON rh.user_id = u.id
                WHERE u.email = %s
                ORDER BY rh.review_date
            """, [self.test_user.email])
            
            db_histories = cursor.fetchall()
        
        # 검증
        self.assertEqual(len(db_histories), 30)
        
        result_counts = {'remembered': 0, 'partial': 0, 'forgot': 0}
        total_time_spent = 0
        
        for i, (history_id, result, time_spent, notes, review_date, content_title, user_email) in enumerate(db_histories):
            # 기본 필드 검증
            self.assertIsNotNone(history_id)
            self.assertIn(result, review_results)
            self.assertIsNotNone(time_spent)
            self.assertTrue(notes.startswith(f'복습 기록 {i+1}'))
            self.assertIsNotNone(review_date)
            self.assertEqual(content_title, content.title)
            self.assertEqual(user_email, self.test_user.email)
            
            # 시간 검증
            expected_time = 60 + (i * 10)
            self.assertEqual(time_spent, expected_time)
            
            # 통계 수집
            result_counts[result] += 1
            total_time_spent += time_spent
        
        # 결과별 개수 검증 (각각 10개씩)
        for result, count in result_counts.items():
            self.assertEqual(count, 10, f"Result {result} should have 10 records, got {count}")
        
        average_time = total_time_spent / 30
        
        print(f"   {len(db_histories)} review history data storage/retrieval verification completed")
        print(f"   Result distribution: {result_counts}")
        print(f"   Average review time: {average_time:.1f}sec")
    
    def test_database_constraints_and_indexes(self):
        """데이터베이스 제약조건 및 인덱스 검증"""
        print("\nDatabase constraints and indexes verification")
        
        with connection.cursor() as cursor:
            # 1. 유니크 제약조건 검증
            cursor.execute("""
                SELECT constraint_name, table_name, column_name
                FROM information_schema.constraint_column_usage
                WHERE constraint_schema = 'public'
                AND constraint_name LIKE '%_unique%'
                OR constraint_name LIKE '%_uniq%'
                OR constraint_name LIKE '%_key'
            """)
            unique_constraints = cursor.fetchall()
            
            # 2. 외래키 제약조건 검증
            cursor.execute("""
                SELECT tc.constraint_name, tc.table_name, kcu.column_name,
                       ccu.table_name AS foreign_table_name,
                       ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """)
            foreign_keys = cursor.fetchall()
            
            # 3. 인덱스 확인
            cursor.execute("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND indexname NOT LIKE '%_pkey'
                ORDER BY tablename, indexname
            """)
            indexes = cursor.fetchall()
        
        # 검증
        self.assertGreater(len(unique_constraints), 0, "유니크 제약조건이 존재해야 함")
        self.assertGreater(len(foreign_keys), 0, "외래키 제약조건이 존재해야 함")
        self.assertGreater(len(indexes), 0, "인덱스가 존재해야 함")
        
        # 중요한 외래키 관계 확인
        important_fk_relations = [
            ('content_content', 'author_id', 'accounts_user'),
            ('content_content', 'category_id', 'content_category'),
            ('review_reviewschedule', 'content_id', 'content_content'),
            ('review_reviewschedule', 'user_id', 'accounts_user'),
            ('review_reviewhistory', 'content_id', 'content_content'),
            ('review_reviewhistory', 'user_id', 'accounts_user'),
        ]
        
        found_relations = set()
        for _, table_name, column_name, foreign_table, foreign_column in foreign_keys:
            found_relations.add((table_name, column_name, foreign_table))
        
        for table, column, foreign_table in important_fk_relations:
            self.assertIn((table, column, foreign_table), found_relations,
                         f"중요한 외래키 관계가 누락됨: {table}.{column} -> {foreign_table}")
        
        print(f"   Unique constraints: {len(unique_constraints)} items")
        print(f"   Foreign key constraints: {len(foreign_keys)} items")
        print(f"   Indexes: {len(indexes)} items")
        print(f"   Important foreign key relationships: {len(important_fk_relations)} items confirmed")
    
    def test_data_integrity_across_operations(self):
        """연속 작업에서의 데이터 무결성 검증"""
        print("\nData integrity verification (continuous operations)")
        
        # 1. 사용자-콘텐츠-복습 데이터 연쇄 생성
        user = User.objects.create_user(
            email='integrity@example.com',
            password='IntegrityTest123!'
        )
        
        category = Category.objects.create(
            name='무결성 테스트',
            user=user
        )
        
        content = Content.objects.create(
            title='무결성 테스트 콘텐츠',
            content='데이터 무결성 검증용',
            author=user,
            category=category
        )
        
        # 복습 스케줄 자동 생성 확인 (시그널)
        time.sleep(0.1)  # 시그널 처리 대기
        
        schedule = ReviewSchedule.objects.filter(content=content, user=user).first()
        self.assertIsNotNone(schedule, "복습 스케줄이 자동 생성되어야 함")
        
        # 2. 복습 완료 후 데이터 변경 확인
        initial_interval = schedule.interval_index
        
        # 복습 기록 생성
        history = ReviewHistory.objects.create(
            content=content,
            user=user,
            result='remembered',
            time_spent=120
        )
        
        # 스케줄 수동 업데이트 (실제 API에서는 자동으로 처리)
        schedule.initial_review_completed = True
        schedule.interval_index += 1
        schedule.next_review_date = timezone.now() + timedelta(days=1)
        schedule.save()
        
        # 3. 데이터베이스에서 무결성 확인
        with connection.cursor() as cursor:
            # 모든 관련 데이터가 일관성 있게 저장되었는지 확인
            cursor.execute("""
                SELECT u.email, c.title, rs.interval_index, rs.initial_review_completed,
                       rh.result, rh.time_spent, cat.name
                FROM accounts_user u
                JOIN content_content c ON c.author_id = u.id
                JOIN content_category cat ON c.category_id = cat.id
                LEFT JOIN review_reviewschedule rs ON rs.content_id = c.id AND rs.user_id = u.id
                LEFT JOIN review_reviewhistory rh ON rh.content_id = c.id AND rh.user_id = u.id
                WHERE u.email = %s
            """, [user.email])
            
            result = cursor.fetchone()
        
        # 무결성 검증
        self.assertIsNotNone(result)
        email, title, interval_index, initial_completed, review_result, time_spent, category_name = result
        
        self.assertEqual(email, user.email)
        self.assertEqual(title, content.title)
        self.assertEqual(interval_index, initial_interval + 1)
        self.assertTrue(initial_completed)
        self.assertEqual(review_result, 'remembered')
        self.assertEqual(time_spent, 120)
        self.assertEqual(category_name, category.name)
        
        # 4. 카스케이드 삭제 테스트
        initial_content_count = Content.objects.count()
        initial_schedule_count = ReviewSchedule.objects.count()
        initial_history_count = ReviewHistory.objects.count()
        
        # 사용자 삭제 (카스케이드로 모든 관련 데이터가 삭제되어야 함)
        user.delete()
        
        final_content_count = Content.objects.count()
        final_schedule_count = ReviewSchedule.objects.count()
        final_history_count = ReviewHistory.objects.count()
        
        # 관련 데이터가 모두 삭제되었는지 확인
        self.assertEqual(final_content_count, initial_content_count - 1)
        self.assertEqual(final_schedule_count, initial_schedule_count - 1)
        self.assertEqual(final_history_count, initial_history_count - 1)
        
        print("   Data chain creation and relationship verification completed")
        print("   Review completion status change verification completed")
        print("   Cascade delete operation verification completed")
    
    def test_database_performance_under_load(self):
        """부하 상황에서의 데이터베이스 성능 검증"""
        print("\nDatabase performance verification (load test)")
        
        start_time = time.time()
        
        # 대량 데이터 생성
        users = []
        for i in range(50):
            user = User.objects.create_user(
                email=f'loadtest{i}@example.com',
                password='LoadTest123!'
            )
            users.append(user)
        
        categories = []
        for user in users[:10]:  # 10개 카테고리만 생성
            category = Category.objects.create(
                name=f'{user.email}의 카테고리',
                user=user
            )
            categories.append(category)
        
        # 대량 콘텐츠 생성 (500개)
        contents = []
        for i in range(500):
            user = users[i % 50]
            category = categories[i % 10]
            
            content = Content.objects.create(
                title=f'부하 테스트 콘텐츠 {i+1}',
                content=f'부하 테스트용 콘텐츠 {i+1}',
                author=user,
                category=category,
                priority=['low', 'medium', 'high'][i % 3]
            )
            contents.append(content)
        
        creation_time = time.time() - start_time
        
        # 복잡한 조회 쿼리 성능 테스트
        query_start = time.time()
        
        with connection.cursor() as cursor:
            # 1. 복잡한 집계 쿼리
            cursor.execute("""
                SELECT 
                    u.email,
                    COUNT(c.id) as content_count,
                    COUNT(DISTINCT cat.id) as category_count,
                    AVG(CASE WHEN c.priority = 'high' THEN 3
                             WHEN c.priority = 'medium' THEN 2
                             ELSE 1 END) as avg_priority_score
                FROM accounts_user u
                LEFT JOIN content_content c ON c.author_id = u.id
                LEFT JOIN content_category cat ON c.category_id = cat.id
                WHERE u.email LIKE 'loadtest%@example.com'
                GROUP BY u.email
                HAVING COUNT(c.id) > 5
                ORDER BY content_count DESC
                LIMIT 10
            """)
            
            aggregation_results = cursor.fetchall()
            
            # 2. 조인이 많은 쿼리
            cursor.execute("""
                SELECT c.title, u.email, cat.name, c.priority, c.created_at
                FROM content_content c
                JOIN accounts_user u ON c.author_id = u.id
                JOIN content_category cat ON c.category_id = cat.id
                WHERE u.email LIKE 'loadtest%@example.com'
                AND c.priority IN ('high', 'medium')
                ORDER BY c.created_at DESC
                LIMIT 50
            """)
            
            join_results = cursor.fetchall()
        
        query_time = time.time() - query_start
        total_time = time.time() - start_time
        
        # 성능 기준 검증
        self.assertLess(creation_time, 30.0, f"대량 데이터 생성이 너무 오래 걸림: {creation_time:.2f}초")
        self.assertLess(query_time, 5.0, f"복잡한 쿼리가 너무 오래 걸림: {query_time:.2f}초")
        
        # 결과 검증
        self.assertGreater(len(aggregation_results), 0, "집계 쿼리 결과가 있어야 함")
        self.assertEqual(len(join_results), 50, "조인 쿼리 결과가 50개여야 함")
        
        print(f"   Large data creation: {creation_time:.2f}sec (500 contents)")
        print(f"   Complex query execution: {query_time:.2f}sec")
        print(f"   Total processing time: {total_time:.2f}sec")
        print(f"   Aggregation query results: {len(aggregation_results)} items")
        print(f"   Join query results: {len(join_results)} items")


class DatabaseAnalyticsVerificationTestCase(TransactionTestCase):
    """분석 데이터 검증 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        self.test_user = User.objects.create_user(
            email='analytics@example.com',
            password='Analytics123!'
        )
        
        self.category = Category.objects.create(
            name='분석 테스트',
            user=self.test_user
        )
    
    def test_analytics_data_accuracy(self):
        """분석 데이터 정확성 검증"""
        print("\nAnalytics data accuracy verification")
        
        # 테스트 데이터 생성
        contents = []
        for i in range(10):
            content = Content.objects.create(
                title=f'분석 테스트 콘텐츠 {i+1}',
                content=f'분석용 콘텐츠 {i+1}',
                author=self.test_user,
                category=self.category
            )
            contents.append(content)
        
        # 복습 기록 생성 (다양한 결과)
        review_data = [
            ('remembered', 8),  # 8개 성공
            ('partial', 1),     # 1개 부분 성공
            ('forgot', 1),      # 1개 실패
        ]
        
        total_reviews = 0
        successful_reviews = 0
        
        for result, count in review_data:
            for i in range(count):
                content = contents[total_reviews % len(contents)]
                ReviewHistory.objects.create(
                    content=content,
                    user=self.test_user,
                    result=result,
                    time_spent=60 + (i * 10)
                )
                total_reviews += 1
                if result == 'remembered':
                    successful_reviews += 1
        
        # 트랜잭션 커밋
        transaction.commit()
        
        # 데이터베이스에서 직접 분석 데이터 계산
        with connection.cursor() as cursor:
            # 1. 총 콘텐츠 수
            cursor.execute("""
                SELECT COUNT(*) FROM content_content WHERE author_id = %s
            """, [self.test_user.id])
            db_total_content = cursor.fetchone()[0]
            
            # 2. 총 복습 수
            cursor.execute("""
                SELECT COUNT(*) FROM review_reviewhistory WHERE user_id = %s
            """, [self.test_user.id])
            db_total_reviews = cursor.fetchone()[0]
            
            # 3. 성공률 계산
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN result = 'remembered' THEN 1 END) as successful,
                    ROUND(
                        COUNT(CASE WHEN result = 'remembered' THEN 1 END) * 100.0 / COUNT(*),
                        1
                    ) as success_rate
                FROM review_reviewhistory 
                WHERE user_id = %s
            """, [self.test_user.id])
            
            db_total, db_successful, db_success_rate = cursor.fetchone()
            
            # 4. 결과별 분포
            cursor.execute("""
                SELECT result, COUNT(*) as count
                FROM review_reviewhistory 
                WHERE user_id = %s
                GROUP BY result
                ORDER BY result
            """, [self.test_user.id])
            
            result_distribution = dict(cursor.fetchall())
        
        # 검증
        self.assertEqual(db_total_content, 10)
        self.assertEqual(db_total_reviews, 10)
        self.assertEqual(db_successful, 8)
        self.assertEqual(float(db_success_rate), 80.0)
        
        # 결과 분포 검증
        expected_distribution = {'forgot': 1, 'partial': 1, 'remembered': 8}
        self.assertEqual(result_distribution, expected_distribution)
        
        print(f"   Total content: {db_total_content} items")
        print(f"   Total reviews: {db_total_reviews} items")
        print(f"   Success rate: {db_success_rate}%")
        print(f"   Result distribution: {result_distribution}")
        print("   All analytics data is accurate")


if __name__ == '__main__':
    print("Database verification test execution")
    print("Docker 환경에서 PostgreSQL이 실행 중인지 확인하세요.")
    
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
    django.setup()
    
    import unittest
    unittest.main()