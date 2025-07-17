from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from review.models import ReviewHistory, ReviewSchedule
from review.utils import calculate_success_rate, get_today_reviews_count, get_pending_reviews_count


class DashboardView(APIView):
    """Dashboard analytics view"""
    
    def get(self, request):
        """Get dashboard data - optimized version"""
        user = request.user
        
        # Use utility functions for consistent calculations
        today_reviews = get_today_reviews_count(user)
        pending_reviews = get_pending_reviews_count(user)
        success_rate, total_reviews_30_days, _ = calculate_success_rate(user, days=30)
        
        # Calculate streak
        streak_days = self._calculate_review_streak(user)
        
        return Response({
            'today_reviews': today_reviews,
            'pending_reviews': pending_reviews,
            'total_content': user.contents.count(),
            'success_rate': success_rate,
            'total_reviews_30_days': total_reviews_30_days,
            'streak_days': streak_days,
        })
    
    def _calculate_review_streak(self, user):
        """Calculate consecutive days of reviews"""
        today = timezone.now().date()
        streak = 0
        
        for i in range(30):  # Check last 30 days max
            check_date = today - timedelta(days=i)
            has_review = ReviewHistory.objects.filter(
                user=user,
                review_date__date=check_date
            ).exists()
            
            if has_review:
                streak += 1
            else:
                break
                
        return streak


class ReviewStatsView(APIView):
    """Enhanced review statistics view"""
    
    def get(self, request):
        """Get comprehensive review statistics"""
        user = request.user
        
        # Review result distribution with percentages and temporal context
        result_stats = self._get_result_distribution(user)
        
        # Enhanced daily review data with success rates
        daily_reviews = self._get_daily_reviews_with_performance(user)
        
        # Weekly performance metrics
        weekly_performance = self._get_weekly_performance(user)
        
        # Review trends
        trends = self._get_review_trends(user)
        
        return Response({
            'result_distribution': result_stats,
            'daily_reviews': daily_reviews,
            'weekly_performance': weekly_performance,
            'trends': trends,
        })
    
    def _get_result_distribution(self, user):
        """Get result distribution with percentages and context"""
        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # All time stats
        all_time_stats = ReviewHistory.objects.filter(user=user).values('result').annotate(
            count=Count('result')
        )
        
        # Recent stats (last 30 days)
        recent_stats = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        ).values('result').annotate(
            count=Count('result')
        )
        
        # Calculate totals and percentages
        all_time_total = sum(item['count'] for item in all_time_stats)
        recent_total = sum(item['count'] for item in recent_stats)
        
        # Process results
        result_mapping = {
            'remembered': '기억함',
            'partial': '애매함', 
            'forgot': '모름'
        }
        
        all_time_processed = []
        recent_processed = []
        
        for result_type in ['remembered', 'partial', 'forgot']:
            # All time
            all_time_count = next((item['count'] for item in all_time_stats if item['result'] == result_type), 0)
            all_time_percentage = (all_time_count / all_time_total * 100) if all_time_total > 0 else 0
            
            # Recent
            recent_count = next((item['count'] for item in recent_stats if item['result'] == result_type), 0)
            recent_percentage = (recent_count / recent_total * 100) if recent_total > 0 else 0
            
            all_time_processed.append({
                'result': result_type,
                'name': result_mapping[result_type],
                'count': all_time_count,
                'percentage': round(all_time_percentage, 1)
            })
            
            recent_processed.append({
                'result': result_type,
                'name': result_mapping[result_type],
                'count': recent_count,
                'percentage': round(recent_percentage, 1)
            })
        
        return {
            'all_time': all_time_processed,
            'recent_30_days': recent_processed,
            'all_time_total': all_time_total,
            'recent_total': recent_total
        }
    
    def _get_daily_reviews_with_performance(self, user):
        """Get daily reviews with success rates and performance metrics"""
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        daily_data = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            
            # Get reviews for this date
            day_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date=date
            )
            
            total_count = day_reviews.count()
            remembered_count = day_reviews.filter(result='remembered').count()
            success_rate = (remembered_count / total_count * 100) if total_count > 0 else 0
            
            daily_data.append({
                'date': date.isoformat(),
                'count': total_count,
                'success_rate': round(success_rate, 1),
                'remembered': remembered_count,
                'partial': day_reviews.filter(result='partial').count(),
                'forgot': day_reviews.filter(result='forgot').count(),
            })
        
        return daily_data
    
    def _get_weekly_performance(self, user):
        """Get weekly performance metrics with trends"""
        today = timezone.now().date()
        weeks_data = []
        
        for week_offset in range(4):  # Last 4 weeks
            week_start = today - timedelta(days=today.weekday() + 7 * week_offset)
            week_end = week_start + timedelta(days=6)
            
            # Get reviews for this week
            week_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date__range=[week_start, week_end]
            )
            
            total_count = week_reviews.count()
            remembered_count = week_reviews.filter(result='remembered').count()
            success_rate = (remembered_count / total_count * 100) if total_count > 0 else 0
            
            # Calculate consistency (days with reviews)
            days_with_reviews = 0
            for day_offset in range(7):
                check_date = week_start + timedelta(days=day_offset)
                if week_reviews.filter(review_date__date=check_date).exists():
                    days_with_reviews += 1
            
            consistency = (days_with_reviews / 7 * 100)
            
            weeks_data.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'week_label': f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}",
                'total_reviews': total_count,
                'success_rate': round(success_rate, 1),
                'consistency': round(consistency, 1),
                'days_active': days_with_reviews,
                'remembered': remembered_count,
                'partial': week_reviews.filter(result='partial').count(),
                'forgot': week_reviews.filter(result='forgot').count(),
            })
        
        return list(reversed(weeks_data))  # Most recent first
    
    def _get_review_trends(self, user):
        """Get review trends and insights"""
        # Calculate trends for last 30 days vs previous 30 days
        today = timezone.now().date()
        
        # Current period (last 30 days)
        current_start = today - timedelta(days=30)
        current_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__date__gte=current_start
        )
        
        # Previous period (30 days before that)
        previous_start = current_start - timedelta(days=30)
        previous_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__date__range=[previous_start, current_start]
        )
        
        # Calculate metrics
        current_total = current_reviews.count()
        previous_total = previous_reviews.count()
        
        current_success_rate = (current_reviews.filter(result='remembered').count() / current_total * 100) if current_total > 0 else 0
        previous_success_rate = (previous_reviews.filter(result='remembered').count() / previous_total * 100) if previous_total > 0 else 0
        
        # Calculate changes
        review_count_change = current_total - previous_total
        success_rate_change = current_success_rate - previous_success_rate
        
        return {
            'review_count_change': review_count_change,
            'success_rate_change': round(success_rate_change, 1),
            'current_period_total': current_total,
            'previous_period_total': previous_total,
            'current_success_rate': round(current_success_rate, 1),
            'previous_success_rate': round(previous_success_rate, 1),
        }