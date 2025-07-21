#!/usr/bin/env python3
"""
Docker 환경에서 전체 시스템 검증 스크립트
실제 Docker 컨테이너에서 모든 서비스가 정상 작동하는지 확인
"""

import os
import sys
import time
import json
import requests
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import psycopg2
import redis


@dataclass
class TestResult:
    name: str
    status: str
    message: str
    duration: float
    details: Optional[Dict] = None


class DockerSystemTester:
    """Docker 환경 시스템 테스터"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.results: List[TestResult] = []
        self.test_user_data = {
            'email': 'systemtest@example.com',
            'password': 'SystemTest123!',
            'first_name': 'System',
            'last_name': 'Test'
        }
        self.access_token = None
        
    def run_command(self, command: str) -> Tuple[int, str, str]:
        """시스템 명령어 실행"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def log_result(self, name: str, status: str, message: str, duration: float, details: Optional[Dict] = None):
        """테스트 결과 기록"""
        result = TestResult(name, status, message, duration, details)
        self.results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {name}: {message} ({duration:.2f}s)")
        
        if details:
            for key, value in details.items():
                print(f"   📊 {key}: {value}")
    
    def test_docker_services(self) -> bool:
        """Docker 서비스 상태 확인"""
        print("\n🐳 Docker 서비스 상태 확인")
        start_time = time.time()
        
        try:
            # Docker Compose 서비스 상태 확인
            returncode, stdout, stderr = self.run_command("docker-compose ps")
            
            if returncode != 0:
                self.log_result(
                    "Docker Services Check",
                    "FAIL",
                    f"Docker compose command failed: {stderr}",
                    time.time() - start_time
                )
                return False
            
            # 필수 서비스 목록
            required_services = ['db', 'redis', 'rabbitmq', 'backend', 'frontend']
            running_services = []
            
            for line in stdout.split('\n'):
                if 'Up' in line:
                    service_name = line.split()[0].split('_')[-1]
                    if any(svc in service_name for svc in required_services):
                        running_services.append(service_name)
            
            missing_services = set(required_services) - set(running_services)
            
            if missing_services:
                self.log_result(
                    "Docker Services Check",
                    "FAIL",
                    f"Missing services: {', '.join(missing_services)}",
                    time.time() - start_time
                )
                return False
            
            self.log_result(
                "Docker Services Check",
                "PASS",
                f"All required services running: {', '.join(running_services)}",
                time.time() - start_time,
                {"running_services": len(running_services), "required_services": len(required_services)}
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Docker Services Check",
                "FAIL",
                f"Exception occurred: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_database_connectivity(self) -> bool:
        """PostgreSQL 데이터베이스 연결 테스트"""
        print("\n🗄️ 데이터베이스 연결 테스트")
        start_time = time.time()
        
        try:
            # PostgreSQL 연결 테스트
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="resee_db",
                user="resee_user",
                password="resee_password"
            )
            
            cursor = conn.cursor()
            
            # 기본 쿼리 테스트
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # 테이블 존재 확인
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'accounts_user', 'content_content', 'content_category',
                'review_reviewschedule', 'review_reviewhistory'
            ]
            
            missing_tables = set(required_tables) - set(tables)
            
            cursor.close()
            conn.close()
            
            if missing_tables:
                self.log_result(
                    "Database Connectivity",
                    "FAIL",
                    f"Missing tables: {', '.join(missing_tables)}",
                    time.time() - start_time
                )
                return False
            
            self.log_result(
                "Database Connectivity",
                "PASS",
                f"Database connected successfully",
                time.time() - start_time,
                {
                    "version": version.split()[0:2],
                    "tables_count": len(tables),
                    "required_tables_present": len(required_tables)
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Database Connectivity",
                "FAIL",
                f"Database connection failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_redis_connectivity(self) -> bool:
        """Redis 연결 테스트"""
        print("\n🔴 Redis 연결 테스트")
        start_time = time.time()
        
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            
            # 기본 연결 테스트
            pong = r.ping()
            
            # 읽기/쓰기 테스트
            test_key = 'system_test_key'
            test_value = 'system_test_value'
            
            r.set(test_key, test_value, ex=60)
            stored_value = r.get(test_key)
            
            if stored_value.decode('utf-8') != test_value:
                raise Exception("Redis read/write test failed")
            
            # 정리
            r.delete(test_key)
            
            # Redis 정보 수집
            info = r.info()
            
            self.log_result(
                "Redis Connectivity",
                "PASS",
                "Redis connected and operational",
                time.time() - start_time,
                {
                    "version": info.get('redis_version'),
                    "used_memory": f"{info.get('used_memory_human')}",
                    "connected_clients": info.get('connected_clients')
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Redis Connectivity",
                "FAIL",
                f"Redis connection failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_backend_health(self) -> bool:
        """백엔드 헬스체크 테스트"""
        print("\n🏥 백엔드 헬스체크 테스트")
        start_time = time.time()
        
        try:
            # 기본 헬스체크
            response = requests.get(f"{self.base_url}/api/health/", timeout=10)
            if response.status_code != 200:
                raise Exception(f"Basic health check failed: {response.status_code}")
            
            health_data = response.json()
            
            # 상세 헬스체크
            response = requests.get(f"{self.base_url}/api/health/detailed/", timeout=10)
            if response.status_code != 200:
                raise Exception(f"Detailed health check failed: {response.status_code}")
            
            detailed_health = response.json()
            
            # 모든 체크가 healthy인지 확인
            failed_checks = []
            if detailed_health.get('status') != 'healthy':
                failed_checks.append('overall_status')
            
            checks = detailed_health.get('checks', {})
            for service, status in checks.items():
                if status != 'healthy':
                    failed_checks.append(service)
            
            if failed_checks:
                self.log_result(
                    "Backend Health Check",
                    "FAIL",
                    f"Failed health checks: {', '.join(failed_checks)}",
                    time.time() - start_time,
                    {"failed_checks": failed_checks}
                )
                return False
            
            self.log_result(
                "Backend Health Check",
                "PASS",
                "All health checks passed",
                time.time() - start_time,
                {
                    "service": health_data.get('service'),
                    "checks_passed": len(checks),
                    "database": checks.get('database'),
                    "cache": checks.get('cache'),
                    "celery": checks.get('celery')
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Backend Health Check",
                "FAIL",
                f"Health check failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_frontend_accessibility(self) -> bool:
        """프론트엔드 접근성 테스트"""
        print("\n🌐 프론트엔드 접근성 테스트")
        start_time = time.time()
        
        try:
            # 프론트엔드 메인 페이지 접근
            response = requests.get(self.frontend_url, timeout=10)
            
            if response.status_code != 200:
                raise Exception(f"Frontend not accessible: {response.status_code}")
            
            html_content = response.text
            
            # 기본 HTML 요소 확인
            required_elements = ['<title>', '<meta', '<div id="root"']
            missing_elements = []
            
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if missing_elements:
                self.log_result(
                    "Frontend Accessibility",
                    "FAIL",
                    f"Missing HTML elements: {', '.join(missing_elements)}",
                    time.time() - start_time
                )
                return False
            
            self.log_result(
                "Frontend Accessibility",
                "PASS",
                "Frontend accessible and serving content",
                time.time() - start_time,
                {
                    "status_code": response.status_code,
                    "content_length": len(html_content),
                    "html_elements_found": len(required_elements)
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Frontend Accessibility",
                "FAIL",
                f"Frontend access failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_api_authentication(self) -> bool:
        """API 인증 시스템 테스트"""
        print("\n🔐 API 인증 시스템 테스트")
        start_time = time.time()
        
        try:
            # 1. 사용자 등록
            register_url = f"{self.base_url}/api/accounts/users/"
            register_data = {
                **self.test_user_data,
                'password_confirm': self.test_user_data['password']
            }
            
            response = requests.post(register_url, json=register_data, timeout=10)
            if response.status_code not in [201, 400]:  # 400은 이미 존재하는 경우
                raise Exception(f"User registration failed: {response.status_code} - {response.text}")
            
            # 2. 로그인
            login_url = f"{self.base_url}/api/auth/token/"
            login_data = {
                'email': self.test_user_data['email'],
                'password': self.test_user_data['password']
            }
            
            response = requests.post(login_url, json=login_data, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Login failed: {response.status_code} - {response.text}")
            
            tokens = response.json()
            self.access_token = tokens['access']
            refresh_token = tokens['refresh']
            
            # 3. 인증된 API 호출
            headers = {'Authorization': f'Bearer {self.access_token}'}
            profile_url = f"{self.base_url}/api/accounts/profile/"
            
            response = requests.get(profile_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Authenticated API call failed: {response.status_code}")
            
            profile_data = response.json()
            
            # 4. 토큰 갱신
            refresh_url = f"{self.base_url}/api/auth/token/refresh/"
            refresh_data = {'refresh': refresh_token}
            
            response = requests.post(refresh_url, json=refresh_data, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Token refresh failed: {response.status_code}")
            
            new_tokens = response.json()
            
            self.log_result(
                "API Authentication",
                "PASS",
                "Authentication system working correctly",
                time.time() - start_time,
                {
                    "user_email": profile_data.get('email'),
                    "access_token_length": len(self.access_token),
                    "refresh_token_renewed": 'access' in new_tokens
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "API Authentication",
                "FAIL",
                f"Authentication test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_content_management_workflow(self) -> bool:
        """콘텐츠 관리 워크플로우 테스트"""
        print("\n📝 콘텐츠 관리 워크플로우 테스트")
        start_time = time.time()
        
        if not self.access_token:
            self.log_result(
                "Content Management Workflow",
                "FAIL",
                "No access token available",
                time.time() - start_time
            )
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            # 1. 카테고리 생성
            category_url = f"{self.base_url}/api/content/categories/"
            category_data = {
                'name': '시스템 테스트 카테고리',
                'description': 'Docker 시스템 테스트용 카테고리'
            }
            
            response = requests.post(category_url, json=category_data, headers=headers, timeout=10)
            if response.status_code != 201:
                raise Exception(f"Category creation failed: {response.status_code}")
            
            category = response.json()
            category_id = category['id']
            
            # 2. 콘텐츠 생성
            content_url = f"{self.base_url}/api/content/contents/"
            content_data = {
                'title': 'Docker 시스템 테스트 콘텐츠',
                'content': '# 테스트 콘텐츠\n\n이것은 Docker 환경에서 실행되는 시스템 테스트입니다.',
                'category': category_id,
                'priority': 'high'
            }
            
            response = requests.post(content_url, json=content_data, headers=headers, timeout=10)
            if response.status_code != 201:
                raise Exception(f"Content creation failed: {response.status_code}")
            
            content = response.json()
            content_id = content['id']
            
            # 3. 콘텐츠 조회
            response = requests.get(f"{content_url}{content_id}/", headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Content retrieval failed: {response.status_code}")
            
            retrieved_content = response.json()
            
            # 4. 콘텐츠 수정
            update_data = {
                'title': 'Docker 시스템 테스트 콘텐츠 (수정됨)',
                'content': retrieved_content['content'] + '\n\n## 수정사항\n콘텐츠가 수정되었습니다.',
                'category': category_id,
                'priority': 'medium'
            }
            
            response = requests.put(f"{content_url}{content_id}/", json=update_data, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Content update failed: {response.status_code}")
            
            updated_content = response.json()
            
            self.log_result(
                "Content Management Workflow",
                "PASS",
                "Complete content workflow successful",
                time.time() - start_time,
                {
                    "category_created": category['name'],
                    "content_created": content['title'],
                    "content_updated": updated_content['title'],
                    "content_id": content_id,
                    "category_id": category_id
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Content Management Workflow",
                "FAIL",
                f"Content workflow failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_review_system_workflow(self) -> bool:
        """복습 시스템 워크플로우 테스트"""
        print("\n🧠 복습 시스템 워크플로우 테스트")
        start_time = time.time()
        
        if not self.access_token:
            self.log_result(
                "Review System Workflow",
                "FAIL",
                "No access token available",
                time.time() - start_time
            )
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            # 1. 오늘의 복습 목록 조회
            today_reviews_url = f"{self.base_url}/api/review/today/"
            response = requests.get(today_reviews_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Today reviews retrieval failed: {response.status_code}")
            
            today_reviews = response.json()
            
            if not today_reviews:
                self.log_result(
                    "Review System Workflow",
                    "SKIP",
                    "No reviews available for today",
                    time.time() - start_time
                )
                return True
            
            # 2. 첫 번째 복습 완료
            review_content = today_reviews[0]
            complete_review_url = f"{self.base_url}/api/review/complete/"
            review_data = {
                'content_id': review_content['content']['id'],
                'result': 'remembered',
                'time_spent': 90,
                'notes': 'Docker 시스템 테스트에서 완료된 복습'
            }
            
            response = requests.post(complete_review_url, json=review_data, headers=headers, timeout=10)
            if response.status_code != 201:
                raise Exception(f"Review completion failed: {response.status_code}")
            
            review_result = response.json()
            
            # 3. 복습 기록 확인
            history_url = f"{self.base_url}/api/review/history/"
            response = requests.get(history_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Review history retrieval failed: {response.status_code}")
            
            history = response.json()
            
            # 4. 복습 통계 확인
            stats_url = f"{self.base_url}/api/analytics/dashboard/"
            response = requests.get(stats_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Review stats retrieval failed: {response.status_code}")
            
            stats = response.json()
            
            self.log_result(
                "Review System Workflow",
                "PASS",
                "Review system workflow completed",
                time.time() - start_time,
                {
                    "today_reviews_count": len(today_reviews),
                    "review_completed": review_result.get('id') is not None,
                    "history_count": len(history.get('results', [])),
                    "success_rate": stats.get('success_rate', 0)
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Review System Workflow",
                "FAIL",
                f"Review workflow failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_analytics_dashboard(self) -> bool:
        """분석 대시보드 테스트"""
        print("\n📊 분석 대시보드 테스트")
        start_time = time.time()
        
        if not self.access_token:
            self.log_result(
                "Analytics Dashboard",
                "FAIL",
                "No access token available",
                time.time() - start_time
            )
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            # 1. 대시보드 데이터
            dashboard_url = f"{self.base_url}/api/analytics/dashboard/"
            response = requests.get(dashboard_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Dashboard data retrieval failed: {response.status_code}")
            
            dashboard_data = response.json()
            
            # 2. 복습 통계
            stats_url = f"{self.base_url}/api/analytics/review-stats/"
            response = requests.get(stats_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Review stats retrieval failed: {response.status_code}")
            
            stats_data = response.json()
            
            # 3. 고급 분석
            advanced_url = f"{self.base_url}/api/analytics/advanced/"
            response = requests.get(advanced_url, headers=headers, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Advanced analytics retrieval failed: {response.status_code}")
            
            advanced_data = response.json()
            
            # 데이터 유효성 검증
            required_dashboard_fields = ['total_content', 'success_rate', 'today_reviews']
            missing_fields = [field for field in required_dashboard_fields if field not in dashboard_data]
            
            if missing_fields:
                raise Exception(f"Missing dashboard fields: {missing_fields}")
            
            self.log_result(
                "Analytics Dashboard",
                "PASS",
                "All analytics endpoints working",
                time.time() - start_time,
                {
                    "total_content": dashboard_data.get('total_content'),
                    "success_rate": dashboard_data.get('success_rate'),
                    "today_reviews": dashboard_data.get('today_reviews'),
                    "stats_available": bool(stats_data),
                    "advanced_available": bool(advanced_data)
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Analytics Dashboard",
                "FAIL",
                f"Analytics test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def test_concurrent_operations(self) -> bool:
        """동시 작업 처리 테스트"""
        print("\n⚡ 동시 작업 처리 테스트")
        start_time = time.time()
        
        if not self.access_token:
            self.log_result(
                "Concurrent Operations",
                "FAIL",
                "No access token available",
                time.time() - start_time
            )
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            def create_content(index: int) -> Tuple[bool, str]:
                """콘텐츠 생성 함수"""
                try:
                    content_url = f"{self.base_url}/api/content/contents/"
                    content_data = {
                        'title': f'동시 테스트 콘텐츠 {index}',
                        'content': f'# 콘텐츠 {index}\n\n동시 생성 테스트용 콘텐츠입니다.',
                        'priority': 'low'
                    }
                    
                    response = requests.post(content_url, json=content_data, headers=headers, timeout=15)
                    if response.status_code == 201:
                        return True, f"Content {index} created successfully"
                    else:
                        return False, f"Content {index} creation failed: {response.status_code}"
                except Exception as e:
                    return False, f"Content {index} error: {str(e)}"
            
            # 10개 콘텐츠 동시 생성
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_content, i) for i in range(1, 11)]
                results = [future.result() for future in futures]
            
            successful_operations = sum(1 for success, _ in results if success)
            failed_operations = len(results) - successful_operations
            
            if failed_operations > 2:  # 20% 이상 실패시 FAIL
                error_messages = [msg for success, msg in results if not success]
                self.log_result(
                    "Concurrent Operations",
                    "FAIL",
                    f"Too many failed operations: {failed_operations}/10",
                    time.time() - start_time,
                    {"error_messages": error_messages[:3]}  # 처음 3개만 표시
                )
                return False
            
            self.log_result(
                "Concurrent Operations",
                "PASS",
                f"Concurrent operations handled successfully",
                time.time() - start_time,
                {
                    "total_operations": len(results),
                    "successful_operations": successful_operations,
                    "failed_operations": failed_operations,
                    "success_rate": f"{(successful_operations/len(results)*100):.1f}%"
                }
            )
            return True
            
        except Exception as e:
            self.log_result(
                "Concurrent Operations",
                "FAIL",
                f"Concurrent test failed: {str(e)}",
                time.time() - start_time
            )
            return False
    
    def generate_report(self) -> Dict:
        """테스트 결과 리포트 생성"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        skipped_tests = len([r for r in self.results if r.status == "SKIP"])
        
        total_duration = sum(r.duration for r in self.results)
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
                "total_duration": f"{total_duration:.2f}s"
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "duration": f"{r.duration:.2f}s",
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        return report
    
    def run_all_tests(self) -> bool:
        """모든 테스트 실행"""
        print("🚀 Docker 시스템 종합 테스트 시작")
        print("=" * 60)
        
        test_sequence = [
            ("Docker 서비스 상태", self.test_docker_services),
            ("데이터베이스 연결", self.test_database_connectivity),
            ("Redis 연결", self.test_redis_connectivity),
            ("백엔드 헬스체크", self.test_backend_health),
            ("프론트엔드 접근성", self.test_frontend_accessibility),
            ("API 인증 시스템", self.test_api_authentication),
            ("콘텐츠 관리 워크플로우", self.test_content_management_workflow),
            ("복습 시스템 워크플로우", self.test_review_system_workflow),
            ("분석 대시보드", self.test_analytics_dashboard),
            ("동시 작업 처리", self.test_concurrent_operations),
        ]
        
        overall_success = True
        
        for test_name, test_func in test_sequence:
            try:
                success = test_func()
                if not success:
                    overall_success = False
            except Exception as e:
                print(f"❌ {test_name}: 예외 발생 - {str(e)}")
                overall_success = False
            
            time.sleep(1)  # 테스트 간 간격
        
        print("\n" + "=" * 60)
        
        # 리포트 생성 및 출력
        report = self.generate_report()
        
        print(f"\n📋 테스트 결과 요약:")
        print(f"   총 테스트: {report['summary']['total_tests']}")
        print(f"   성공: {report['summary']['passed']}")
        print(f"   실패: {report['summary']['failed']}")
        print(f"   건너뜀: {report['summary']['skipped']}")
        print(f"   성공률: {report['summary']['success_rate']}")
        print(f"   총 소요시간: {report['summary']['total_duration']}")
        
        # 리포트 파일 저장
        with open('docker_system_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 상세 리포트가 'docker_system_test_report.json'에 저장되었습니다.")
        
        return overall_success


def main():
    """메인 함수"""
    print("🐳 Resee Docker 시스템 테스트")
    print("현재 Docker Compose가 실행 중인지 확인하세요.")
    print("실행 명령어: docker-compose up -d")
    
    input("\n준비가 되면 Enter를 눌러 테스트를 시작하세요...")
    
    tester = DockerSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ 모든 시스템 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        print("\n❌ 일부 테스트가 실패했습니다. 리포트를 확인해주세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())