"""
Management command to create long-term test data simulating 180 days of daily activity
for PRO subscription tier testing with subscription tier limitations
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
    help = 'Create long-term test data simulating 180 days of daily learning activity with subscription testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing long-term test data before creating new data'
        )
        
        parser.add_argument(
            '--tier',
            type=str,
            choices=['free', 'basic', 'premium', 'pro', 'all'],
            default='pro',
            help='Subscription tier to create test data for'
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing long-term test data...')
            self.clear_long_term_data()

        tier = options['tier']
        
        if tier == 'all':
            # Create test accounts for all tiers
            self.stdout.write('Creating long-term test data for all subscription tiers...')
            for tier_choice in [SubscriptionTier.FREE, SubscriptionTier.BASIC, SubscriptionTier.PREMIUM, SubscriptionTier.PRO]:
                self.create_tier_test_data(tier_choice)
        else:
            # Create test account for specific tier
            tier_map = {
                'free': SubscriptionTier.FREE,
                'basic': SubscriptionTier.BASIC,
                'premium': SubscriptionTier.PREMIUM,
                'pro': SubscriptionTier.PRO
            }
            self.stdout.write(f'Creating long-term test data for {tier.upper()} tier...')
            self.create_tier_test_data(tier_map[tier])

        self.stdout.write(
            self.style.SUCCESS(
                'Successfully created long-term test data!'
            )
        )

    def clear_long_term_data(self):
        """Clear existing long-term test data"""
        # Delete users with specific pattern
        test_emails = [
            'longterm_free@resee.com',
            'longterm_basic@resee.com', 
            'longterm_premium@resee.com',
            'longterm_pro@resee.com'
        ]
        
        for email in test_emails:
            user = User.objects.filter(email=email).first()
            if user:
                # Delete all content and related data (cascades)
                Content.objects.filter(author=user).delete()
                ReviewSchedule.objects.filter(user=user).delete()
                ReviewHistory.objects.filter(user=user).delete()
                user.delete()
                self.stdout.write(f'Deleted user: {email}')
        
        # Clean up categories
        Category.objects.filter(name__startswith='장기 테스트').delete()

    def create_tier_test_data(self, subscription_tier):
        """Create test data for a specific subscription tier"""
        
        # Create user
        user = self.create_tier_user(subscription_tier)
        
        # Create categories
        categories = self.create_test_categories()
        
        # Simulate 180 days of learning
        self.simulate_180_days_learning(user, categories, subscription_tier)
        
        # Display summary
        self.display_tier_summary(user, subscription_tier)
        
        return user

    def create_tier_user(self, subscription_tier):
        """Create a user with specific subscription tier"""
        tier_info = {
            SubscriptionTier.FREE: {
                'email': 'longterm_free@resee.com',
                'username': '장기 테스트 FREE 사용자',
                'weekly_goal': 7
            },
            SubscriptionTier.BASIC: {
                'email': 'longterm_basic@resee.com',
                'username': '장기 테스트 BASIC 사용자',
                'weekly_goal': 14
            },
            SubscriptionTier.PREMIUM: {
                'email': 'longterm_premium@resee.com',
                'username': '장기 테스트 PREMIUM 사용자',
                'weekly_goal': 21
            },
            SubscriptionTier.PRO: {
                'email': 'longterm_pro@resee.com',
                'username': '장기 테스트 PRO 사용자',
                'weekly_goal': 35
            }
        }
        
        info = tier_info[subscription_tier]
        
        user, created = User.objects.get_or_create(
            email=info['email'],
            defaults={
                'username': info['username'],
                'is_email_verified': True,
                'weekly_goal': info['weekly_goal']
            }
        )
        
        if created:
            user.set_password('test123!')
            user.save()
        
        # Set subscription tier
        user.subscription.tier = subscription_tier
        user.subscription.is_active = True
        user.subscription.start_date = timezone.now() - timedelta(days=190)  # Started before test period
        user.subscription.end_date = timezone.now() + timedelta(days=365)    # Valid for next year
        user.subscription.save()
        
        tier_max_intervals = {
            SubscriptionTier.FREE: 7,
            SubscriptionTier.BASIC: 30,
            SubscriptionTier.PREMIUM: 60,
            SubscriptionTier.PRO: 180,
        }
        
        self.stdout.write(
            f'Created user: {user.username} ({subscription_tier}) '
            f'with max interval: {tier_max_intervals[subscription_tier]} days'
        )
        
        return user

    def create_test_categories(self):
        """Create test categories"""
        categories = []
        
        category_data = [
            ('장기 테스트 - 프로그래밍', '180일 장기 프로그래밍 학습'),
            ('장기 테스트 - 언어학습', '180일 장기 언어 학습'),
            ('장기 테스트 - 전문지식', '180일 장기 전문 지식 학습'),
            ('장기 테스트 - 기술동향', '180일 장기 기술 동향 학습'),
        ]
        
        for name, description in category_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'slug': name.lower().replace(' ', '-').replace('-', '_'),
                    'description': description
                }
            )
            categories.append(category)
            
            if created:
                self.stdout.write(f'Created category: {name}')
        
        return categories

    def simulate_180_days_learning(self, user, categories, subscription_tier):
        """Simulate 180 days of learning activity with subscription-aware review progression"""
        
        # Learning content templates for long-term study
        learning_templates = {
            '장기 테스트 - 프로그래밍': [
                ('Python 고급 패턴', 'Design patterns, metaclasses, descriptors'),
                ('시스템 설계', 'Scalability, load balancing, microservices'),
                ('알고리즘 최적화', 'Time complexity, space complexity, optimization'),
                ('데이터베이스 설계', 'Normalization, indexing, query optimization'),
                ('클라우드 아키텍처', 'AWS, Docker, Kubernetes, serverless'),
            ],
            '장기 테스트 - 언어학습': [
                ('고급 문법', 'Complex grammatical structures'),
                ('비즈니스 영어', 'Professional communication skills'),
                ('기술 용어', 'Technical terminology and usage'),
                ('프레젠테이션', 'Public speaking and presentation skills'),
                ('협상 기법', 'Negotiation and persuasion techniques'),
            ],
            '장기 테스트 - 전문지식': [
                ('프로젝트 관리', 'Agile, Scrum, risk management'),
                ('리더십 스킬', 'Team management, motivation, delegation'),
                ('비즈니스 전략', 'Strategic planning, market analysis'),
                ('재무 관리', 'Budgeting, ROI, financial planning'),
                ('혁신 관리', 'Innovation processes, change management'),
            ],
            '장기 테스트 - 기술동향': [
                ('AI/ML 트렌드', 'Latest developments in artificial intelligence'),
                ('블록체인', 'Cryptocurrency, smart contracts, DeFi'),
                ('IoT 기술', 'Internet of Things applications'),
                ('사이버보안', 'Security threats, protection strategies'),
                ('신기술 동향', 'Emerging technologies and their impact'),
            ]
        }
        
        # Start date: 180 days ago
        start_date = timezone.now() - timedelta(days=180)
        
        # Track all created content for review simulation
        all_contents = []
        
        # Get subscription limits
        user_intervals = get_review_intervals(user)
        max_interval = user.get_max_review_interval()
        
        self.stdout.write(f'User {user.email} intervals: {user_intervals} (max: {max_interval} days)')
        
        # Simulate each day
        for day in range(180):
            current_date = start_date + timedelta(days=day)
            
            # Create 1 content per day consistently
            category = random.choice(categories)
            templates = learning_templates.get(category.name, [])
            if not templates:
                continue
                
            template = random.choice(templates)
            title, content_text = template
            
            # Add day-specific information
            content_text += f"\n\n📅 학습일: {current_date.strftime('%Y년 %m월 %d일')} (Day {day+1}/180)"
            content_text += f"\n🎯 구독: {user.subscription.tier} (최대 {max_interval}일 간격)"
            content_text += f"\n💡 진행: {self.get_progress_note(day)}"
            
            # Create content
            content = Content.objects.create(
                title=f"{title} (Day {day+1:03d})",
                content=content_text,
                author=user,
                category=category,
                priority=random.choice(['high', 'medium', 'low'])
            )
            
            # Override created_at
            Content.objects.filter(id=content.id).update(
                created_at=current_date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
            )
            
            # Create initial review schedule
            schedule, created = ReviewSchedule.objects.get_or_create(
                content=content,
                user=user,
                defaults={
                    'next_review_date': current_date + timedelta(days=1),  # First review next day
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
            
            if (day + 1) % 30 == 0:
                self.stdout.write(f'Day {day+1}: Created content "{title}" (Total: {len(all_contents)})')
            
            # Simulate reviews for existing content
            self.simulate_reviews_for_day(user, all_contents, current_date, subscription_tier)
        
        self.stdout.write(f'Created {len(all_contents)} contents over 180 days')

    def simulate_reviews_for_day(self, user, all_contents, current_date, subscription_tier):
        """Simulate reviews for a specific day with subscription-aware intervals"""
        intervals = get_review_intervals(user)
        max_interval = user.get_max_review_interval()
        
        reviews_today = 0
        
        for content, schedule, created_date in all_contents:
            # Only process content created before current date
            if created_date >= current_date:
                continue
            
            # Check if review is due
            if schedule.next_review_date and schedule.next_review_date.date() <= current_date.date():
                # Simulate review with realistic results based on time and subscription tier
                days_since_creation = (current_date - created_date).days
                current_interval_days = intervals[schedule.interval_index] if schedule.interval_index < len(intervals) else intervals[-1]
                
                # Better retention for premium tiers (they study more systematically)
                tier_bonus = {
                    SubscriptionTier.FREE: 0.0,
                    SubscriptionTier.BASIC: 0.1,
                    SubscriptionTier.PREMIUM: 0.2,
                    SubscriptionTier.PRO: 0.3
                }
                
                retention_bonus = tier_bonus.get(subscription_tier, 0.0)
                
                # Calculate success probability based on interval and tier
                if current_interval_days <= 7:
                    # Short intervals: higher success rate
                    base_success_rate = 0.7 + retention_bonus
                elif current_interval_days <= 30:
                    # Medium intervals
                    base_success_rate = 0.6 + retention_bonus
                else:
                    # Long intervals: test subscription tier effectiveness
                    base_success_rate = 0.5 + retention_bonus * 1.5  # PRO users should be much better at long intervals
                
                # Adjust for age of content
                if days_since_creation > 90:
                    base_success_rate += 0.1  # Well-learned content
                
                base_success_rate = min(0.95, max(0.1, base_success_rate))  # Clamp between 10% and 95%
                
                if random.random() < base_success_rate:
                    result = 'remembered'
                elif random.random() < 0.7:  # 70% of non-remembered are partial
                    result = 'partial'
                else:
                    result = 'forgot'
                
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
                    notes=self.get_review_note(result, subscription_tier, current_interval_days)
                )
                
                # Override review_date
                ReviewHistory.objects.filter(id=review_history.id).update(
                    review_date=review_date
                )
                
                # Update schedule based on result with subscription limits
                if result == 'remembered':
                    # Advance to next interval, but respect subscription limits
                    if schedule.interval_index < len(intervals) - 1:
                        next_index = schedule.interval_index + 1
                        next_interval = intervals[next_index]
                        
                        # Check subscription limit
                        if next_interval <= max_interval:
                            schedule.interval_index = next_index
                        else:
                            # Find max allowed interval for this subscription
                            allowed_intervals = [i for i in intervals if i <= max_interval]
                            if allowed_intervals:
                                max_allowed_interval = max(allowed_intervals)
                                try:
                                    schedule.interval_index = intervals.index(max_allowed_interval)
                                except ValueError:
                                    schedule.interval_index = len(allowed_intervals) - 1
                    
                elif result == 'partial':
                    # Stay at current interval
                    pass
                else:  # forgot
                    # Go back to earlier interval
                    schedule.interval_index = max(0, schedule.interval_index - 1)
                
                # Set next review date
                current_interval = intervals[schedule.interval_index]
                # Ensure we don't exceed subscription limit
                if current_interval > max_interval:
                    current_interval = max_interval
                
                schedule.next_review_date = current_date + timedelta(days=current_interval)
                schedule.initial_review_completed = True
                schedule.save()
                
                reviews_today += 1
        
        # Occasionally log review activity
        if reviews_today > 0 and current_date.day % 10 == 0:
            self.stdout.write(f'Day {(current_date - (timezone.now() - timedelta(days=180))).days + 1}: {reviews_today} reviews completed')

    def get_progress_note(self, day):
        """Get progress note based on day"""
        if day < 30:
            return "초기 학습 단계"
        elif day < 90:
            return "기초 정착 단계"
        elif day < 150:
            return "심화 학습 단계"
        else:
            return "마스터리 단계"

    def get_review_note(self, result, subscription_tier, interval_days):
        """Get review note based on result and context"""
        tier_names = {
            SubscriptionTier.FREE: 'FREE',
            SubscriptionTier.BASIC: 'BASIC',
            SubscriptionTier.PREMIUM: 'PREMIUM',
            SubscriptionTier.PRO: 'PRO'
        }
        
        tier_name = tier_names.get(subscription_tier, 'UNKNOWN')
        
        if result == 'remembered':
            notes = [
                f"완벽 기억! ({tier_name}, {interval_days}일 간격)",
                f"쉽게 떠올림 ({tier_name})",
                f"확실히 이해함 ({interval_days}일 후에도)",
                f"잘 정착된 지식 ({tier_name} 효과)"
            ]
        elif result == 'partial':
            notes = [
                f"대략 기억 ({tier_name}, {interval_days}일 간격)",
                f"핵심은 기억하지만 세부사항 애매 ({tier_name})",
                f"조금 더 복습 필요 ({interval_days}일 간격)",
                f"부분적 이해 ({tier_name})"
            ]
        else:  # forgot
            notes = [
                f"완전히 잊음 ({tier_name}, {interval_days}일 간격)",
                f"다시 학습 필요 ({tier_name})",
                f"간격이 너무 길었나? ({interval_days}일)",
                f"복습 주기 조정 필요 ({tier_name})"
            ]
        return random.choice(notes)

    def display_tier_summary(self, user, subscription_tier):
        """Display summary for a specific tier"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(f'LONG-TERM TEST DATA SUMMARY - {subscription_tier.upper()}')
        self.stdout.write('='*60)
        
        content_count = Content.objects.filter(author=user).count()
        schedule_count = ReviewSchedule.objects.filter(user=user).count()
        history_count = ReviewHistory.objects.filter(user=user).count()
        
        # Calculate review statistics
        total_reviews = ReviewHistory.objects.filter(user=user)
        remembered = total_reviews.filter(result='remembered').count()
        partial = total_reviews.filter(result='partial').count()
        forgot = total_reviews.filter(result='forgot').count()
        
        # Get max interval reached
        max_reached_schedule = ReviewSchedule.objects.filter(user=user).order_by('-interval_index').first()
        intervals = get_review_intervals(user)
        max_interval_reached = intervals[max_reached_schedule.interval_index] if max_reached_schedule else 0
        
        # Get content by category
        categories = Category.objects.filter(name__startswith='장기 테스트')
        
        self.stdout.write(f'\n사용자: {user.username} ({user.email})')
        self.stdout.write(f'구독 티어: {subscription_tier} (최대 {user.get_max_review_interval()}일 간격)')
        self.stdout.write(f'주간 목표: {user.weekly_goal}회')
        self.stdout.write(f'테스트 기간: 180일')
        
        self.stdout.write(f'\n학습 통계:')
        self.stdout.write(f'  총 콘텐츠: {content_count}개 (매일 1개씩 180일)')
        self.stdout.write(f'  활성 복습 스케줄: {schedule_count}개')
        self.stdout.write(f'  총 복습 횟수: {history_count}회')
        self.stdout.write(f'  최대 도달 간격: {max_interval_reached}일')
        
        if history_count > 0:
            self.stdout.write(f'\n복습 성과:')
            self.stdout.write(f'  완벽히 기억: {remembered}회 ({remembered*100//history_count}%)')
            self.stdout.write(f'  부분 기억: {partial}회 ({partial*100//history_count}%)')
            self.stdout.write(f'  잊어버림: {forgot}회 ({forgot*100//history_count}%)')
        
        self.stdout.write(f'\n카테고리별 콘텐츠:')
        for category in categories:
            count = Content.objects.filter(author=user, category=category).count()
            if count > 0:
                self.stdout.write(f'  {category.name}: {count}개')
        
        # Get current due reviews
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
        
        # Check for long-interval schedules
        long_interval_schedules = ReviewSchedule.objects.filter(
            user=user,
            is_active=True,
            interval_index__gte=len(intervals)-2  # Last 2 intervals
        ).count()
        
        self.stdout.write(f'\n복습 현황:')
        self.stdout.write(f'  오늘 복습: {due_today}개')
        self.stdout.write(f'  밀린 복습: {overdue}개')
        self.stdout.write(f'  장기 간격 스케줄: {long_interval_schedules}개')
        
        self.stdout.write(f'\n구독 효과 테스트:')
        max_allowed = user.get_max_review_interval()
        max_reached = max_interval_reached
        if max_reached >= max_allowed:
            self.stdout.write(f'  ✅ 최대 간격 도달: {max_reached}일 (한도: {max_allowed}일)')
        else:
            self.stdout.write(f'  ⚠️  최대 간격 미달: {max_reached}일 (한도: {max_allowed}일)')
        
        # Count schedules at max interval
        max_interval_schedules = 0
        if max_allowed in intervals:
            max_index = intervals.index(max_allowed)
            max_interval_schedules = ReviewSchedule.objects.filter(
                user=user,
                is_active=True,
                interval_index=max_index
            ).count()
        
        self.stdout.write(f'  최대 간격 스케줄 수: {max_interval_schedules}개')
        
        self.stdout.write(f'\n로그인 정보:')
        self.stdout.write(f'  이메일: {user.email}')
        self.stdout.write(f'  비밀번호: test123!')
        
        tier_descriptions = {
            SubscriptionTier.FREE: "7일 최대 간격으로 기본 복습",
            SubscriptionTier.BASIC: "30일 최대 간격으로 중기 기억",
            SubscriptionTier.PREMIUM: "60일 최대 간격으로 장기 기억",
            SubscriptionTier.PRO: "180일 최대 간격으로 완전한 장기 기억"
        }
        
        self.stdout.write(f'\n이 계정은 {tier_descriptions[subscription_tier]}을 테스트할 수 있습니다!')