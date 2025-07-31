"""
샘플 콘텐츠 및 리뷰 데이터 생성
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from content.models import Content, Category
from review.models import ReviewHistory, ReviewSchedule

User = get_user_model()


class Command(BaseCommand):
    help = '테스트를 위한 샘플 데이터 생성'

    def handle(self, *args, **options):
        # 테스트 사용자 가져오기
        try:
            user = User.objects.get(email='test@resee.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('test@resee.com 사용자가 없습니다. 먼저 create_test_users를 실행하세요.'))
            return

        # 카테고리 생성
        categories = []
        category_names = ['프로그래밍', '알고리즘', '데이터베이스', '네트워크', '운영체제', '수학']
        for name in category_names:
            # slug를 자동 생성하기 위해 name과 user로 찾기
            from django.utils.text import slugify
            slug = slugify(name, allow_unicode=True)
            
            category, created = Category.objects.get_or_create(
                name=name,
                user=user,
                defaults={'slug': slug}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'✅ 카테고리 생성: {name}')

        # 콘텐츠 생성
        contents = []
        content_data = [
            ('Python 기초 문법', '파이썬의 기본 문법과 데이터 타입', '프로그래밍'),
            ('리스트 컴프리헨션', '파이썬의 리스트 컴프리헨션 사용법', '프로그래밍'),
            ('데코레이터 패턴', '파이썬 데코레이터의 이해와 활용', '프로그래밍'),
            ('이진 탐색', '효율적인 검색 알고리즘', '알고리즘'),
            ('퀵 정렬', 'O(n log n) 평균 시간복잡도의 정렬 알고리즘', '알고리즘'),
            ('다이나믹 프로그래밍', '복잡한 문제를 간단한 하위 문제로 나누어 해결', '알고리즘'),
            ('SQL 조인', 'INNER, LEFT, RIGHT JOIN의 차이점', '데이터베이스'),
            ('인덱스 최적화', '데이터베이스 쿼리 성능 향상 방법', '데이터베이스'),
            ('트랜잭션 ACID', '원자성, 일관성, 고립성, 지속성', '데이터베이스'),
            ('TCP/IP 프로토콜', '인터넷 통신의 기본 프로토콜', '네트워크'),
            ('HTTP와 HTTPS', '웹 통신 프로토콜의 차이점', '네트워크'),
            ('프로세스와 스레드', '동시성 프로그래밍의 기본 개념', '운영체제'),
            ('가상 메모리', '메모리 관리 기법', '운영체제'),
            ('미분과 적분', '변화율과 누적의 수학적 개념', '수학'),
            ('선형대수', '벡터와 행렬의 기초', '수학'),
        ]

        for title, content_text, category_name in content_data:
            category = next(c for c in categories if c.name == category_name)
            content, created = Content.objects.get_or_create(
                title=title,
                author=user,
                defaults={
                    'content': content_text,
                    'category': category,
                }
            )
            contents.append(content)
            if created:
                self.stdout.write(f'✅ 콘텐츠 생성: {title}')

        # 복습 이력 생성 (최근 30일)
        now = timezone.now()
        for content in contents:
            # 각 콘텐츠에 대해 3-8회의 복습 생성
            review_count = random.randint(3, 8)
            
            for i in range(review_count):
                # 과거 30일 내의 랜덤한 날짜
                days_ago = random.randint(1, 30)
                review_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))
                
                # 성공률은 시간이 지날수록 높아지도록
                base_score = 60 + (i * 5)  # 60%에서 시작해서 점진적으로 향상
                score = min(100, base_score + random.randint(-10, 15))
                
                # score를 result로 변환
                if score >= 80:
                    result = 'remembered'
                elif score >= 60:
                    result = 'partial'
                else:
                    result = 'forgot'
                
                ReviewHistory.objects.create(
                    content=content,
                    user=user,
                    result=result,
                    review_date=review_date,
                    time_spent=random.randint(30, 300),  # 30초 ~ 5분
                    notes=f'자동 생성된 복습 기록 (점수: {score}%)'
                )
            
            self.stdout.write(f'  - {content.title}: {review_count}개 복습 이력 생성')

        # ReviewSchedule 생성
        for content in contents:
            schedule, created = ReviewSchedule.objects.get_or_create(
                content=content,
                user=user,
                defaults={
                    'next_review_date': now + timedelta(days=random.randint(1, 7)),
                    'interval_index': random.randint(0, 3),
                    'initial_review_completed': True
                }
            )
            if created:
                self.stdout.write(f'  - {content.title}: 복습 스케줄 생성')

        self.stdout.write(self.style.SUCCESS('\n🎉 샘플 데이터 생성 완료!'))
        self.stdout.write(f'총 {len(contents)}개의 콘텐츠와 복습 이력이 생성되었습니다.')