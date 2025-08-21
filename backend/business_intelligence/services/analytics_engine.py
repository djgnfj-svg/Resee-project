"""
Advanced analytics engine for business intelligence
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from decimal import Decimal

from django.db.models import (
    Avg, Count, Sum, Max, Min, F, Q, Case, When, 
    FloatField, IntegerField, Value
)
from django.db.models.functions import TruncDate, TruncHour, Coalesce
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import Subscription
from content.models import Content, Category
from review.models import ReviewHistory, ReviewSchedule
from ai_review.models import AIUsageTracking
from monitoring.models import UserActivity, APIMetrics

logger = logging.getLogger(__name__)
User = get_user_model()


class LearningAnalyticsEngine:
    """Engine for learning pattern analysis"""
    
    def __init__(self, user):
        self.user = user
    
    def get_learning_insights(self, days: int = 30) -> Dict:
        """Get comprehensive learning insights for a user"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get review history data
        reviews = ReviewHistory.objects.filter(
            user=self.user,
            review_date__date__gte=start_date,
            review_date__date__lte=end_date
        ).select_related('content', 'content__category')
        
        if not reviews.exists():
            return self._empty_insights()
        
        # Calculate basic metrics
        total_reviews = reviews.count()
        successful_reviews = reviews.filter(result='remembered').count()
        success_rate = (successful_reviews / total_reviews) * 100 if total_reviews > 0 else 0
        
        # Learning streak analysis
        current_streak, longest_streak = self._calculate_streaks(reviews)
        
        # Time analysis
        hourly_distribution = self._analyze_study_times(reviews)
        most_productive_hour = max(hourly_distribution, key=hourly_distribution.get) if hourly_distribution else 12
        
        # Study time calculation
        total_study_time = reviews.aggregate(
            total_time=Coalesce(Sum('time_spent'), Value(0))
        )['total_time'] or 0
        total_study_hours = total_study_time / 3600 if total_study_time else 0
        
        # Learning consistency
        learning_days = reviews.values('review_date__date').distinct().count()
        consistency_score = (learning_days / days) * 100 if days > 0 else 0
        
        # Average daily reviews
        avg_daily_reviews = total_reviews / learning_days if learning_days > 0 else 0
        
        return {
            'total_learning_days': learning_days,
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'average_daily_reviews': round(avg_daily_reviews, 2),
            'average_success_rate': round(success_rate, 2),
            'most_productive_hour': most_productive_hour,
            'total_study_hours': round(total_study_hours, 2),
            'learning_consistency_score': round(consistency_score, 2),
        }
    
    def get_content_analytics(self) -> Dict:
        """Analyze content effectiveness and patterns"""
        user_content = Content.objects.filter(user=self.user).prefetch_related('reviews')
        
        if not user_content.exists():
            return self._empty_content_analytics()
        
        total_content = user_content.count()
        
        # Categorize content by performance
        mastered_content = 0
        struggling_content = 0
        abandoned_content = 0
        mastery_times = []
        
        category_performance = defaultdict(lambda: {'total': 0, 'success_rate': 0, 'reviews': 0})
        content_type_performance = defaultdict(lambda: {'total': 0, 'success_rate': 0})
        
        for content in user_content:
            reviews = content.reviews.filter(user=self.user).order_by('review_date')
            
            if not reviews.exists():
                abandoned_content += 1
                continue
            
            # Calculate content metrics
            total_reviews = reviews.count()
            successful_reviews = reviews.filter(result='remembered').count()
            success_rate = (successful_reviews / total_reviews) * 100 if total_reviews > 0 else 0
            
            # Determine content status
            recent_reviews = reviews.order_by('-review_date')[:3]
            recent_success_count = recent_reviews.filter(result='remembered').count()
            
            if recent_success_count >= 3:
                mastered_content += 1
                # Calculate mastery time
                first_review = reviews.first()
                last_successful = reviews.filter(result='remembered').last()
                if first_review and last_successful:
                    mastery_time = (last_successful.review_date.date() - first_review.review_date.date()).days
                    mastery_times.append(mastery_time)
            elif success_rate < 50 and total_reviews >= 3:
                struggling_content += 1
            
            # Category performance
            if content.category:
                cat_data = category_performance[content.category.name]
                cat_data['total'] += 1
                cat_data['reviews'] += total_reviews
                cat_data['success_rate'] = (cat_data['success_rate'] + success_rate) / 2 if cat_data['total'] > 1 else success_rate
            
            # Content type performance
            type_data = content_type_performance[content.content_type]
            type_data['total'] += 1
            type_data['success_rate'] = (type_data['success_rate'] + success_rate) / 2 if type_data['total'] > 1 else success_rate
        
        # Find most/least effective content types
        most_effective_type = max(content_type_performance.items(), 
                                key=lambda x: x[1]['success_rate'], 
                                default=('N/A', {'success_rate': 0}))[0]
        least_effective_type = min(content_type_performance.items(), 
                                 key=lambda x: x[1]['success_rate'], 
                                 default=('N/A', {'success_rate': 0}))[0]
        
        # Average mastery time
        avg_mastery_time = sum(mastery_times) / len(mastery_times) if mastery_times else 0
        
        return {
            'total_content': total_content,
            'mastered_content': mastered_content,
            'struggling_content': struggling_content,
            'abandoned_content': abandoned_content,
            'average_mastery_time_days': round(avg_mastery_time, 1),
            'most_effective_content_type': most_effective_type,
            'least_effective_content_type': least_effective_type,
            'category_performance': dict(category_performance),
        }
    
    def get_performance_trends(self, days: int = 30) -> List[Dict]:
        """Get daily performance trends"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trends = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            daily_reviews = ReviewHistory.objects.filter(
                user=self.user,
                review_date__date=current_date
            )
            
            if daily_reviews.exists():
                total_reviews = daily_reviews.count()
                successful_reviews = daily_reviews.filter(result='remembered').count()
                success_rate = (successful_reviews / total_reviews) * 100 if total_reviews > 0 else 0
                
                # Calculate study time
                study_time = daily_reviews.aggregate(
                    total_time=Coalesce(Sum('time_spent'), Value(0))
                )['total_time'] or 0
                study_time_minutes = study_time / 60 if study_time else 0
                
                # Calculate difficulty trend (average content difficulty)
                difficulty_trend = daily_reviews.aggregate(
                    avg_difficulty=Coalesce(Avg('content__difficulty_level'), Value(3.0))
                )['avg_difficulty'] or 3.0
                
                # Simple engagement score based on reviews and time
                engagement_score = min(100, (total_reviews * 10) + (study_time_minutes / 10))
                
                trends.append({
                    'date': current_date,
                    'success_rate': round(success_rate, 2),
                    'reviews_completed': total_reviews,
                    'study_time_minutes': int(study_time_minutes),
                    'difficulty_trend': round(difficulty_trend, 2),
                    'engagement_score': round(engagement_score, 2),
                })
            else:
                trends.append({
                    'date': current_date,
                    'success_rate': 0,
                    'reviews_completed': 0,
                    'study_time_minutes': 0,
                    'difficulty_trend': 3.0,
                    'engagement_score': 0,
                })
        
        return trends
    
    def _calculate_streaks(self, reviews) -> Tuple[int, int]:
        """Calculate current and longest learning streaks"""
        dates = reviews.values_list('review_date__date', flat=True).distinct().order_by('-review_date__date')
        
        if not dates:
            return 0, 0
        
        dates_list = list(dates)
        current_streak = 0
        longest_streak = 0
        temp_streak = 1
        
        # Calculate current streak
        today = timezone.now().date()
        if dates_list and dates_list[0] >= today - timedelta(days=1):
            current_streak = 1
            for i in range(1, len(dates_list)):
                if dates_list[i-1] - dates_list[i] == timedelta(days=1):
                    current_streak += 1
                else:
                    break
        
        # Calculate longest streak
        for i in range(1, len(dates_list)):
            if dates_list[i-1] - dates_list[i] == timedelta(days=1):
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1
        
        longest_streak = max(longest_streak, temp_streak)
        
        return current_streak, longest_streak
    
    def _analyze_study_times(self, reviews) -> Dict[int, int]:
        """Analyze hourly study patterns"""
        hourly_data = reviews.extra(
            select={'hour': "EXTRACT(hour FROM review_date)"}
        ).values('hour').annotate(count=Count('id'))
        
        return {int(item['hour']): item['count'] for item in hourly_data}
    
    def _empty_insights(self) -> Dict:
        """Return empty insights structure"""
        return {
            'total_learning_days': 0,
            'current_streak': 0,
            'longest_streak': 0,
            'average_daily_reviews': 0.0,
            'average_success_rate': 0.0,
            'most_productive_hour': 12,
            'total_study_hours': 0.0,
            'learning_consistency_score': 0.0,
        }
    
    def _empty_content_analytics(self) -> Dict:
        """Return empty content analytics structure"""
        return {
            'total_content': 0,
            'mastered_content': 0,
            'struggling_content': 0,
            'abandoned_content': 0,
            'average_mastery_time_days': 0.0,
            'most_effective_content_type': 'N/A',
            'least_effective_content_type': 'N/A',
            'category_performance': {},
        }


class BusinessMetricsEngine:
    """Engine for business-wide analytics"""
    
    def get_business_dashboard(self, days: int = 30) -> Dict:
        """Get comprehensive business metrics"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # User metrics
        total_users = User.objects.count()
        active_users_today = User.objects.filter(
            last_login__date=timezone.now().date()
        ).count()
        new_users_this_month = User.objects.filter(
            date_joined__gte=timezone.now().replace(day=1)
        ).count()
        
        # Revenue metrics
        monthly_revenue = Subscription.objects.filter(
            created_at__gte=timezone.now().replace(day=1),
            is_active=True
        ).aggregate(
            total=Coalesce(Sum('amount_paid'), Value(Decimal('0.00')))
        )['total'] or Decimal('0.00')
        
        # Engagement metrics
        avg_session_duration = self._calculate_average_session_duration(days)
        daily_active_users_trend = self._get_daily_active_users_trend(days)
        retention_rate = self._calculate_user_retention(days)
        
        # Content metrics
        total_content = Content.objects.count()
        avg_reviews_per_user = ReviewHistory.objects.aggregate(
            avg=Coalesce(Count('id') / Count('user', distinct=True), Value(0.0))
        )['avg'] or 0.0
        
        # Content completion rate
        users_with_content = User.objects.filter(contents__isnull=False).distinct().count()
        users_with_reviews = User.objects.filter(review_history__isnull=False).distinct().count()
        completion_rate = (users_with_reviews / users_with_content * 100) if users_with_content > 0 else 0
        
        # Subscription metrics
        subscription_stats = self._get_subscription_metrics()
        
        # AI usage metrics
        ai_metrics = self._get_ai_usage_metrics(days)
        
        # Performance metrics
        performance_metrics = self._get_performance_metrics(days)
        
        return {
            'total_users': total_users,
            'active_users_today': active_users_today,
            'new_users_this_month': new_users_this_month,
            'monthly_revenue': monthly_revenue,
            'average_session_duration': avg_session_duration,
            'daily_active_users_trend': daily_active_users_trend,
            'user_retention_rate': retention_rate,
            'total_content_created': total_content,
            'average_reviews_per_user': round(avg_reviews_per_user, 2),
            'content_completion_rate': round(completion_rate, 2),
            **subscription_stats,
            **ai_metrics,
            **performance_metrics,
        }
    
    def _calculate_average_session_duration(self, days: int) -> float:
        """Calculate average session duration in minutes"""
        # This would ideally use session tracking data
        # For now, estimate based on review patterns
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Estimate session duration from review time patterns
        avg_time = ReviewHistory.objects.filter(
            review_date__gte=start_date
        ).aggregate(
            avg_time=Coalesce(Avg('time_spent'), Value(0))
        )['avg_time'] or 0
        
        return round(avg_time / 60, 2) if avg_time else 0  # Convert to minutes
    
    def _get_daily_active_users_trend(self, days: int) -> List[int]:
        """Get daily active users for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            active_count = User.objects.filter(
                last_login__date=date
            ).count()
            trend.append(active_count)
        
        return trend
    
    def _calculate_user_retention(self, days: int) -> float:
        """Calculate user retention rate"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Users who joined more than X days ago
        older_users = User.objects.filter(date_joined__lt=cutoff_date).count()
        
        # Of those, how many are still active
        retained_users = User.objects.filter(
            date_joined__lt=cutoff_date,
            last_login__gte=cutoff_date
        ).count()
        
        return (retained_users / older_users * 100) if older_users > 0 else 0
    
    def _get_subscription_metrics(self) -> Dict:
        """Get subscription-related metrics"""
        # Tier distribution
        tier_counts = Subscription.objects.filter(is_active=True).values('tier').annotate(
            count=Count('id')
        )
        tier_distribution = {item['tier']: item['count'] for item in tier_counts}
        
        # Conversion rate (users with subscription vs total users)
        total_users = User.objects.count()
        subscribed_users = User.objects.filter(subscription__is_active=True).count()
        conversion_rate = (subscribed_users / total_users * 100) if total_users > 0 else 0
        
        # Churn rate (cancelled subscriptions in last month)
        month_start = timezone.now().replace(day=1)
        churned_subscriptions = Subscription.objects.filter(
            is_active=False,
            updated_at__gte=month_start
        ).count()
        active_subscriptions = Subscription.objects.filter(is_active=True).count()
        churn_rate = (churned_subscriptions / (active_subscriptions + churned_subscriptions) * 100) if (active_subscriptions + churned_subscriptions) > 0 else 0
        
        # Average revenue per user
        total_revenue = Subscription.objects.filter(is_active=True).aggregate(
            total=Coalesce(Sum('amount_paid'), Value(Decimal('0.00')))
        )['total'] or Decimal('0.00')
        arpu = float(total_revenue) / subscribed_users if subscribed_users > 0 else 0
        
        return {
            'conversion_rate': round(conversion_rate, 2),
            'churn_rate': round(churn_rate, 2),
            'average_revenue_per_user': round(arpu, 2),
            'tier_distribution': tier_distribution,
        }
    
    def _get_ai_usage_metrics(self, days: int) -> Dict:
        """Get AI usage and cost metrics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # AI adoption rate
        total_users = User.objects.count()
        users_with_ai = User.objects.filter(ai_usage_tracking__isnull=False).distinct().count()
        adoption_rate = (users_with_ai / total_users * 100) if total_users > 0 else 0
        
        # AI cost efficiency
        ai_usage = AIUsageTracking.objects.filter(
            usage_date__gte=start_date.date()
        ).aggregate(
            total_cost=Coalesce(Sum('cost_usd'), Value(Decimal('0.00'))),
            total_questions=Coalesce(Sum('questions_generated'), Value(0))
        )
        
        cost_efficiency = float(ai_usage['total_cost']) / ai_usage['total_questions'] if ai_usage['total_questions'] > 0 else 0
        questions_per_user = ai_usage['total_questions'] / users_with_ai if users_with_ai > 0 else 0
        
        return {
            'ai_adoption_rate': round(adoption_rate, 2),
            'ai_cost_efficiency': round(cost_efficiency, 4),
            'ai_questions_per_user': round(questions_per_user, 2),
        }
    
    def _get_performance_metrics(self, days: int) -> Dict:
        """Get system performance metrics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # API performance
        api_metrics = APIMetrics.objects.filter(
            timestamp__gte=start_date
        ).aggregate(
            avg_response_time=Coalesce(Avg('response_time_ms'), Value(0)),
            error_count=Count('id', filter=Q(status_code__gte=400)),
            total_requests=Count('id')
        )
        
        avg_response_time = int(api_metrics['avg_response_time'] or 0)
        error_rate = (api_metrics['error_count'] / api_metrics['total_requests'] * 100) if api_metrics['total_requests'] > 0 else 0
        
        # System uptime (simplified calculation)
        uptime = 100.0  # This would be calculated from actual monitoring data
        
        return {
            'system_uptime': uptime,
            'average_response_time': avg_response_time,
            'error_rate': round(error_rate, 2),
        }