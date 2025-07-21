"""
성능 및 스트레스 테스트
시스템의 성능 한계를 테스트하고 병목 지점을 식별
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone
from django.urls import reverse
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()


class PerformanceTestCase(TransactionTestCase):
    """성능 테스트 케이스"""
    
    def setUp(self):
        """테스트 설정"""
        self.client = APIClient()
        self.users = []
        self.contents = []
        
        # 테스트용 사용자 생성
        for i in range(10):
            user = User.objects.create_user(
                email=f'perftest{i}@example.com',
                password='PerfTest123!',
                first_name=f'Perf{i}',
                last_name='Tester'
            )
            self.users.append(user)
    
    def get_auth_headers(self, user):
        """인증 헤더 생성"""
        refresh = RefreshToken.for_user(user)
        return {'HTTP_AUTHORIZATION': f'Bearer {refresh.access_token}'}
    
    def test_content_creation_performance(self):
        """콘텐츠 생성 성능 테스트"""
        print("\n📝 콘텐츠 생성 성능 테스트")
        
        user = self.users[0]
        headers = self.get_auth_headers(user)
        
        # 카테고리 생성
        category = Category.objects.create(
            name='성능 테스트 카테고리',
            user=user
        )
        
        content_data = {
            'title': '성능 테스트 콘텐츠',
            'content': '# 성능 테스트\n\n이것은 성능 테스트용 콘텐츠입니다.' * 10,
            'category': category.id,
            'priority': 'medium'
        }
        
        # 100개 콘텐츠 생성 시간 측정
        start_time = time.time()
        
        for i in range(100):
            content_data['title'] = f'성능 테스트 콘텐츠 {i+1}'
            response = self.client.post(
                '/api/content/contents/',
                content_data,
                **headers
            )
            self.assertEqual(response.status_code, 201)
        
        creation_time = time.time() - start_time
        
        print(f"   📊 100개 콘텐츠 생성: {creation_time:.2f}초")
        print(f"   📊 평균 생성 시간: {creation_time/100:.3f}초/개")
        
        # 성능 기준 검증 (2초 이내)
        self.assertLess(creation_time, 2.0, f"콘텐츠 생성이 너무 느림: {creation_time:.2f}초")
    
    def test_content_retrieval_performance(self):
        """콘텐츠 조회 성능 테스트"""
        print("\n🔍 콘텐츠 조회 성능 테스트")
        
        user = self.users[0]
        headers = self.get_auth_headers(user)
        
        # 대량 콘텐츠 생성
        category = Category.objects.create(name='조회 테스트', user=user)
        
        contents = []
        for i in range(200):
            content = Content.objects.create(
                title=f'조회 테스트 콘텐츠 {i+1}',
                content=f'조회 테스트용 콘텐츠 {i+1}',
                author=user,
                category=category,
                priority=['low', 'medium', 'high'][i % 3]
            )
            contents.append(content)
        
        # 목록 조회 성능 테스트
        start_time = time.time()
        
        for _ in range(10):
            response = self.client.get('/api/content/contents/', **headers)
            self.assertEqual(response.status_code, 200)
        
        list_retrieval_time = time.time() - start_time
        
        # 개별 조회 성능 테스트
        start_time = time.time()
        
        for content in contents[:50]:  # 50개만 테스트
            response = self.client.get(f'/api/content/contents/{content.id}/', **headers)
            self.assertEqual(response.status_code, 200)
        
        detail_retrieval_time = time.time() - start_time
        
        print(f"   📊 목록 조회 10회: {list_retrieval_time:.2f}초")
        print(f"   📊 평균 목록 조회: {list_retrieval_time/10:.3f}초/회")
        print(f"   📊 개별 조회 50회: {detail_retrieval_time:.2f}초")
        print(f"   📊 평균 개별 조회: {detail_retrieval_time/50:.3f}초/회")
        
        # 성능 기준 검증
        self.assertLess(list_retrieval_time/10, 0.5, "목록 조회가 너무 느림")
        self.assertLess(detail_retrieval_time/50, 0.1, "개별 조회가 너무 느림")
    
    def test_review_completion_performance(self):
        """복습 완료 성능 테스트"""
        print("\n🧠 복습 완료 성능 테스트")
        
        user = self.users[0]
        headers = self.get_auth_headers(user)
        
        # 테스트용 콘텐츠 및 스케줄 생성
        category = Category.objects.create(name='복습 테스트', user=user)
        
        contents = []
        for i in range(50):
            content = Content.objects.create(
                title=f'복습 테스트 콘텐츠 {i+1}',
                content=f'복습 테스트용 콘텐츠 {i+1}',
                author=user,
                category=category
            )
            contents.append(content)
            
            # 복습 스케줄 생성
            ReviewSchedule.objects.create(
                content=content,
                user=user,
                next_review_date=timezone.now(),
                interval_index=0
            )
        
        # 복습 완료 성능 측정
        start_time = time.time()
        
        for content in contents:
            review_data = {
                'content_id': content.id,
                'result': 'remembered',
                'time_spent': 60,
                'notes': f'성능 테스트 복습 {content.id}'
            }
            
            response = self.client.post(
                '/api/review/complete/',
                review_data,
                **headers
            )
            self.assertEqual(response.status_code, 201)
        
        completion_time = time.time() - start_time
        
        print(f"   📊 50개 복습 완료: {completion_time:.2f}초")
        print(f"   📊 평균 복습 완료: {completion_time/50:.3f}초/개")
        
        # 성능 기준 검증
        self.assertLess(completion_time, 5.0, f"복습 완료가 너무 느림: {completion_time:.2f}초")
    
    def test_database_query_performance(self):
        """데이터베이스 쿼리 성능 테스트"""
        print("\n🗄️ 데이터베이스 쿼리 성능 테스트")
        
        user = self.users[0]
        
        # 대량 데이터 생성
        category = Category.objects.create(name='쿼리 테스트', user=user)
        
        contents = []
        for i in range(500):
            content = Content.objects.create(
                title=f'쿼리 테스트 콘텐츠 {i+1}',
                content=f'쿼리 테스트용 콘텐츠 {i+1}',
                author=user,
                category=category
            )
            contents.append(content)
            
            # 복습 기록 생성
            ReviewHistory.objects.create(
                content=content,
                user=user,
                result=['remembered', 'partial', 'forgot'][i % 3],
                time_spent=60 + (i % 120)
            )
        
        # 복잡한 집계 쿼리 성능 테스트
        start_time = time.time()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.priority,
                    COUNT(*) as content_count,
                    AVG(rh.time_spent) as avg_time_spent,
                    COUNT(CASE WHEN rh.result = 'remembered' THEN 1 END) as remembered_count,
                    ROUND(
                        COUNT(CASE WHEN rh.result = 'remembered' THEN 1 END) * 100.0 / COUNT(*),
                        2
                    ) as success_rate
                FROM content_content c
                LEFT JOIN review_reviewhistory rh ON c.id = rh.content_id
                WHERE c.author_id = %s
                GROUP BY c.priority
                ORDER BY c.priority
            """, [user.id])
            
            results = cursor.fetchall()
        
        aggregation_time = time.time() - start_time
        
        # 조인 쿼리 성능 테스트
        start_time = time.time()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.title, 
                    c.priority, 
                    cat.name as category_name,
                    rs.next_review_date,
                    rs.interval_index,
                    COUNT(rh.id) as review_count
                FROM content_content c
                JOIN content_category cat ON c.category_id = cat.id
                LEFT JOIN review_reviewschedule rs ON c.id = rs.content_id AND rs.user_id = %s
                LEFT JOIN review_reviewhistory rh ON c.id = rh.content_id AND rh.user_id = %s
                WHERE c.author_id = %s
                GROUP BY c.id, c.title, c.priority, cat.name, rs.next_review_date, rs.interval_index
                ORDER BY c.created_at DESC
                LIMIT 100
            """, [user.id, user.id, user.id])
            
            join_results = cursor.fetchall()
        
        join_time = time.time() - start_time
        
        print(f"   📊 집계 쿼리: {aggregation_time:.3f}초")
        print(f"   📊 조인 쿼리: {join_time:.3f}초")
        print(f"   📊 집계 결과: {len(results)}개")
        print(f"   📊 조인 결과: {len(join_results)}개")
        
        # 성능 기준 검증
        self.assertLess(aggregation_time, 1.0, "집계 쿼리가 너무 느림")
        self.assertLess(join_time, 2.0, "조인 쿼리가 너무 느림")


class StressTestCase(TransactionTestCase):
    """스트레스 테스트 케이스"""
    
    def setUp(self):
        """테스트 설정"""
        self.base_url = '/api'
        self.test_results = []
        
        # 테스트용 사용자들 생성
        self.users = []
        for i in range(20):
            user = User.objects.create_user(
                email=f'stresstest{i}@example.com',
                password='StressTest123!',
                first_name=f'Stress{i}',
                last_name='Tester'
            )
            self.users.append(user)
    
    def create_auth_client(self, user):
        """인증된 클라이언트 생성"""
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return client
    
    def simulate_user_activity(self, user_index, duration_seconds=30):
        """사용자 활동 시뮬레이션"""
        user = self.users[user_index]
        client = self.create_auth_client(user)
        
        # 카테고리 생성
        category_data = {
            'name': f'스트레스 테스트 카테고리 {user_index}',
            'description': f'사용자 {user_index}의 카테고리'
        }
        response = client.post(f'{self.base_url}/content/categories/', category_data)
        if response.status_code != 201:
            return {'user': user_index, 'error': f'Category creation failed: {response.status_code}'}
        
        category_id = response.json()['id']
        
        operations = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                # 콘텐츠 생성
                content_data = {
                    'title': f'스트레스 테스트 콘텐츠 {int(time.time())}',
                    'content': f'# 스트레스 테스트\n\n사용자 {user_index}의 테스트 콘텐츠',
                    'category': category_id,
                    'priority': 'medium'
                }
                
                response = client.post(f'{self.base_url}/content/contents/', content_data)
                operations.append(('create_content', response.status_code == 201))
                
                if response.status_code == 201:
                    content_id = response.json()['id']
                    
                    # 콘텐츠 조회
                    response = client.get(f'{self.base_url}/content/contents/{content_id}/')
                    operations.append(('get_content', response.status_code == 200))
                    
                    # 오늘의 복습 조회
                    response = client.get(f'{self.base_url}/review/today/')
                    operations.append(('get_today_reviews', response.status_code == 200))
                    
                    # 복습 완료 (일정 확률로)
                    if len(operations) % 3 == 0:
                        review_data = {
                            'content_id': content_id,
                            'result': 'remembered',
                            'time_spent': 90,
                            'notes': f'스트레스 테스트 복습 {user_index}'
                        }
                        response = client.post(f'{self.base_url}/review/complete/', review_data)
                        operations.append(('complete_review', response.status_code == 201))
                
                # 대시보드 조회
                response = client.get(f'{self.base_url}/analytics/dashboard/')
                operations.append(('get_dashboard', response.status_code == 200))
                
                time.sleep(0.1)  # 짧은 대기
                
            except Exception as e:
                operations.append(('error', False))
        
        # 결과 집계
        total_operations = len(operations)
        successful_operations = sum(1 for _, success in operations if success)
        
        return {
            'user': user_index,
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'operations': operations
        }
    
    def test_concurrent_user_load(self):
        """동시 사용자 부하 테스트"""
        print("\n⚡ 동시 사용자 부하 테스트")
        
        num_concurrent_users = 10
        test_duration = 20  # 20초
        
        print(f"   👥 동시 사용자: {num_concurrent_users}명")
        print(f"   ⏱️ 테스트 시간: {test_duration}초")
        
        start_time = time.time()
        
        # 동시 실행
        with ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            futures = []
            for i in range(num_concurrent_users):
                future = executor.submit(self.simulate_user_activity, i, test_duration)
                futures.append(future)
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=test_duration + 10)
                    results.append(result)
                except Exception as e:
                    results.append({'error': str(e)})
        
        total_time = time.time() - start_time
        
        # 결과 분석
        successful_users = [r for r in results if 'error' not in r]
        failed_users = [r for r in results if 'error' in r]
        
        if successful_users:
            total_ops = sum(r['total_operations'] for r in successful_users)
            successful_ops = sum(r['successful_operations'] for r in successful_users)
            avg_success_rate = sum(r['success_rate'] for r in successful_users) / len(successful_users)
            
            print(f"   ✅ 성공한 사용자: {len(successful_users)}/{num_concurrent_users}")
            print(f"   📊 총 작업 수: {total_ops}")
            print(f"   📊 성공한 작업: {successful_ops}")
            print(f"   📊 평균 성공률: {avg_success_rate:.1f}%")
            print(f"   📊 총 소요 시간: {total_time:.2f}초")
            print(f"   📊 초당 작업 처리: {total_ops/total_time:.1f}개/초")
            
            if failed_users:
                print(f"   ❌ 실패한 사용자: {len(failed_users)}명")
                for failed in failed_users[:3]:  # 처음 3개만 표시
                    print(f"      - 오류: {failed.get('error', 'Unknown error')}")
            
            # 성능 기준 검증
            self.assertGreaterEqual(len(successful_users), num_concurrent_users * 0.8, 
                                  "80% 이상의 사용자가 성공해야 함")
            self.assertGreaterEqual(avg_success_rate, 90.0, 
                                  "평균 성공률이 90% 이상이어야 함")
        else:
            self.fail("모든 사용자가 실패했습니다")
    
    def test_database_connection_stress(self):
        """데이터베이스 연결 스트레스 테스트"""
        print("\n🗄️ 데이터베이스 연결 스트레스 테스트")
        
        def execute_db_operations():
            """데이터베이스 작업 실행"""
            operations = []
            user = self.users[threading.current_thread().ident % len(self.users)]
            
            try:
                for i in range(50):
                    # 콘텐츠 생성
                    content = Content.objects.create(
                        title=f'DB 스트레스 테스트 {threading.current_thread().ident}_{i}',
                        content=f'데이터베이스 스트레스 테스트 콘텐츠 {i}',
                        author=user,
                        category=Category.objects.get_or_create(
                            name=f'DB 테스트 카테고리',
                            user=user,
                            defaults={'description': 'DB 스트레스 테스트용'}
                        )[0]
                    )
                    operations.append(('create', True))
                    
                    # 조회
                    retrieved = Content.objects.get(id=content.id)
                    operations.append(('read', retrieved.id == content.id))
                    
                    # 수정
                    content.title = f'수정된 {content.title}'
                    content.save()
                    operations.append(('update', True))
                    
                    if i % 10 == 0:
                        transaction.commit()
                
                return operations
                
            except Exception as e:
                return [('error', False, str(e))]
        
        # 5개 스레드로 동시 DB 작업
        num_threads = 5
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(execute_db_operations) for _ in range(num_threads)]
            results = [future.result() for future in as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # 결과 집계
        all_operations = []
        for result in results:
            all_operations.extend(result)
        
        total_ops = len(all_operations)
        successful_ops = sum(1 for op in all_operations if len(op) >= 2 and op[1])
        error_ops = [op for op in all_operations if len(op) > 2]
        
        print(f"   📊 총 DB 작업: {total_ops}")
        print(f"   📊 성공한 작업: {successful_ops}")
        print(f"   📊 성공률: {(successful_ops/total_ops*100):.1f}%")
        print(f"   📊 실행 시간: {execution_time:.2f}초")
        print(f"   📊 초당 작업: {total_ops/execution_time:.1f}개/초")
        
        if error_ops:
            print(f"   ❌ 오류 발생: {len(error_ops)}개")
            for error in error_ops[:3]:
                print(f"      - {error[2]}")
        
        # 성능 기준 검증
        self.assertGreaterEqual(successful_ops/total_ops, 0.95, "95% 이상의 DB 작업이 성공해야 함")
        self.assertLess(execution_time, 30.0, "30초 이내에 완료되어야 함")
    
    def test_memory_usage_under_load(self):
        """부하 상황에서 메모리 사용량 테스트"""
        print("\n💾 메모리 사용량 테스트")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 대량 데이터 생성 및 처리
        user = self.users[0]
        category = Category.objects.create(name='메모리 테스트', user=user)
        
        # 메모리 사용량 모니터링하면서 대량 데이터 처리
        memory_readings = [initial_memory]
        
        for batch in range(10):
            # 100개씩 배치로 생성
            contents = []
            for i in range(100):
                content = Content.objects.create(
                    title=f'메모리 테스트 콘텐츠 {batch}_{i}',
                    content='# 메모리 테스트\n\n' + 'x' * 1000,  # 긴 콘텐츠
                    author=user,
                    category=category
                )
                contents.append(content)
            
            # 복습 기록 생성
            for content in contents:
                ReviewHistory.objects.create(
                    content=content,
                    user=user,
                    result='remembered',
                    time_spent=60
                )
            
            # 메모리 사용량 측정
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
            
            # 강제 가비지 컬렉션
            import gc
            gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        max_memory = max(memory_readings)
        memory_increase = final_memory - initial_memory
        
        print(f"   📊 초기 메모리: {initial_memory:.1f}MB")
        print(f"   📊 최종 메모리: {final_memory:.1f}MB")
        print(f"   📊 최대 메모리: {max_memory:.1f}MB")
        print(f"   📊 메모리 증가: {memory_increase:.1f}MB")
        print(f"   📊 증가율: {(memory_increase/initial_memory*100):.1f}%")
        
        # 메모리 사용량이 과도하게 증가하지 않았는지 확인
        self.assertLess(memory_increase, 500, "메모리 증가가 500MB를 초과함")
        self.assertLess(memory_increase/initial_memory, 2.0, "메모리가 초기 대비 2배 이상 증가함")


if __name__ == '__main__':
    print("⚡ 성능 및 스트레스 테스트 실행")
    print("Docker 환경에서 모든 서비스가 실행 중인지 확인하세요.")
    
    import django
    import os
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resee.settings')
    django.setup()
    
    import unittest
    unittest.main()