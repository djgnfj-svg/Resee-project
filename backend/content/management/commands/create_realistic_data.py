"""
실제 사용자처럼 복잡하고 현실적인 학습 데이터 생성
30일간 꾸준한 학습 패턴, 다양한 카테고리, 시간대별 학습 패턴 등을 포함
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime, time
import random
import math
from content.models import Content, Category
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class Command(BaseCommand):
    help = '실제 사용자처럼 현실적인 학습 데이터 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@resee.com',
            help='대상 사용자 이메일 (기본값: test@resee.com)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='생성할 학습 데이터 일수 (기본값: 30일)'
        )

    def handle(self, *args, **options):
        email = options['email']
        days = options['days']
        
        # 사용자 가져오기
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'{email} 사용자가 없습니다.'))
            return

        # 기존 데이터 정리
        self.stdout.write('기존 데이터 정리 중...')
        ReviewHistory.objects.filter(user=user).delete()
        ReviewSchedule.objects.filter(user=user).delete()
        Content.objects.filter(author=user).delete()
        Category.objects.filter(user=user).delete()
        
        self.stdout.write(f'🚀 {email}을 위한 현실적인 학습 데이터 생성 시작')
        
        # 카테고리 생성 (더 다양하고 현실적인 카테고리)
        categories = self.create_categories(user)
        
        # 콘텐츠 생성 (더 많고 다양한 콘텐츠)
        contents = self.create_contents(user, categories)
        
        # 현실적인 학습 패턴으로 복습 데이터 생성
        self.create_realistic_review_data(user, contents, days)
        
        # 사용자 프로필 업데이트 (주간 목표 설정)
        self.update_user_profile(user)
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 현실적인 학습 데이터 생성 완료!'))
        self.stdout.write(f'총 {len(contents)}개의 콘텐츠와 {days}일간의 학습 이력이 생성되었습니다.')

    def create_categories(self, user):
        """다양한 카테고리 생성"""
        category_data = [
            ('프로그래밍', '💻'),
            ('알고리즘', '🧮'),
            ('데이터베이스', '🗄️'),
            ('네트워크', '🌐'),
            ('운영체제', '⚙️'),
            ('수학', '📊'),
            ('영어', '🇺🇸'),
            ('프론트엔드', '🎨'),
            ('백엔드', '⚡'),
            ('데브옵스', '🚀'),
            ('머신러닝', '🤖'),
            ('보안', '🔒'),
            ('모바일', '📱'),
            ('클라우드', '☁️'),
            ('디자인 패턴', '🏗️'),
        ]
        
        categories = []
        for name, emoji in category_data:
            from django.utils.text import slugify
            slug = slugify(name, allow_unicode=True)
            
            category, created = Category.objects.get_or_create(
                name=name,
                user=user,
                defaults={'slug': slug}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'✅ 카테고리 생성: {emoji} {name}')
        
        return categories

    def create_contents(self, user, categories):
        """현실적이고 다양한 콘텐츠 생성"""
        content_data = [
            # 프로그래밍
            ('Python 기초 문법', 'Python의 변수, 함수, 클래스 등 기본 문법 정리', '프로그래밍'),
            ('리스트 컴프리헨션', 'Python의 리스트 컴프리헨션 패턴과 활용법', '프로그래밍'),
            ('데코레이터 패턴', 'Python 데코레이터의 작동 원리와 실제 사용 예시', '프로그래밍'),
            ('제너레이터와 이터레이터', 'Python의 메모리 효율적 데이터 처리 방법', '프로그래밍'),
            ('Context Manager', 'with문과 __enter__, __exit__ 메서드 활용법', '프로그래밍'),
            
            # 알고리즘
            ('이진 탐색', 'O(log n) 시간복잡도의 효율적인 검색 알고리즘', '알고리즘'),
            ('퀵 정렬', '분할 정복을 이용한 O(n log n) 정렬 알고리즘', '알고리즘'),
            ('다이나믹 프로그래밍', '메모이제이션을 활용한 최적화 기법', '알고리즘'),
            ('그래프 탐색 (DFS/BFS)', '깊이 우선 탐색과 너비 우선 탐색의 차이점', '알고리즘'),
            ('최단 경로 알고리즘', '다익스트라와 플로이드-워셜 알고리즘', '알고리즘'),
            
            # 데이터베이스
            ('SQL 조인 종류', 'INNER, LEFT, RIGHT, FULL OUTER JOIN의 차이점', '데이터베이스'),
            ('인덱스 최적화', 'B-Tree 인덱스와 쿼리 성능 향상 방법', '데이터베이스'),
            ('트랜잭션 ACID', '원자성, 일관성, 고립성, 지속성의 개념과 중요성', '데이터베이스'),
            ('정규화와 비정규화', '테이블 설계 시 고려사항과 성능 트레이드오프', '데이터베이스'),
            ('NoSQL vs SQL', 'MongoDB, Redis 등 NoSQL의 특징과 사용 케이스', '데이터베이스'),
            
            # 네트워크
            ('TCP/IP 프로토콜', '인터넷 통신의 기본 4계층 모델', '네트워크'),
            ('HTTP와 HTTPS', 'SSL/TLS를 이용한 보안 웹 통신', '네트워크'),
            ('RESTful API 설계', 'REST 아키텍처 원칙과 좋은 API 설계 방법', '네트워크'),
            ('DNS 작동 원리', '도메인 이름을 IP 주소로 변환하는 과정', '네트워크'),
            ('로드 밸런싱', '트래픽 분산을 위한 다양한 전략과 알고리즘', '네트워크'),
            
            # 운영체제
            ('프로세스와 스레드', '동시성 프로그래밍의 기본 개념과 차이점', '운영체제'),
            ('가상 메모리', '페이징과 세그멘테이션을 통한 메모리 관리', '운영체제'),
            ('CPU 스케줄링', 'FCFS, SJF, Round Robin 등 스케줄링 알고리즘', '운영체제'),
            ('데드락과 해결방법', '교착상태의 4가지 조건과 예방/회피/탐지 기법', '운영체제'),
            ('파일 시스템', 'inode 구조와 디렉터리 관리 방식', '운영체제'),
            
            # 프론트엔드
            ('React Hooks 패턴', 'useState, useEffect, useContext 활용법', '프론트엔드'),
            ('CSS Grid vs Flexbox', '레이아웃을 위한 두 가지 방식의 차이점', '프론트엔드'),
            ('웹 성능 최적화', '번들 크기 줄이기, 지연 로딩, 캐싱 전략', '프론트엔드'),
            ('브라우저 렌더링 과정', 'DOM 트리 생성부터 화면 출력까지의 과정', '프론트엔드'),
            ('TypeScript 고급 타입', '제네릭, 유니온 타입, 조건부 타입 활용', '프론트엔드'),
            
            # 백엔드
            ('Django ORM 최적화', 'select_related, prefetch_related 활용법', '백엔드'),
            ('캐싱 전략', 'Redis를 이용한 다양한 캐싱 패턴', '백엔드'),
            ('API 인증과 권한', 'JWT, OAuth, Session 기반 인증 방식 비교', '백엔드'),
            ('마이크로서비스 아키텍처', '모놀리식과 마이크로서비스의 장단점', '백엔드'),
            ('메시지 큐 시스템', 'RabbitMQ, Kafka를 이용한 비동기 처리', '백엔드'),
            
            # 기타 카테고리들
            ('영어 기술 단어', '프로그래밍에서 자주 사용되는 영어 용어들', '영어'),
            ('Docker 컨테이너', '컨테이너화와 이미지 관리 방법', '데브옵스'),
            ('AWS 서비스 이해', 'EC2, S3, RDS 등 주요 서비스 개념', '클라우드'),
            ('싱글톤 패턴', '인스턴스를 하나만 생성하는 디자인 패턴', '디자인 패턴'),
            ('선형 회귀', '기계학습의 기본 회귀 알고리즘', '머신러닝'),
        ]
        
        contents = []
        for title, content_text, category_name in content_data:
            category = next((c for c in categories if c.name == category_name), categories[0])
            
            # 콘텐츠 생성일을 랜덤하게 설정 (최근 2개월 내)
            days_ago = random.randint(1, 60)
            created_at = timezone.now() - timedelta(days=days_ago)
            
            content = Content.objects.create(
                title=title,
                content=content_text,
                author=user,
                category=category,
                created_at=created_at,
                updated_at=created_at
            )
            contents.append(content)
            self.stdout.write(f'✅ 콘텐츠 생성: {title}')
        
        return contents

    def create_realistic_review_data(self, user, contents, days):
        """현실적인 학습 패턴으로 복습 데이터 생성"""
        now = timezone.now()
        
        # 사용자의 학습 패턴 설정 (실제 사용자처럼)
        user_patterns = {
            'morning_person': True,  # 아침형 인간
            'consistency': 0.8,  # 80% 확률로 꾸준히 학습
            'weekend_less': True,  # 주말에는 학습량 감소
            'improvement_rate': 0.1,  # 시간이 지날수록 실력 향상
            'preferred_hours': [7, 8, 9, 20, 21, 22],  # 선호 학습 시간
            'break_days': [3, 10, 17, 24],  # 가끔 쉬는 날들
        }
        
        total_reviews = 0
        
        # 날짜별로 학습 데이터 생성
        for day in range(days):
            current_date = now - timedelta(days=days - day)
            
            # 주말 여부 확인
            is_weekend = current_date.weekday() >= 5
            
            # 쉬는 날 확인
            is_break_day = day in user_patterns['break_days']
            
            # 학습 여부 결정
            study_probability = user_patterns['consistency']
            if is_weekend and user_patterns['weekend_less']:
                study_probability *= 0.6
            if is_break_day:
                study_probability = 0.1
                
            if random.random() > study_probability:
                continue  # 이날은 학습 안함
            
            # 하루 학습량 결정 (1-8개 콘텐츠)
            if is_weekend:
                daily_reviews = random.choices([1, 2, 3, 4], weights=[30, 40, 20, 10])[0]
            else:
                daily_reviews = random.choices([2, 3, 4, 5, 6], weights=[20, 30, 25, 15, 10])[0]
            
            # 학습 시간 패턴 생성
            study_sessions = self.generate_study_sessions(current_date, daily_reviews, user_patterns)
            
            # 각 세션에서 복습할 콘텐츠 선택
            available_contents = list(contents)
            
            for session_time, session_reviews in study_sessions:
                # 복습할 콘텐츠 랜덤 선택
                session_contents = random.sample(available_contents, min(session_reviews, len(available_contents)))
                
                for content in session_contents:
                    # 학습 시간에 따른 성과 변화
                    base_performance = 0.6 + (day * user_patterns['improvement_rate'] / days)
                    base_performance = min(0.9, base_performance)  # 최대 90%
                    
                    # 시간대별 성과 조정 (집중도 반영)
                    hour = session_time.hour
                    if hour in user_patterns['preferred_hours']:
                        performance_modifier = 1.2
                    elif hour < 6 or hour > 23:
                        performance_modifier = 0.7
                    else:
                        performance_modifier = 1.0
                    
                    final_performance = base_performance * performance_modifier
                    final_performance = min(1.0, final_performance)
                    
                    # 성과를 점수로 변환
                    score = final_performance * 100 + random.uniform(-15, 15)
                    score = max(0, min(100, score))
                    
                    # 결과 결정
                    if score >= 80:
                        result = 'remembered'
                    elif score >= 60:
                        result = 'partial'
                    else:
                        result = 'forgot'
                    
                    # 학습 시간 계산 (현실적인 시간)
                    base_time = 120  # 2분
                    if result == 'forgot':
                        time_spent = base_time + random.randint(60, 240)  # 3-6분
                    elif result == 'partial':
                        time_spent = base_time + random.randint(30, 120)  # 2.5-4분
                    else:
                        time_spent = base_time + random.randint(0, 60)  # 2-3분
                    
                    # 복습 이력 생성
                    ReviewHistory.objects.create(
                        content=content,
                        user=user,
                        result=result,
                        review_date=session_time,
                        time_spent=time_spent,
                        notes=self.generate_realistic_notes(result, content.title)
                    )
                    
                    total_reviews += 1
            
            self.stdout.write(f'  📅 {current_date.strftime("%m/%d")}: {daily_reviews}회 복습')
        
        # ReviewSchedule 생성 (미래 복습 계획)
        for content in contents:
            # 에빙하우스 망각곡선 기반 간격 설정
            intervals = [1, 3, 7, 14, 30]  # 일 단위
            
            # 해당 콘텐츠의 마지막 복습 확인
            last_review = ReviewHistory.objects.filter(
                content=content, user=user
            ).order_by('-review_date').first()
            
            if last_review:
                # 마지막 복습 결과에 따라 다음 복습 간격 결정
                if last_review.result == 'remembered':
                    interval_index = min(4, random.randint(2, 4))
                elif last_review.result == 'partial':
                    interval_index = random.randint(1, 2)
                else:
                    interval_index = 0
                
                next_review_date = last_review.review_date.date() + timedelta(days=intervals[interval_index])
            else:
                # 복습한 적 없으면 곧 복습 예정
                interval_index = 0
                next_review_date = now.date() + timedelta(days=random.randint(1, 3))
            
            # timezone-aware datetime으로 변환
            next_review_datetime = timezone.make_aware(
                datetime.combine(next_review_date, datetime.min.time())
            )
            
            schedule, created = ReviewSchedule.objects.get_or_create(
                content=content,
                user=user,
                defaults={
                    'next_review_date': next_review_datetime,
                    'interval_index': interval_index,
                    'initial_review_completed': True
                }
            )
        
        self.stdout.write(f'📊 총 {total_reviews}개의 복습 이력 생성 완료')

    def generate_study_sessions(self, date, total_reviews, patterns):
        """하루 동안의 학습 세션 생성"""
        sessions = []
        
        # 학습 세션 수 결정 (1-3개 세션)
        session_count = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
        
        # 세션별 복습 수 분배
        if session_count == 1 or total_reviews == 1:
            session_reviews = [total_reviews]
        elif session_count == 2:
            if total_reviews == 2:
                session_reviews = [1, 1]
            else:
                first_session = random.randint(1, total_reviews - 1)
                session_reviews = [first_session, total_reviews - first_session]
        else:  # 3 sessions
            if total_reviews <= 3:
                session_reviews = [1] * total_reviews + [0] * (3 - total_reviews)
                session_reviews = [r for r in session_reviews if r > 0]
            else:
                first = random.randint(1, max(1, total_reviews - 2))
                second = random.randint(1, max(1, total_reviews - first - 1))
                third = total_reviews - first - second
                session_reviews = [first, second, third]
        
        # 각 세션의 시간 결정
        preferred_hours = patterns['preferred_hours']
        for i, reviews in enumerate(session_reviews):
            if i == 0:  # 첫 번째 세션 (주로 아침이나 저녁)
                hour = random.choice(preferred_hours)
            elif i == 1:  # 두 번째 세션
                hour = random.choice([12, 13, 14, 20, 21, 22])
            else:  # 세 번째 세션
                hour = random.choice([22, 23])
            
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            session_time = datetime.combine(
                date.date(),
                time(hour, minute, second)
            )
            session_time = timezone.make_aware(session_time)
            
            sessions.append((session_time, reviews))
        
        return sorted(sessions, key=lambda x: x[0])

    def generate_realistic_notes(self, result, content_title):
        """결과에 따른 현실적인 노트 생성"""
        if result == 'remembered':
            notes = [
                "완벽히 기억하고 있음!",
                "이해도가 높아졌음",
                "응용까지 가능한 수준",
                "확실히 알고 있음",
                "설명도 가능함",
                "개념이 명확함"
            ]
        elif result == 'partial':
            notes = [
                "대략적으로는 기억하지만 세부사항이 애매함",
                "키워드는 기억하는데 설명이 부족함",
                "조금 더 복습이 필요함",
                "거의 다 기억하지만 확신이 부족",
                "비슷한 개념과 헷갈림",
                "예시를 더 봐야겠음"
            ]
        else:  # forgot
            notes = [
                "완전히 까먹었음. 다시 공부 필요",
                "기억이 안 남. 처음부터 다시",
                "개념 자체를 잊어버림",
                "더 자주 복습해야겠음",
                "이해가 부족했던 것 같음",
                "기본기부터 다시 정리 필요"
            ]
        
        return random.choice(notes)

    def update_user_profile(self, user):
        """사용자 프로필 업데이트"""
        user.weekly_goal = 25  # 주 25회 복습 목표
        user.save()
        
        self.stdout.write(f'👤 사용자 프로필 업데이트: 주간 목표 {user.weekly_goal}회')