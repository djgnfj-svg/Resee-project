"""
Create a student account with 10 days of learning history
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a student account with 10 days of consistent learning history'

    def handle(self, *args, **options):
        # Create student user
        email = 'student@resee.com'
        password = 'student123!'
        
        # Delete existing user if exists
        User.objects.filter(email=email).delete()
        
        # Create new user
        user = User.objects.create_user(
            email=email,
            password=password,
            username='Student User'
        )
        user.is_active = True
        user.is_email_verified = True  # 이메일 인증 완료
        user.weekly_goal = 35  # 5 reviews per day × 7 days
        user.save()
        
        self.stdout.write(f'Created user: {email}')
        
        # Create categories
        categories = [
            ('프로그래밍', 'programming'),
            ('수학', 'math'),
            ('영어', 'english')
        ]
        
        category_objects = []
        for name, slug in categories:
            category = Category.objects.create(
                name=name,
                slug=slug,
                user=user
            )
            category_objects.append(category)
            self.stdout.write(f'Created category: {name}')
        
        # Create contents (10 per category = 30 total)
        contents = []
        content_data = {
            'programming': [
                ('Python 리스트 컴프리헨션', 'List comprehension: [x for x in range(10)]'),
                ('JavaScript 화살표 함수', 'Arrow function: const func = () => {}'),
                ('SQL JOIN 문법', 'SELECT * FROM a JOIN b ON a.id = b.id'),
                ('Git 브랜치 전략', 'git checkout -b feature/new-feature'),
                ('Docker 컨테이너 기초', 'docker run -d -p 80:80 nginx'),
                ('REST API 설계 원칙', 'GET /api/users, POST /api/users'),
                ('정규표현식 패턴', 'Pattern: /^[a-zA-Z0-9]+$/'),
                ('알고리즘: 이진 탐색', 'Binary search: O(log n) complexity'),
                ('데이터베이스 인덱싱', 'CREATE INDEX idx_name ON table(column)'),
                ('비동기 프로그래밍', 'async/await vs Promise.then()')
            ],
            'math': [
                ('미분의 기본 정리', 'd/dx(x^n) = nx^(n-1)'),
                ('적분 공식', '∫x^n dx = x^(n+1)/(n+1) + C'),
                ('피타고라스 정리', 'a² + b² = c²'),
                ('이차방정식의 해', 'x = (-b ± √(b²-4ac))/2a'),
                ('삼각함수 공식', 'sin²θ + cos²θ = 1'),
                ('로그 함수', 'log(ab) = log(a) + log(b)'),
                ('수열과 급수', 'Σ(n) = n(n+1)/2'),
                ('벡터의 내적', 'a·b = |a||b|cosθ'),
                ('행렬의 곱셈', 'AB ≠ BA (일반적으로)'),
                ('확률과 통계', 'P(A∪B) = P(A) + P(B) - P(A∩B)')
            ],
            'english': [
                ('Present Perfect Tense', 'I have lived here for 5 years'),
                ('Conditional Sentences', 'If I were you, I would...'),
                ('Phrasal Verbs', 'give up, look after, put off'),
                ('Relative Clauses', 'The book which I read yesterday'),
                ('Passive Voice', 'The letter was written by John'),
                ('Reported Speech', 'He said that he was tired'),
                ('Modal Verbs', 'can, could, may, might, should'),
                ('Gerunds vs Infinitives', 'enjoy + -ing, want + to verb'),
                ('Prepositions of Time', 'at, in, on - time expressions'),
                ('Comparative & Superlative', 'better/best, more/most')
            ]
        }
        
        for category in category_objects:
            category_contents = content_data[category.slug]
            for title, content_text in category_contents:
                content = Content.objects.create(
                    title=title,
                    content=content_text,
                    category=category,
                    author=user,
                    priority='medium'
                )
                contents.append(content)
        
        self.stdout.write(f'Created {len(contents)} contents')
        
        # Generate 30 days of review history with realistic spaced intervals
        today = timezone.now().date()
        review_intervals = [1, 3, 7, 14, 30]  # 에빙하우스 복습 간격
        
        # Track total reviews
        total_review_count = 0
        
        # For each content, create a realistic review pattern
        for i, content in enumerate(contents):
            # Start each content at different times over the past 30 days
            first_review_days_ago = random.randint(25, 30)
            current_days_ago = first_review_days_ago
            interval_index = 0
            
            # Create reviews following spaced repetition intervals
            while current_days_ago >= 0 and interval_index < len(review_intervals):
                review_date = today - timedelta(days=current_days_ago)
                review_time = timezone.now().replace(
                    year=review_date.year,
                    month=review_date.month,
                    day=review_date.day,
                    hour=random.randint(8, 22),
                    minute=random.randint(0, 59),
                    second=0,
                    microsecond=0
                )
                
                # Generate review result with realistic distribution
                result_weights = {
                    'remembered': 0.85,  # 85% success rate
                    'partial': 0.12,     # 12% partial
                    'forgot': 0.03       # 3% forgot
                }
                result = random.choices(
                    list(result_weights.keys()),
                    weights=list(result_weights.values())
                )[0]
                
                # Create review history
                ReviewHistory.objects.create(
                    content=content,
                    user=user,
                    result=result,
                    time_spent=random.randint(60, 180),  # 1-3 minutes per review
                    review_date=review_time
                )
                total_review_count += 1
                
                # Update review schedule
                schedule, created = ReviewSchedule.objects.get_or_create(
                    content=content,
                    user=user,
                    defaults={
                        'next_review_date': review_time + timedelta(days=1),
                        'interval_index': 0,
                        'is_active': True,
                        'initial_review_completed': True
                    }
                )
                
                # Move to next interval if remembered, reset if forgot
                if result == 'remembered':
                    interval_index += 1
                    if interval_index < len(review_intervals):
                        current_days_ago -= review_intervals[interval_index - 1]
                    else:
                        # Continue with 30-day intervals
                        current_days_ago -= 30
                        
                    # Update schedule interval
                    if not created:
                        schedule.interval_index = min(interval_index, len(review_intervals) - 1)
                        schedule.next_review_date = today + timedelta(days=review_intervals[min(interval_index, len(review_intervals) - 1)])
                        schedule.save()
                elif result == 'forgot':
                    # Reset to beginning
                    interval_index = 0
                    current_days_ago -= 1  # Review again next day
                    
                    if not created:
                        schedule.interval_index = 0
                        schedule.next_review_date = today + timedelta(days=1)
                        schedule.save()
                else:  # partial
                    # Stay at same interval
                    current_days_ago -= review_intervals[interval_index] if interval_index < len(review_intervals) else 30
        
        # Summary statistics
        total_reviews = ReviewHistory.objects.filter(user=user).count()
        remembered_count = ReviewHistory.objects.filter(user=user, result='remembered').count()
        success_rate = (remembered_count / total_reviews * 100) if total_reviews > 0 else 0
        
        # Calculate unique review days
        review_dates = ReviewHistory.objects.filter(user=user).values_list('review_date__date', flat=True).distinct()
        unique_days = len(set(review_dates))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully created student account:\n'
            f'Email: {email}\n'
            f'Password: {password}\n'
            f'Total contents: {len(contents)}\n'
            f'Total reviews: {total_reviews}\n'
            f'Success rate: {success_rate:.1f}%\n'
            f'Study days: {unique_days} days over the past month\n'
            f'Average reviews per content: {total_reviews / len(contents):.1f}'
        ))