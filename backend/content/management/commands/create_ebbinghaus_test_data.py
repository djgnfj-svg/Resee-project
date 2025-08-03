"""
Management command to create test data for Ebbinghaus forgetting curve review system
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

from accounts.models import SubscriptionTier, Subscription
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory
from review.utils import get_review_intervals

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for Ebbinghaus-optimized review system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new data'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing test data...')
            self.clear_test_data()

        self.stdout.write('Creating Ebbinghaus test data...')
        
        # Create test users for each subscription tier
        users = self.create_test_users()
        
        # Create categories
        categories = self.create_categories()
        
        # Create content for each user
        for user in users:
            self.create_content_for_user(user, categories)
            
        # Create review schedules with different intervals
        for user in users:
            self.create_review_schedules_for_user(user)
            
        # Create some review history
        for user in users:
            self.create_review_history_for_user(user)
            
        # Display summary
        self.display_summary(users)

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created Ebbinghaus test data!'
            )
        )

    def clear_test_data(self):
        """Clear existing test data"""
        # Delete test users (will cascade delete related data)
        test_emails = [
            'ebbinghaus_free@resee.com',
            'ebbinghaus_basic@resee.com', 
            'ebbinghaus_premium@resee.com',
            'ebbinghaus_pro@resee.com'
        ]
        
        User.objects.filter(email__in=test_emails).delete()
        
        # Clean up any orphaned data
        Category.objects.filter(name__startswith='Ebbinghaus Test').delete()

    def create_test_users(self):
        """Create test users for each subscription tier"""
        users = []
        
        tiers = [
            (SubscriptionTier.FREE, 'ebbinghaus_free@resee.com', 'Free Tier User'),
            (SubscriptionTier.BASIC, 'ebbinghaus_basic@resee.com', 'Basic Tier User'),
            (SubscriptionTier.PREMIUM, 'ebbinghaus_premium@resee.com', 'Premium Tier User'),
            (SubscriptionTier.PRO, 'ebbinghaus_pro@resee.com', 'Pro Tier User'),
        ]
        
        for tier, email, username in tiers:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'is_email_verified': True,
                    'weekly_goal': 20
                }
            )
            
            if created:
                user.set_password('test123!')
                user.save()
            
            # Set subscription tier
            user.subscription.tier = tier
            user.subscription.is_active = True
            user.subscription.start_date = timezone.now() - timedelta(days=30)
            user.subscription.end_date = timezone.now() + timedelta(days=30)
            user.subscription.save()
            
            users.append(user)
            
            self.stdout.write(
                f'Created user: {username} with {tier} tier '
                f'(max interval: {user.subscription.max_interval_days} days)'
            )
        
        return users

    def create_categories(self):
        """Create test categories"""
        categories = []
        
        category_names = [
            'Ebbinghaus Test - 프로그래밍',
            'Ebbinghaus Test - 언어학습', 
            'Ebbinghaus Test - 과학',
            'Ebbinghaus Test - 수학'
        ]
        
        for name in category_names:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-')}
            )
            categories.append(category)
            
            if created:
                self.stdout.write(f'Created category: {name}')
        
        return categories

    def create_content_for_user(self, user, categories):
        """Create content for a user"""
        tier_content_counts = {
            SubscriptionTier.FREE: 5,
            SubscriptionTier.BASIC: 10,
            SubscriptionTier.PREMIUM: 15,
            SubscriptionTier.PRO: 20
        }
        
        content_count = tier_content_counts.get(user.subscription.tier, 5)
        
        content_templates = [
            ('Python 기초', 'Python 프로그래밍의 기본 문법과 개념을 학습합니다.'),
            ('JavaScript ES6', 'ES6의 새로운 기능들을 알아봅시다.'),
            ('React Hooks', 'React Hooks의 사용법과 패턴을 익힙니다.'),
            ('Django ORM', 'Django ORM을 활용한 데이터베이스 조작 방법입니다.'),
            ('영어 문법', '영어 기본 문법 규칙들을 정리했습니다.'),
            ('물리학 공식', '고등학교 물리학 주요 공식들입니다.'),
            ('미적분 개념', '미적분의 기본 개념과 응용을 다룹니다.'),
            ('화학 반응', '화학 반응의 종류와 특징을 학습합니다.'),
        ]
        
        for i in range(content_count):
            template = content_templates[i % len(content_templates)]
            category = random.choice(categories)
            
            title = f"{template[0]} - {user.subscription.tier} #{i+1}"
            content_text = f"{template[1]}\n\n구독 티어: {user.subscription.tier}\n최대 복습 간격: {user.subscription.max_interval_days}일"
            
            content = Content.objects.create(
                title=title,
                content=content_text,
                author=user,
                category=category
            )
            
            self.stdout.write(f'Created content: {title} for {user.email}')

    def create_review_schedules_for_user(self, user):
        """Create review schedules at different intervals for a user"""
        user_contents = Content.objects.filter(author=user)
        intervals = get_review_intervals(user)
        
        for i, content in enumerate(user_contents):
            # Distribute content across different interval stages
            interval_index = i % len(intervals)
            current_interval = intervals[interval_index]
            
            # Some content due today, some in the future, some overdue
            days_offset = random.choice([-2, -1, 0, 1, 2])  # Mix of overdue and future
            next_review_date = timezone.now() + timedelta(days=days_offset)
            
            # Mark some as initial review completed
            initial_completed = random.choice([True, False])
            if not initial_completed:
                # New content should be available immediately
                next_review_date = timezone.now() - timedelta(hours=1)
                interval_index = 0
            
            schedule, created = ReviewSchedule.objects.get_or_create(
                content=content,
                user=user,
                defaults={
                    'next_review_date': next_review_date,
                    'interval_index': interval_index,
                    'initial_review_completed': initial_completed,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    f'Created schedule for {content.title}: '
                    f'interval_index={interval_index} ({current_interval} days), '
                    f'next_review={next_review_date.strftime("%Y-%m-%d")}, '
                    f'initial_completed={initial_completed}'
                )

    def create_review_history_for_user(self, user):
        """Create some review history for a user"""
        user_contents = Content.objects.filter(author=user)
        results = ['remembered', 'partial', 'forgot']
        
        # Create history for about half of the content
        for content in user_contents[:len(user_contents)//2]:
            # Create 1-3 history entries per content
            history_count = random.randint(1, 3)
            
            for i in range(history_count):
                # History from last 30 days
                days_ago = random.randint(1, 30)
                review_date = timezone.now() - timedelta(days=days_ago)
                
                result = random.choice(results)
                time_spent = random.randint(60, 300)  # 1-5 minutes
                
                ReviewHistory.objects.create(
                    content=content,
                    user=user,
                    review_date=review_date,
                    result=result,
                    time_spent=time_spent,
                    notes=f'Test review - {result}'
                )
        
        history_count = ReviewHistory.objects.filter(user=user).count()
        self.stdout.write(f'Created {history_count} review history entries for {user.email}')

    def display_summary(self, users):
        """Display summary of created data"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('EBBINGHAUS TEST DATA SUMMARY')
        self.stdout.write('='*50)
        
        for user in users:
            intervals = get_review_intervals(user)
            content_count = Content.objects.filter(author=user).count()
            schedule_count = ReviewSchedule.objects.filter(user=user).count()
            history_count = ReviewHistory.objects.filter(user=user).count()
            today_reviews = ReviewSchedule.objects.filter(
                user=user,
                is_active=True,
                next_review_date__date__lte=timezone.now().date()
            ).count()
            
            self.stdout.write(f'\n{user.username} ({user.email}):')
            self.stdout.write(f'  Tier: {user.subscription.tier}')
            self.stdout.write(f'  Max interval: {user.subscription.max_interval_days} days')
            self.stdout.write(f'  Available intervals: {intervals}')
            self.stdout.write(f'  Content created: {content_count}')
            self.stdout.write(f'  Review schedules: {schedule_count}')
            self.stdout.write(f'  Review history: {history_count}')
            self.stdout.write(f'  Due today: {today_reviews}')
        
        self.stdout.write(f'\nTest login credentials:')
        self.stdout.write(f'Password for all test users: test123!')
        self.stdout.write(f'\nTest these APIs:')
        self.stdout.write(f'- GET /api/review/today/ (with each user)')
        self.stdout.write(f'- POST /api/review/complete/ (complete a review)')
        self.stdout.write(f'- GET /api/accounts/subscription/ (check intervals)')
        self.stdout.write(f'- POST /api/accounts/subscription/upgrade/ (test tier changes)')