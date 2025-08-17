"""
Management command to create realistic user data with 40 days of daily activity
"""

import json
import random
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Subscription, SubscriptionTier
from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule
from review.utils import get_review_intervals

User = get_user_model()


class Command(BaseCommand):
    help = 'Create realistic user data simulating 40 days of daily learning activity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing realistic test data before creating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing realistic test data...')
            self.clear_realistic_data()

        self.stdout.write('Creating realistic user data (40 days of activity)...')
        
        # Create realistic user
        user = self.create_realistic_user()
        
        # Create categories
        categories = self.create_categories()
        
        # Simulate 40 days of learning
        self.simulate_40_days_learning(user, categories)
        
        # Display summary
        self.display_summary(user)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created realistic user data!'
            )
        )

    def clear_realistic_data(self):
        """Clear existing realistic test data"""
        # Delete user (will cascade delete related data)
        user = User.objects.filter(email='realistic_learner@resee.com').first()
        if user:
            # Delete all content and related data
            Content.objects.filter(author=user).delete()
            ReviewSchedule.objects.filter(user=user).delete()
            ReviewHistory.objects.filter(user=user).delete()
            user.delete()
        
        # Clean up categories
        Category.objects.filter(name__startswith='실전 학습').delete()

    def create_realistic_user(self):
        """Create a realistic user with PRO subscription"""
        user, created = User.objects.get_or_create(
            email='realistic_learner@resee.com',
            defaults={
                'username': '열정적인 학습자',
                'is_email_verified': True,
                'weekly_goal': 30  # Realistic weekly goal
            }
        )
        
        if created:
            user.set_password('test123!')
            user.save()
        
        # Set PRO subscription (for full feature access)
        user.subscription.tier = SubscriptionTier.PRO
        user.subscription.is_active = True
        user.subscription.start_date = timezone.now() - timedelta(days=45)
        user.subscription.end_date = timezone.now() + timedelta(days=320)
        user.subscription.save()
        
        self.stdout.write(
            f'Created realistic user: {user.username} with PRO tier '
            f'(max interval: {user.subscription.max_interval_days} days)'
        )
        
        return user

    def create_categories(self):
        """Create realistic categories"""
        categories = []
        
        category_data = [
            ('실전 학습 - 프로그래밍', '프로그래밍 언어와 기술 학습'),
            ('실전 학습 - 영어', '영어 단어와 문법 학습'),
            ('실전 학습 - 자기계발', '독서 노트와 인사이트'),
            ('실전 학습 - 업무 스킬', '업무 관련 지식과 스킬'),
        ]
        
        for name, description in category_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'slug': name.lower().replace(' ', '-'),
                    'description': description
                }
            )
            categories.append(category)
            
            if created:
                self.stdout.write(f'Created category: {name}')
        
        return categories

    def simulate_40_days_learning(self, user, categories):
        """Simulate 40 days of realistic learning activity"""
        
        # Learning content templates - realistic topics
        learning_templates = {
            '실전 학습 - 프로그래밍': [
                ('Python 리스트 컴프리헨션', 'squares = [x**2 for x in range(10)]\n짝수만: even = [x for x in range(10) if x % 2 == 0]'),
                ('JavaScript async/await', 'async function fetchData() {\n  const response = await fetch(url);\n  return await response.json();\n}'),
                ('React useState Hook', 'const [count, setCount] = useState(0);\n// 상태 업데이트: setCount(count + 1)'),
                ('Django ORM 쿼리 최적화', 'Model.objects.select_related("foreign_key")\n.prefetch_related("many_to_many")'),
                ('Git rebase vs merge', 'rebase: 히스토리를 깔끔하게\nmerge: 모든 커밋 보존'),
                ('SQL JOIN 종류', 'INNER JOIN: 교집합\nLEFT JOIN: 왼쪽 테이블 전체\nRIGHT JOIN: 오른쪽 테이블 전체'),
                ('Python 데코레이터', '@functools.wraps(func)\ndef decorator(func):\n    def wrapper(*args):\n        return func(*args)'),
                ('TypeScript 제네릭', 'function identity<T>(arg: T): T {\n    return arg;\n}'),
                ('Docker 기본 명령어', 'docker build -t image .\ndocker run -p 8000:8000 image\ndocker-compose up -d'),
                ('REST API 설계 원칙', 'GET: 조회\nPOST: 생성\nPUT: 전체 수정\nPATCH: 부분 수정\nDELETE: 삭제'),
            ],
            '실전 학습 - 영어': [
                ('implement', '구현하다\nWe need to implement the new feature by Friday.'),
                ('deprecate', '사용 중단 예정\nThis method is deprecated and will be removed in v3.0'),
                ('refactor', '리팩토링하다\nWe should refactor this code to improve readability.'),
                ('resilient', '회복력 있는, 탄력적인\nThe system needs to be resilient to failures.'),
                ('concurrent', '동시에 일어나는\nThe server can handle 1000 concurrent connections.'),
                ('idempotent', '멱등성의\nPUT requests should be idempotent.'),
                ('asynchronous', '비동기의\nJavaScript uses asynchronous programming patterns.'),
                ('scalable', '확장 가능한\nWe need a scalable architecture for growth.'),
                ('robust', '견고한\nThe application needs robust error handling.'),
                ('optimize', '최적화하다\nWe need to optimize the database queries.'),
            ],
            '실전 학습 - 자기계발': [
                ('파레토 법칙', '20%의 노력으로 80%의 결과를 얻는다.\n핵심 20%에 집중하자.'),
                ('포모도로 기법', '25분 집중 + 5분 휴식\n4회 반복 후 긴 휴식(15-30분)'),
                ('SMART 목표 설정', 'Specific(구체적)\nMeasurable(측정가능)\nAchievable(달성가능)\nRelevant(관련성)\nTime-bound(기한)'),
                ('1만 시간의 법칙', '전문가가 되려면 1만 시간의 의도적 연습이 필요\n하루 3시간 = 약 10년'),
                ('복리 효과', '매일 1%씩 성장하면\n1년 후 37배 성장 (1.01^365 = 37.78)'),
                ('아이젠하워 매트릭스', '긴급+중요: 즉시 처리\n중요+긴급X: 계획하여 처리\n긴급+중요X: 위임\n긴급X+중요X: 제거'),
                ('5 Why 기법', '문제의 근본 원인 찾기\n"왜?"를 5번 반복하여 진짜 원인 파악'),
                ('칸반 보드', 'To Do | In Progress | Done\n업무 시각화와 흐름 관리'),
                ('회고의 중요성', '무엇이 잘 되었나?\n무엇이 개선되어야 하나?\n다음에 시도할 것은?'),
                ('성장 마인드셋', '실패는 학습의 기회\n노력하면 능력이 향상된다\n도전을 두려워하지 않기'),
            ],
            '실전 학습 - 업무 스킬': [
                ('효과적인 이메일 작성', '제목: 명확하고 구체적으로\n본문: 결론 먼저, 상세 내용은 뒤에\n액션 아이템 명시'),
                ('회의 진행 스킬', '사전 안건 공유\n시간 엄수\n회의록 작성 및 공유\n액션 아이템과 담당자 명시'),
                ('프레젠테이션 구조', '도입: 문제 제기\n본론: 해결책 제시\n결론: 핵심 메시지 반복'),
                ('피드백 주는 법', 'SBI 모델\nSituation(상황)\nBehavior(행동)\nImpact(영향)'),
                ('시간 관리 기법', '타임 블로킹: 시간대별 업무 할당\n배치 처리: 비슷한 업무 모아서 처리'),
                ('문서화의 중요성', '미래의 나와 동료를 위해\n왜(Why) > 무엇(What) > 어떻게(How)'),
                ('코드 리뷰 에티켓', '구체적이고 건설적인 피드백\n좋은 점도 언급\n대안 제시'),
                ('애자일 스크럼', '스프린트: 1-4주 단위\n데일리 스탠드업\n스프린트 리뷰와 회고'),
                ('OKR 설정', 'Objectives: 목표 (정성적)\nKey Results: 핵심 결과 (정량적)\n분기별 설정 및 리뷰'),
                ('네트워킹 스킬', '먼저 도움 주기\n정기적인 연락 유지\n상호 이익 추구'),
            ]
        }
        
        # Start date: 40 days ago
        start_date = timezone.now() - timedelta(days=40)
        
        # Track all created content for review simulation
        all_contents = []
        
        # Simulate each day
        for day in range(40):
            current_date = start_date + timedelta(days=day)
            
            # Determine how many contents to create this day (1-3, weighted towards 1-2)
            contents_today = random.choices([1, 2, 3], weights=[50, 40, 10])[0]
            
            for _ in range(contents_today):
                # Choose a random category
                category = random.choice(categories)
                
                # Get templates for this category
                templates = learning_templates.get(category.name, [])
                if not templates:
                    continue
                
                # Choose a random template
                template = random.choice(templates)
                title, content_text = template
                
                # Add some variation to the content
                content_text += f"\n\n📅 학습일: {current_date.strftime('%Y년 %m월 %d일')}"
                content_text += f"\n💡 추가 메모: {self.get_random_note()}"
                
                # Create content with the specific date
                content = Content.objects.create(
                    title=f"{title} ({current_date.strftime('%m/%d')})",
                    content=content_text,
                    author=user,
                    category=category,
                    priority=random.choice(['high', 'medium', 'low'])
                )
                
                # Override created_at to simulate creation on that day
                Content.objects.filter(id=content.id).update(
                    created_at=current_date.replace(hour=random.randint(8, 22), minute=random.randint(0, 59))
                )
                
                # Create initial review schedule (use get_or_create to avoid duplicates)
                schedule, created = ReviewSchedule.objects.get_or_create(
                    content=content,
                    user=user,
                    defaults={
                        'next_review_date': current_date + timedelta(days=1),
                        'interval_index': 0,
                        'initial_review_completed': False,
                        'is_active': True
                    }
                )
                
                # Override created_at for schedule
                ReviewSchedule.objects.filter(id=schedule.id).update(
                    created_at=current_date
                )
                
                all_contents.append((content, schedule, current_date))
                
                self.stdout.write(f'Day {day+1}: Created "{title}" in {category.name}')
            
            # Simulate reviews for existing content
            self.simulate_reviews_for_day(user, all_contents, current_date)
        
        self.stdout.write(f'Created {len(all_contents)} contents over 40 days')

    def simulate_reviews_for_day(self, user, all_contents, current_date):
        """Simulate reviews for a specific day"""
        intervals = get_review_intervals(user)
        
        for content, schedule, created_date in all_contents:
            # Only process content created before current date
            if created_date >= current_date:
                continue
            
            # Check if review is due
            if schedule.next_review_date and schedule.next_review_date.date() <= current_date.date():
                # Simulate review with realistic results
                # Better performance for older content
                days_since_creation = (current_date - created_date).days
                
                if days_since_creation < 7:
                    # New content: more likely to forget
                    result = random.choices(
                        ['remembered', 'partial', 'forgot'],
                        weights=[40, 40, 20]
                    )[0]
                elif days_since_creation < 30:
                    # Medium-term: better retention
                    result = random.choices(
                        ['remembered', 'partial', 'forgot'],
                        weights=[60, 30, 10]
                    )[0]
                else:
                    # Long-term: well remembered
                    result = random.choices(
                        ['remembered', 'partial', 'forgot'],
                        weights=[75, 20, 5]
                    )[0]
                
                # Create review history
                review_date = current_date.replace(
                    hour=random.randint(6, 23),
                    minute=random.randint(0, 59)
                )
                review_history = ReviewHistory.objects.create(
                    content=content,
                    user=user,
                    result=result,
                    time_spent=random.randint(30, 300),  # 30 seconds to 5 minutes
                    notes=self.get_review_note(result)
                )
                
                # Override review_date to specific date/time
                ReviewHistory.objects.filter(id=review_history.id).update(
                    review_date=review_date
                )
                
                # Update schedule based on result
                if result == 'remembered':
                    # Advance to next interval
                    if schedule.interval_index < len(intervals) - 1:
                        schedule.interval_index += 1
                    next_interval = intervals[min(schedule.interval_index, len(intervals) - 1)]
                elif result == 'partial':
                    # Keep same interval
                    next_interval = intervals[schedule.interval_index]
                else:  # forgot
                    # Reset to shorter interval
                    schedule.interval_index = max(0, schedule.interval_index - 1)
                    next_interval = intervals[schedule.interval_index]
                
                # Update next review date
                schedule.next_review_date = current_date + timedelta(days=next_interval)
                schedule.initial_review_completed = True
                schedule.save()

    def get_random_note(self):
        """Get a random note for content"""
        notes = [
            "중요한 개념이니 반드시 기억하자",
            "실무에서 자주 사용됨",
            "면접 질문으로 나올 수 있음",
            "프로젝트에 적용해보기",
            "더 깊이 공부 필요",
            "관련 자료 더 찾아보기",
            "예제 코드 작성해보기",
            "블로그에 정리하기",
            "팀원들과 공유하기",
            "실습 프로젝트 만들어보기"
        ]
        return random.choice(notes)

    def get_review_note(self, result):
        """Get a review note based on result"""
        if result == 'remembered':
            notes = [
                "완벽하게 기억함! 👍",
                "쉽게 떠올랐음",
                "확실히 이해한 개념",
                "잘 기억하고 있음",
                "자신있게 설명 가능"
            ]
        elif result == 'partial':
            notes = [
                "대략적으로 기억함",
                "세부사항은 헷갈림",
                "핵심은 기억하지만 디테일 부족",
                "조금 더 복습 필요",
                "일부만 기억남"
            ]
        else:  # forgot
            notes = [
                "완전히 잊어버림",
                "다시 학습 필요",
                "기억이 안 남",
                "처음 보는 것 같음",
                "복습 더 자주 해야겠음"
            ]
        return random.choice(notes)

    def display_summary(self, user):
        """Display summary of created data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('REALISTIC USER DATA SUMMARY')
        self.stdout.write('='*50)
        
        content_count = Content.objects.filter(author=user).count()
        schedule_count = ReviewSchedule.objects.filter(user=user).count()
        history_count = ReviewHistory.objects.filter(user=user).count()
        
        # Calculate review statistics
        total_reviews = ReviewHistory.objects.filter(user=user)
        remembered = total_reviews.filter(result='remembered').count()
        partial = total_reviews.filter(result='partial').count()
        forgot = total_reviews.filter(result='forgot').count()
        
        # Get content by category
        categories = Category.objects.filter(name__startswith='실전 학습')
        
        self.stdout.write(f'\n사용자: {user.username} ({user.email})')
        self.stdout.write(f'구독 티어: PRO (최대 180일 간격)')
        self.stdout.write(f'주간 목표: {user.weekly_goal}회')
        self.stdout.write(f'\n학습 통계:')
        self.stdout.write(f'  총 콘텐츠: {content_count}개')
        self.stdout.write(f'  활성 복습 스케줄: {schedule_count}개')
        self.stdout.write(f'  총 복습 횟수: {history_count}회')
        
        if history_count > 0:
            self.stdout.write(f'\n복습 성과:')
            self.stdout.write(f'  완벽히 기억: {remembered}회 ({remembered*100//history_count}%)')
            self.stdout.write(f'  부분 기억: {partial}회 ({partial*100//history_count}%)')
            self.stdout.write(f'  잊어버림: {forgot}회 ({forgot*100//history_count}%)')
        
        self.stdout.write(f'\n카테고리별 콘텐츠:')
        for category in categories:
            count = Content.objects.filter(author=user, category=category).count()
            self.stdout.write(f'  {category.name}: {count}개')
        
        # Get overdue reviews
        today = timezone.now().date()
        overdue = ReviewSchedule.objects.filter(
            user=user,
            is_active=True,
            next_review_date__date__lt=today
        ).count()
        
        due_today = ReviewSchedule.objects.filter(
            user=user,
            is_active=True,
            next_review_date__date=today
        ).count()
        
        self.stdout.write(f'\n복습 현황:')
        self.stdout.write(f'  오늘 복습: {due_today}개')
        self.stdout.write(f'  밀린 복습: {overdue}개')
        
        self.stdout.write(f'\n로그인 정보:')
        self.stdout.write(f'  이메일: realistic_learner@resee.com')
        self.stdout.write(f'  비밀번호: test123!')
        
        self.stdout.write(f'\n이 계정은 40일간 매일 학습한 실제 사용자처럼 보입니다!')